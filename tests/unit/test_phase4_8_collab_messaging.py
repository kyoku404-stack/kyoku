"""Unit tests for Phase 4.8 Member 2 — Communication, Task Dispatching & Findings.

Tests dependency gates, retry policies, secret scrubbing, message routing,
and evidence-backed findings catalog.
"""

from __future__ import annotations

import pytest

from backend.app.agents.collaboration.contracts import (
    CollaborationMessageType,
    CollaborationRequest,
    CollaborationSecurityContext,
    CollaborationTaskSpec,
    TaskStatus,
)
from backend.app.agents.collaboration.findings import FindingsCatalog
from backend.app.agents.collaboration.messaging import (
    CollaborationMessageService,
    scrub_secrets_from_text,
    scrub_secrets_recursively,
)
from backend.app.agents.collaboration.repository import InMemoryCollaborationRepository
from backend.app.agents.collaboration.session_manager import SessionManager
from backend.app.agents.collaboration.task_dispatcher import TaskDispatcher
from backend.app.agents.errors import (
    CollaborationMessageInvalidError,
    CollaborationSessionNotFoundError,
    CollaborationTaskDependencyFailedError,
)


@pytest.fixture
def repo() -> InMemoryCollaborationRepository:
    return InMemoryCollaborationRepository()


@pytest.fixture
def session_mgr(repo: InMemoryCollaborationRepository) -> SessionManager:
    return SessionManager(repository=repo)


@pytest.fixture
def dispatcher(repo: InMemoryCollaborationRepository) -> TaskDispatcher:
    return TaskDispatcher(repository=repo)


@pytest.fixture
def msg_service(repo: InMemoryCollaborationRepository) -> CollaborationMessageService:
    return CollaborationMessageService(repository=repo)


@pytest.fixture
def findings_catalog(repo: InMemoryCollaborationRepository) -> FindingsCatalog:
    return FindingsCatalog(repository=repo)


@pytest.fixture
def security_context() -> CollaborationSecurityContext:
    return CollaborationSecurityContext(
        tenant_id="tenant-acme",
        user_id="usr-eng-01",
    )


def test_secret_scrubbing():
    """Verify regex patterns redact bearer tokens, OpenAI keys, and password fields."""
    raw = "Here is my token Bearer eyJhbGciOiJIUzI1NiIsInR5cCI... and api_key='sk-1234567890abcdef12' secret"
    sanitized = scrub_secrets_from_text(raw)
    assert "Bearer eyJhb" not in sanitized
    assert "sk-1234567890abcdef12" not in sanitized
    assert "[REDACTED_SECRET]" in sanitized

    nested = {
        "headers": {"Authorization": "Bearer secret-token-xyz"},
        "config": {"db_password": "supersecretpassword123"},
        "items": ["sk-abcdef1234567890", "harmless text"],
    }
    cleaned = scrub_secrets_recursively(nested)
    assert "[REDACTED_SECRET]" in cleaned["headers"]["Authorization"]
    assert "[REDACTED_SECRET]" in cleaned["items"][0]
    assert cleaned["items"][1] == "harmless text"


@pytest.mark.asyncio
async def test_task_dispatch_and_dependencies(
    session_mgr: SessionManager,
    dispatcher: TaskDispatcher,
    security_context: CollaborationSecurityContext,
):
    """Verify tasks cannot start until dependencies succeed, and ready tasks are detected."""
    request = CollaborationRequest(
        objective="Dependency workflow",
        agent_ids=["agent:worker1", "agent:worker2"],
        tasks=[
            CollaborationTaskSpec(task_id="step-1", agent_id="agent:worker1", title="Step 1"),
            CollaborationTaskSpec(task_id="step-2", agent_id="agent:worker2", title="Step 2", dependencies=["step-1"]),
        ],
    )
    session = await session_mgr.create_session(request, security_context)

    # Initially step-1 is ready, step-2 is blocked
    ready = await dispatcher.get_ready_tasks(session.session_id, security_context)
    assert len(ready) == 1
    assert ready[0].task_id == "step-1"

    # Trying to start step-2 prematurely fails
    with pytest.raises(ValueError, match="dependencies are not yet complete"):
        await dispatcher.start_task("step-2", security_context)

    # Start and complete step-1
    await dispatcher.start_task("step-1", security_context)
    await dispatcher.complete_task("step-1", {"result": "done"}, security_context)

    # Now step-2 is ready
    ready = await dispatcher.get_ready_tasks(session.session_id, security_context)
    assert len(ready) == 1
    assert ready[0].task_id == "step-2"

    t2 = await dispatcher.start_task("step-2", security_context)
    assert t2.status == TaskStatus.RUNNING
    assert t2.attempt == 1


@pytest.mark.asyncio
async def test_task_failed_dependency_cascade(
    session_mgr: SessionManager,
    dispatcher: TaskDispatcher,
    security_context: CollaborationSecurityContext,
):
    """Verify a task whose dependency failed raises CollaborationTaskDependencyFailedError."""
    request = CollaborationRequest(
        objective="Failure cascade workflow",
        agent_ids=["agent:worker"],
        tasks=[
            CollaborationTaskSpec(task_id="upstream", agent_id="agent:worker", title="Upstream"),
            CollaborationTaskSpec(task_id="downstream", agent_id="agent:worker", title="Downstream", dependencies=["upstream"]),
        ],
    )
    await session_mgr.create_session(request, security_context)

    # Fail upstream permanently
    await dispatcher.start_task("upstream", security_context)
    await dispatcher.fail_task("upstream", "EXECUTION_TIMEOUT", security_context, allow_retry=False)

    with pytest.raises(CollaborationTaskDependencyFailedError) as exc_info:
        await dispatcher.start_task("downstream", security_context)

    assert "upstream" in exc_info.value.details["failed_dependencies"]
    downstream = await dispatcher.get_task("downstream", security_context)
    assert downstream.status == TaskStatus.FAILED
    assert downstream.error_code == "COLLABORATION_TASK_DEPENDENCY_FAILED"


@pytest.mark.asyncio
async def test_task_retry_lifecycle(
    session_mgr: SessionManager,
    dispatcher: TaskDispatcher,
    security_context: CollaborationSecurityContext,
):
    """Verify task retry resets status to PENDING until max_attempts is exceeded."""
    request = CollaborationRequest(
        objective="Retry test",
        agent_ids=["agent:worker"],
        tasks=[CollaborationTaskSpec(task_id="retry-task", agent_id="agent:worker", title="Retryable", max_attempts=2)],
    )
    await session_mgr.create_session(request, security_context)

    # Attempt 1: Start and fail with retry
    t1 = await dispatcher.start_task("retry-task", security_context)
    assert t1.attempt == 1
    t1_failed = await dispatcher.fail_task("retry-task", "TRANSIENT_ERROR", security_context, allow_retry=True)
    assert t1_failed.status == TaskStatus.PENDING

    # Attempt 2: Start and fail permanently
    t2 = await dispatcher.start_task("retry-task", security_context)
    assert t2.attempt == 2
    t2_failed = await dispatcher.fail_task("retry-task", "PERMANENT_ERROR", security_context, allow_retry=True)
    assert t2_failed.status == TaskStatus.FAILED
    assert t2_failed.error_code == "PERMANENT_ERROR"


@pytest.mark.asyncio
async def test_messaging_routing_and_secret_redaction(
    session_mgr: SessionManager,
    msg_service: CollaborationMessageService,
    security_context: CollaborationSecurityContext,
):
    """Verify message exchange sanitizes payload secrets and tracks correlation IDs."""
    request = CollaborationRequest(
        objective="Messaging test",
        agent_ids=["agent:researcher", "agent:analyst"],
    )
    session = await session_mgr.create_session(request, security_context)

    msg = await msg_service.send_message(
        session_id=session.session_id,
        sender_id="agent:researcher",
        recipient_id="agent:analyst",
        message_type=CollaborationMessageType.HANDOFF,
        payload={"notes": "Use Authorization: Bearer secret-12345-token", "data": 42},
        security_context=security_context,
    )

    assert msg.message_id.startswith("collab_msg_")
    assert msg.sender_id == "agent:researcher"
    assert msg.recipient_id == "agent:analyst"
    assert msg.message_type == CollaborationMessageType.HANDOFF
    assert "secret-12345-token" not in str(msg.payload)
    assert "[REDACTED_SECRET]" in str(msg.payload)
    assert msg.correlation_id.startswith("corr_")

    history = await msg_service.list_messages(session.session_id, security_context)
    assert len(history) == 1
    assert history[0].message_id == msg.message_id


@pytest.mark.asyncio
async def test_messaging_validation_and_isolation(
    session_mgr: SessionManager,
    msg_service: CollaborationMessageService,
    security_context: CollaborationSecurityContext,
):
    """Verify empty recipient raises validation error and cross-tenant message access is rejected."""
    request = CollaborationRequest(objective="Msg validation", agent_ids=["agent:a"])
    session = await session_mgr.create_session(request, security_context)

    with pytest.raises(CollaborationMessageInvalidError, match="recipient_id cannot be empty"):
        await msg_service.send_message(
            session_id=session.session_id,
            sender_id="agent:a",
            recipient_id="",
            message_type=CollaborationMessageType.CLARIFICATION,
            payload={},
            security_context=security_context,
        )

    other_ctx = CollaborationSecurityContext(tenant_id="tenant-foreign", user_id="usr-other")
    with pytest.raises(CollaborationSessionNotFoundError):
        await msg_service.send_message(
            session_id=session.session_id,
            sender_id="agent:a",
            recipient_id="agent:b",
            message_type=CollaborationMessageType.CLARIFICATION,
            payload={},
            security_context=other_ctx,
        )


@pytest.mark.asyncio
async def test_findings_registration_and_retrieval(
    session_mgr: SessionManager,
    findings_catalog: FindingsCatalog,
    security_context: CollaborationSecurityContext,
):
    """Verify findings are registered with claims, evidence references, and provenance."""
    request = CollaborationRequest(
        objective="Findings test",
        agent_ids=["agent:researcher"],
        tasks=[CollaborationTaskSpec(task_id="t-research", agent_id="agent:researcher", title="Research spec")],
    )
    session = await session_mgr.create_session(request, security_context)

    finding = await findings_catalog.register_finding(
        session_id=session.session_id,
        task_id="t-research",
        claim="PostgreSQL 16 improves query parallelism by 24%.",
        evidence_refs=["doc:benchmark-report-2026", "keep://evidence/doc-881"],
        limitations="Tested only on OLAP workloads.",
        provenance={"model": "gpt-4o", "temperature": 0.2},
        security_context=security_context,
    )

    assert finding.finding_id.startswith("collab_fnd_")
    assert finding.claim == "PostgreSQL 16 improves query parallelism by 24%."
    assert len(finding.evidence_refs) == 2
    assert finding.provenance["agent_id"] == "agent:researcher"
    assert finding.limitations == "Tested only on OLAP workloads."

    # Empty claim rejected
    with pytest.raises(ValueError, match="Finding claim cannot be empty"):
        await findings_catalog.register_finding(
            session_id=session.session_id,
            task_id="t-research",
            claim="   ",
            security_context=security_context,
        )

    # Retrieve findings
    findings = await findings_catalog.list_findings(session.session_id, security_context)
    assert len(findings) == 1
    assert findings[0].finding_id == finding.finding_id
