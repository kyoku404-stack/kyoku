"""Phase 4.9 Member 1 Unit Tests — Autonomous Controller, Lifecycle & Contracts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.app.agents.autonomy.contracts import (
    SERVER_MAX_AGENT_ATTEMPTS,
    SERVER_MAX_DEADLINE_SECONDS,
    SERVER_MAX_REPLANS,
    SERVER_MAX_STEPS,
    AutonomousWorkflowRequest,
    AutonomyPolicy,
    AutonomySecurityContext,
    EvaluationResult,
    is_valid_autonomy_transition,
)
from backend.app.agents.autonomy.controller import AutonomousWorkflowController
from backend.app.agents.autonomy.repository import InMemoryAutonomyRepository
from backend.app.agents.autonomy.state import sanitize_autonomy_state
from backend.app.agents.errors import (
    AutonomousWorkflowBudgetExhaustedError,
    AutonomousWorkflowDeadlineExceededError,
    AutonomousWorkflowIdempotencyConflictError,
    AutonomousWorkflowInvalidStateError,
    AutonomousWorkflowNotFoundError,
    AutonomousWorkflowReplanLimitError,
    AutonomousWorkflowUnsupportedTypeError,
)


def _ctx(tenant: str = "tenant-a", user: str = "user-1") -> AutonomySecurityContext:
    return AutonomySecurityContext(
        tenant_id=tenant,
        user_id=user,
        roles=["analyst"],
        permissions=["agent.invoke", "agent.read"],
    )


@pytest.mark.asyncio
async def test_initialize_workflow_clamps_server_limits_and_validates_type():
    repo = InMemoryAutonomyRepository()
    controller = AutonomousWorkflowController(repo)

    req = AutonomousWorkflowRequest(
        objective="Investigate Q4 customer churn increase",
        workflow_id="churn_investigation",
        policy=AutonomyPolicy(
            max_steps=99,
            max_replans=10,
            max_agent_attempts=5,
            deadline_seconds=3600,
            require_approval_for_writes=True,
        ),
    )
    record = await controller.initialize_workflow(req, _ctx())

    assert record.status == "pending"
    assert record.policy.max_steps == SERVER_MAX_STEPS
    assert record.policy.max_replans == SERVER_MAX_REPLANS
    assert record.policy.max_agent_attempts == SERVER_MAX_AGENT_ATTEMPTS
    assert record.policy.deadline_seconds == SERVER_MAX_DEADLINE_SECONDS
    assert record.budget is not None
    assert record.budget.remaining_steps == SERVER_MAX_STEPS


@pytest.mark.asyncio
async def test_rejects_unsupported_workflow_type():
    repo = InMemoryAutonomyRepository()
    controller = AutonomousWorkflowController(repo)

    req = AutonomousWorkflowRequest(
        objective="Do something arbitrary",
        workflow_id="unapproved_arbitrary_runner",
    )
    with pytest.raises(AutonomousWorkflowUnsupportedTypeError):
        await controller.initialize_workflow(req, _ctx())


@pytest.mark.asyncio
async def test_lifecycle_transitions_and_terminal_immutability():
    assert is_valid_autonomy_transition("pending", "running")
    assert is_valid_autonomy_transition("running", "awaiting_approval")
    assert is_valid_autonomy_transition("awaiting_approval", "running")
    assert not is_valid_autonomy_transition("completed", "running")

    repo = InMemoryAutonomyRepository()
    controller = AutonomousWorkflowController(repo)
    record = await controller.initialize_workflow(
        AutonomousWorkflowRequest(objective="Check churn root causes"),
        _ctx(),
    )
    await controller.transition_status(record.execution_id, "running", _ctx())
    completed = await controller.terminate(
        record.execution_id,
        _ctx(),
        target_status="completed",
        reason="Objective satisfied",
    )
    assert completed.status == "completed"

    with pytest.raises(AutonomousWorkflowInvalidStateError):
        await controller.transition_status(record.execution_id, "running", _ctx())


@pytest.mark.asyncio
async def test_step_budget_and_replan_budget_exhaustion():
    repo = InMemoryAutonomyRepository()
    controller = AutonomousWorkflowController(repo)
    record = await controller.initialize_workflow(
        AutonomousWorkflowRequest(
            objective="Analyze churn cohorts",
            policy=AutonomyPolicy(max_steps=1, max_replans=1),
        ),
        _ctx(),
    )
    await controller.transition_status(record.execution_id, "running", _ctx())

    budget = await controller.consume_step_budget(record.execution_id, _ctx())
    assert budget.steps_consumed == 1

    with pytest.raises(AutonomousWorkflowBudgetExhaustedError):
        await controller.consume_step_budget(record.execution_id, _ctx())

    # Fresh workflow for replan bound verification
    r2 = await controller.initialize_workflow(
        AutonomousWorkflowRequest(
            objective="Analyze churn cohorts",
            policy=AutonomyPolicy(max_steps=5, max_replans=1),
        ),
        _ctx(),
    )
    await controller.consume_replan_budget(r2.execution_id, _ctx())
    with pytest.raises(AutonomousWorkflowReplanLimitError):
        await controller.consume_replan_budget(r2.execution_id, _ctx())


@pytest.mark.asyncio
async def test_deadline_enforcement_on_transition():
    repo = InMemoryAutonomyRepository()
    controller = AutonomousWorkflowController(repo)
    record = await controller.initialize_workflow(
        AutonomousWorkflowRequest(
            objective="Time-boxed churn review",
            policy=AutonomyPolicy(deadline_seconds=10),
        ),
        _ctx(),
    )
    future_time = datetime.now(UTC) + timedelta(seconds=30)
    with pytest.raises(AutonomousWorkflowDeadlineExceededError):
        await controller.check_budget_and_deadline(record.execution_id, _ctx(), now=future_time)

    fetched = await controller.get_workflow_or_raise(record.execution_id, _ctx())
    assert fetched.status == "budget_exhausted"


@pytest.mark.asyncio
async def test_idempotency_and_tenant_isolation():
    repo = InMemoryAutonomyRepository()
    controller = AutonomousWorkflowController(repo)

    req1 = AutonomousWorkflowRequest(
        objective="Churn report",
        idempotency_key="idem-churn-001",
    )
    first = await controller.initialize_workflow(req1, _ctx("tenant-a", "usr-1"))
    second = await controller.initialize_workflow(req1, _ctx("tenant-a", "usr-1"))
    assert first.execution_id == second.execution_id

    req_conflict = AutonomousWorkflowRequest(
        objective="Completely different goal",
        idempotency_key="idem-churn-001",
    )
    with pytest.raises(AutonomousWorkflowIdempotencyConflictError):
        await controller.initialize_workflow(req_conflict, _ctx("tenant-a", "usr-1"))

    with pytest.raises(AutonomousWorkflowNotFoundError):
        await controller.get_workflow_or_raise(first.execution_id, _ctx("tenant-b", "usr-2"))


@pytest.mark.asyncio
async def test_decision_loop_actions_and_checkpoint_sanitization():
    repo = InMemoryAutonomyRepository()
    controller = AutonomousWorkflowController(repo)
    record = await controller.initialize_workflow(
        AutonomousWorkflowRequest(
            objective="Investigate churn",
            policy=AutonomyPolicy(max_steps=4, max_replans=1),
        ),
        _ctx(),
    )

    act_replan = await controller.decide_next_action(
        record.execution_id,
        EvaluationResult(
            objective_satisfied=False,
            evidence_sufficient=False,
            should_replan=True,
            reasons=["Missing billing retention evidence"],
        ),
        _ctx(),
    )
    assert act_replan == "replan"

    act_pause = await controller.decide_next_action(
        record.execution_id,
        EvaluationResult(objective_satisfied=False, evidence_sufficient=True),
        _ctx(),
        pending_write_requires_approval=True,
    )
    assert act_pause == "pause_for_approval"

    decisions = await repo.list_decisions(record.execution_id, "tenant-a")
    assert len(decisions) == 2

    sanitized = sanitize_autonomy_state(
        {
            "execution_id": record.execution_id,
            "api_key": "sk-secret1234567890abcdef",
            "note": "Authorization Bearer eyJhbGciOiJIUzI1NiJ9.payload12345.sig",
        }
    )
    assert sanitized["api_key"] == "[REDACTED]"
    assert "[REDACTED]" in sanitized["note"]
