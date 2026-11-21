"""Unit tests for Phase 4.8 Member 1 — Core Architecture, Contracts & Session Management.

Validates session lifecycles, state machine transitions, cancellation cascades,
multi-tenant isolation, and report compilation.
"""

from __future__ import annotations

import pytest

from backend.app.agents.collaboration.contracts import (
    CancelSessionRequest,
    CollaborationConflict,
    CollaborationFinding,
    CollaborationRequest,
    CollaborationSecurityContext,
    CollaborationTaskSpec,
    ConflictResolutionRequest,
    ConflictStatus,
    ReviewOutcome,
    ReviewResult,
    SessionStatus,
    TaskStatus,
    generate_collaboration_conflict_id,
    generate_collaboration_finding_id,
    generate_collaboration_message_id,
    generate_collaboration_review_id,
    generate_collaboration_session_id,
    generate_collaboration_task_id,
)
from backend.app.agents.collaboration.repository import InMemoryCollaborationRepository
from backend.app.agents.collaboration.service import CollaborationService
from backend.app.agents.collaboration.session_manager import SessionManager
from backend.app.agents.errors import (
    CollaborationSessionCancelledError,
    CollaborationSessionCompletedError,
    CollaborationSessionNotFoundError,
)


@pytest.fixture
def repo() -> InMemoryCollaborationRepository:
    return InMemoryCollaborationRepository()


@pytest.fixture
def session_mgr(repo: InMemoryCollaborationRepository) -> SessionManager:
    return SessionManager(repository=repo)


@pytest.fixture
def collab_service(repo: InMemoryCollaborationRepository, session_mgr: SessionManager) -> CollaborationService:
    return CollaborationService(repository=repo, session_manager=session_mgr)


@pytest.fixture
def security_context() -> CollaborationSecurityContext:
    return CollaborationSecurityContext(
        tenant_id="tenant-corp",
        user_id="usr-lead-01",
        roles=["architect", "engineer"],
        permissions=["agent.invoke", "agent.read"],
    )


def test_id_generators():
    """Verify unique domain prefixes for all entity ID generators."""
    assert generate_collaboration_session_id().startswith("collab_sess_")
    assert generate_collaboration_task_id().startswith("collab_task_")
    assert generate_collaboration_message_id().startswith("collab_msg_")
    assert generate_collaboration_finding_id().startswith("collab_fnd_")
    assert generate_collaboration_review_id().startswith("collab_rev_")
    assert generate_collaboration_conflict_id().startswith("collab_cnf_")


@pytest.mark.asyncio
async def test_session_creation_with_tasks(session_mgr: SessionManager, security_context: CollaborationSecurityContext):
    """Verify session creation registers initial subtasks and enters PLANNING status."""
    request = CollaborationRequest(
        objective="Assess multi-agent performance",
        workflow_id="wf-benchmark-01",
        agent_ids=["agent:researcher", "agent:analyst"],
        tasks=[
            CollaborationTaskSpec(
                task_id="task-r1",
                agent_id="agent:researcher",
                title="Run benchmarks",
                dependencies=[],
                inputs={"target": "redis"},
            ),
            CollaborationTaskSpec(
                task_id="task-a1",
                agent_id="agent:analyst",
                title="Synthesize results",
                dependencies=["task-r1"],
                inputs={"criteria": "latency"},
            ),
        ],
        require_review=True,
        max_revisions=2,
    )

    session = await session_mgr.create_session(request, security_context)

    assert session.session_id.startswith("collab_sess_")
    assert session.status == SessionStatus.PLANNING
    assert session.tenant_id == "tenant-corp"
    assert session.requested_by == "usr-lead-01"
    assert session.workflow_id == "wf-benchmark-01"

    tasks = await session_mgr.repository.list_tasks(session.session_id, "tenant-corp")
    assert len(tasks) == 2
    assert tasks[0].task_id == "task-r1"
    assert tasks[0].status == TaskStatus.PENDING
    assert tasks[1].dependencies == ["task-r1"]


@pytest.mark.asyncio
async def test_session_creation_exceeds_max_agents(session_mgr: SessionManager, security_context: CollaborationSecurityContext):
    """Verify exceeding agent ceiling raises ValueError."""
    request = CollaborationRequest(
        objective="Excessive agents",
        agent_ids=["agent:1", "agent:2", "agent:3", "agent:4"],
        max_agents=3,
    )

    with pytest.raises(ValueError, match="exceeds maximum allowed"):
        await session_mgr.create_session(request, security_context)


@pytest.mark.asyncio
async def test_session_lifecycle_transitions(session_mgr: SessionManager, security_context: CollaborationSecurityContext):
    """Verify valid state progression and terminal completion immutability."""
    request = CollaborationRequest(
        objective="State transition test",
        agent_ids=["agent:worker"],
    )
    session = await session_mgr.create_session(request, security_context)

    # PLANNING -> IN_PROGRESS
    s1 = await session_mgr.transition_status(session.session_id, SessionStatus.IN_PROGRESS, security_context)
    assert s1.status == SessionStatus.IN_PROGRESS

    # IN_PROGRESS -> REVIEWING
    s2 = await session_mgr.transition_status(session.session_id, SessionStatus.REVIEWING, security_context)
    assert s2.status == SessionStatus.REVIEWING

    # REVIEWING -> SYNTHESIZING
    s3 = await session_mgr.transition_status(session.session_id, SessionStatus.SYNTHESIZING, security_context)
    assert s3.status == SessionStatus.SYNTHESIZING

    # SYNTHESIZING -> COMPLETED
    s4 = await session_mgr.transition_status(
        session.session_id,
        SessionStatus.COMPLETED,
        security_context,
        summary="All objectives completed successfully.",
    )
    assert s4.status == SessionStatus.COMPLETED
    assert s4.completed_at is not None
    assert s4.summary == "All objectives completed successfully."

    # Cannot transition from completed
    with pytest.raises(CollaborationSessionCompletedError):
        await session_mgr.transition_status(session.session_id, SessionStatus.IN_PROGRESS, security_context)


@pytest.mark.asyncio
async def test_session_cancellation_cascades_to_tasks(session_mgr: SessionManager, security_context: CollaborationSecurityContext):
    """Verify cancellation marks session and all non-completed tasks cancelled."""
    request = CollaborationRequest(
        objective="Cancellation test",
        agent_ids=["agent:worker"],
        tasks=[
            CollaborationTaskSpec(task_id="t1", agent_id="agent:worker", title="Step 1"),
            CollaborationTaskSpec(task_id="t2", agent_id="agent:worker", title="Step 2"),
        ],
    )
    session = await session_mgr.create_session(request, security_context)

    # Manually transition task 1 to running
    t1 = await session_mgr.repository.get_task("t1", "tenant-corp")
    assert t1 is not None
    t1.status = TaskStatus.RUNNING
    await session_mgr.repository.update_task(t1)

    cancelled_session = await session_mgr.cancel_session(
        session.session_id,
        CancelSessionRequest(reason="User triggered cancel"),
        security_context,
    )

    assert cancelled_session.status == SessionStatus.CANCELLED
    assert "User triggered cancel" in (cancelled_session.summary or "")

    tasks = await session_mgr.repository.list_tasks(session.session_id, "tenant-corp")
    for t in tasks:
        assert t.status == TaskStatus.CANCELLED
        assert t.completed_at is not None

    # Transitioning a cancelled session fails
    with pytest.raises(CollaborationSessionCancelledError):
        await session_mgr.transition_status(session.session_id, SessionStatus.IN_PROGRESS, security_context)


@pytest.mark.asyncio
async def test_multi_tenant_isolation(session_mgr: SessionManager, security_context: CollaborationSecurityContext):
    """Verify cross-tenant access to sessions and tasks is strictly blocked."""
    request = CollaborationRequest(
        objective="Tenant A session",
        agent_ids=["agent:worker"],
        tasks=[CollaborationTaskSpec(task_id="t-iso", agent_id="agent:worker", title="Iso task")],
    )
    session = await session_mgr.create_session(request, security_context)

    # Different tenant tries to access
    attacker_context = CollaborationSecurityContext(
        tenant_id="tenant-other",
        user_id="usr-adversary",
    )

    with pytest.raises(CollaborationSessionNotFoundError):
        await session_mgr.get_session(session.session_id, attacker_context)

    # Repository isolation check
    assert await session_mgr.repository.get_session(session.session_id, "tenant-other") is None
    assert await session_mgr.repository.get_task("t-iso", "tenant-other") is None


@pytest.mark.asyncio
async def test_compile_report_and_metrics(repo: InMemoryCollaborationRepository, session_mgr: SessionManager, security_context: CollaborationSecurityContext):
    """Verify complete report synthesis including findings, reviews, and unresolved conflicts."""
    request = CollaborationRequest(
        objective="Report compilation test",
        agent_ids=["agent:researcher", "agent:analyst"],
        tasks=[
            CollaborationTaskSpec(task_id="t-succ", agent_id="agent:researcher", title="Succ task"),
        ],
    )
    session = await session_mgr.create_session(request, security_context)

    # Mark task succeeded
    t = await repo.get_task("t-succ", "tenant-corp")
    assert t is not None
    t.status = TaskStatus.SUCCEEDED
    await repo.update_task(t)

    # Add finding
    f1 = CollaborationFinding(
        finding_id="fnd-1",
        session_id=session.session_id,
        tenant_id="tenant-corp",
        task_id="t-succ",
        claim="Latency is sub-10ms.",
        evidence_refs=["doc-123"],
    )
    await repo.create_finding(f1)

    # Add review
    r1 = ReviewResult(
        review_id="rev-1",
        session_id=session.session_id,
        tenant_id="tenant-corp",
        reviewer_id="agent:analyst",
        finding_ids=["fnd-1"],
        outcome=ReviewOutcome.ACCEPTED,
    )
    await repo.create_review(r1)

    # Add conflict (unresolved)
    c1 = CollaborationConflict(
        conflict_id="cnf-1",
        session_id=session.session_id,
        tenant_id="tenant-corp",
        finding_ids=["fnd-1"],
        status=ConflictStatus.DETECTED,
        description="Contradicts previous claim",
    )
    await repo.create_conflict(c1)

    # Complete session
    await session_mgr.transition_status(session.session_id, SessionStatus.COMPLETED, security_context, summary="Done")

    report = await session_mgr.compile_report(session.session_id, security_context)
    assert report.session_id == session.session_id
    assert report.status == SessionStatus.COMPLETED
    assert len(report.findings) == 1
    assert len(report.reviews) == 1
    assert len(report.conflicts) == 1
    assert len(report.unresolved_conflicts) == 1
    assert report.metrics["succeeded_tasks"] == 1
    assert report.metrics["failed_tasks"] == 0
    assert report.metrics["unresolved_conflicts"] == 1


@pytest.mark.asyncio
async def test_conflict_resolution(collab_service: CollaborationService, repo: InMemoryCollaborationRepository, security_context: CollaborationSecurityContext):
    """Verify human or policy conflict resolution updates state to RESOLVED with notes."""
    request = CollaborationRequest(
        objective="Conflict test",
        agent_ids=["agent:worker"],
    )
    session = await collab_service.start_session(request, security_context)

    conflict = CollaborationConflict(
        conflict_id="cnf-99",
        session_id=session.session_id,
        tenant_id="tenant-corp",
        finding_ids=["fnd-a", "fnd-b"],
        status=ConflictStatus.ESCALATED,
        description="Conflicting throughput numbers",
    )
    await repo.create_conflict(conflict)

    res_req = ConflictResolutionRequest(
        conflict_id="cnf-99",
        resolution="Adopt finding fnd-a per calibrated test run",
        accepted_finding_ids=["fnd-a"],
        rejected_finding_ids=["fnd-b"],
    )

    resolved = await collab_service.resolve_conflict(session.session_id, res_req, security_context)
    assert resolved.status == ConflictStatus.RESOLVED
    assert resolved.resolution == "Adopt finding fnd-a per calibrated test run"
    assert resolved.resolved_by == "usr-lead-01"
    assert resolved.resolved_at is not None
