"""Phase 4.2 Member 1 — Runtime Architecture & Execution Lifecycle Unit Tests.

Verifies:
- Canonical ExecutionStatus transitions & terminal state immutability.
- RuntimeExecutionContext deadline tracking.
- AgentRuntime sync execution, async background dispatch, timeout vs cancel vs failure distinction,
  idempotency deduplication & conflict rejection, retry lineage, and stale recovery.

Specification: devdocs/p4/p4.2.txt (Sections 3, 4, 5, 13)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from backend.app.agents.contracts import AgentContext, AgentRequest, AgentResult
from backend.app.agents.errors import (
    ExecutionCancelledError,
    ExecutionNotFoundError,
    ExecutionTimeoutError,
    IdempotencyConflictError,
    InvalidExecutionTransitionError,
)
from backend.app.agents.metadata import AgentMetadata
from backend.app.agents.reference_agent import ReferenceAgent
from backend.app.agents.registry import AgentRegistry
from backend.app.agents.runtime.context import build_runtime_context
from backend.app.agents.runtime.executor import AgentRuntime
from backend.app.agents.runtime.interfaces import AgentRuntimeInterface
from backend.app.agents.runtime.lifecycle import (
    ExecutionRecord,
    ExecutionStatus,
    assert_valid_transition,
    can_transition,
    is_terminal_status,
)


class _StubRepo:
    def __init__(self) -> None:
        self.records: dict[str, ExecutionRecord] = {}

    async def create(self, record: ExecutionRecord) -> ExecutionRecord:
        self.records[record.execution_id] = record.model_copy(deep=True)
        return self.records[record.execution_id]

    async def get(self, execution_id: str, *, tenant_id: str | None = None) -> ExecutionRecord | None:
        rec = self.records.get(execution_id)
        if rec is None:
            return None
        if tenant_id is not None and rec.tenant_id != tenant_id:
            return None
        return rec.model_copy(deep=True)

    async def find_by_idempotency_key(self, *, tenant_id: str, requested_by: str, idempotency_key: str) -> ExecutionRecord | None:
        for rec in self.records.values():
            if rec.tenant_id == tenant_id and rec.requested_by == requested_by and rec.idempotency_key == idempotency_key:
                return rec.model_copy(deep=True)
        return None

    async def list_executions(self, *, tenant_id: str, agent_id: str | None = None, status: ExecutionStatus | None = None, limit: int = 50) -> list[ExecutionRecord]:
        items = [r for r in self.records.values() if r.tenant_id == tenant_id]
        if agent_id:
            items = [r for r in items if r.agent_id == agent_id]
        if status:
            items = [r for r in items if r.status == status]
        return items[:limit]

    async def mark_running(self, execution_id: str, *, started_at: datetime | None = None) -> ExecutionRecord:
        rec = self.records[execution_id]
        assert_valid_transition(execution_id, rec.status, ExecutionStatus.RUNNING)
        rec.status = ExecutionStatus.RUNNING
        rec.started_at = started_at or datetime.now(UTC)
        return rec.model_copy(deep=True)

    async def mark_succeeded(self, execution_id: str, *, result_payload: dict[str, Any], completed_at: datetime | None = None) -> ExecutionRecord:
        rec = self.records[execution_id]
        assert_valid_transition(execution_id, rec.status, ExecutionStatus.SUCCEEDED)
        rec.status = ExecutionStatus.SUCCEEDED
        rec.result_payload = result_payload
        rec.completed_at = completed_at or datetime.now(UTC)
        return rec.model_copy(deep=True)

    async def mark_failed(self, execution_id: str, *, error_code: str, error_message: str, result_payload: dict[str, Any] | None = None, completed_at: datetime | None = None) -> ExecutionRecord:
        rec = self.records[execution_id]
        assert_valid_transition(execution_id, rec.status, ExecutionStatus.FAILED)
        rec.status = ExecutionStatus.FAILED
        rec.error_code = error_code
        rec.error_message = error_message
        rec.result_payload = result_payload
        rec.completed_at = completed_at or datetime.now(UTC)
        return rec.model_copy(deep=True)

    async def mark_timed_out(self, execution_id: str, *, error_code: str, error_message: str, completed_at: datetime | None = None) -> ExecutionRecord:
        rec = self.records[execution_id]
        assert_valid_transition(execution_id, rec.status, ExecutionStatus.TIMED_OUT)
        rec.status = ExecutionStatus.TIMED_OUT
        rec.error_code = error_code
        rec.error_message = error_message
        rec.completed_at = completed_at or datetime.now(UTC)
        return rec.model_copy(deep=True)

    async def request_cancel(self, execution_id: str, *, tenant_id: str) -> ExecutionRecord:
        rec = self.records[execution_id]
        if rec.tenant_id != tenant_id:
            raise ExecutionNotFoundError(execution_id)
        rec.cancel_requested = True
        rec.cancel_requested_at = datetime.now(UTC)
        if rec.status == ExecutionStatus.PENDING:
            rec.status = ExecutionStatus.CANCELLED
            rec.completed_at = datetime.now(UTC)
        return rec.model_copy(deep=True)

    async def mark_cancelled(self, execution_id: str, *, reason: str = "Cancelled", completed_at: datetime | None = None) -> ExecutionRecord:
        rec = self.records[execution_id]
        assert_valid_transition(execution_id, rec.status, ExecutionStatus.CANCELLED)
        rec.status = ExecutionStatus.CANCELLED
        rec.error_code = "EXECUTION_CANCELLED"
        rec.error_message = reason
        rec.completed_at = completed_at or datetime.now(UTC)
        return rec.model_copy(deep=True)

    async def find_stale_running(self, *, stale_before: datetime) -> list[ExecutionRecord]:
        return [
            r.model_copy(deep=True)
            for r in self.records.values()
            if r.status == ExecutionStatus.RUNNING and r.started_at and r.started_at < stale_before
        ]


class _StubPolicy:
    def __init__(self, *, force_error: Exception | None = None) -> None:
        self.force_error = force_error
        self.cancelled_ids: list[str] = []

    def resolve_timeout(self, requested_timeout: float | None) -> float:
        return min(requested_timeout or 30.0, 300.0)

    def validate_request_limits(self, request: AgentRequest) -> None:
        return None

    def authorize(self, metadata: AgentMetadata, request: AgentRequest, context: AgentContext) -> None:
        return None

    def can_retry(self, record: ExecutionRecord) -> tuple[bool, str]:
        if record.status in (ExecutionStatus.FAILED, ExecutionStatus.TIMED_OUT, ExecutionStatus.CANCELLED):
            return True, "Eligible"
        return False, "Not terminal failure"

    async def run_with_controls(self, coro, *, execution_id: str, agent_id: str, tenant_id: str, timeout_seconds: float) -> AgentResult:
        if self.force_error is not None:
            coro.close()
            raise self.force_error
        return await coro

    def signal_cancel(self, execution_id: str) -> bool:
        self.cancelled_ids.append(execution_id)
        return True


class _StubDispatcher:
    def __init__(self) -> None:
        self.enqueued: list[str] = []

    async def enqueue(self, execution_id: str, request: AgentRequest, context: AgentContext) -> None:
        self.enqueued.append(execution_id)


def _ctx(tenant_id: str | None = None) -> AgentContext:
    return AgentContext(
        user_id=str(uuid4()),
        tenant_id=tenant_id or str(uuid4()),
        correlation_id="corr-rt-001",
        roles=["Member"],
        permissions={"agent.view", "agent.invoke", "tool:execute"},
    )


class TestLifecycleStateMachine:
    def test_valid_and_invalid_transitions(self) -> None:
        assert can_transition(ExecutionStatus.PENDING, ExecutionStatus.RUNNING) is True
        assert can_transition(ExecutionStatus.PENDING, ExecutionStatus.CANCELLED) is True
        assert can_transition(ExecutionStatus.PENDING, ExecutionStatus.SUCCEEDED) is False
        assert can_transition(ExecutionStatus.RUNNING, ExecutionStatus.SUCCEEDED) is True
        assert can_transition(ExecutionStatus.RUNNING, ExecutionStatus.TIMED_OUT) is True
        assert can_transition(ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED) is True

        for term in (
            ExecutionStatus.SUCCEEDED,
            ExecutionStatus.FAILED,
            ExecutionStatus.TIMED_OUT,
            ExecutionStatus.CANCELLED,
        ):
            assert is_terminal_status(term) is True
            with pytest.raises(InvalidExecutionTransitionError):
                assert_valid_transition("exec-1", term, ExecutionStatus.RUNNING)

    def test_runtime_context_deadline_budget(self) -> None:
        rt_ctx = build_runtime_context(
            execution_id="exec-ctx-1",
            agent_context=_ctx(),
            timeout_seconds=15.0,
        )
        assert rt_ctx.remaining_seconds() > 0.0
        assert rt_ctx.is_expired() is False
        assert rt_ctx.is_expired(now=rt_ctx.deadline_at + timedelta(seconds=1)) is True


class TestAgentRuntimeCore:
    @pytest.mark.asyncio
    async def test_sync_execution_succeeds_and_conforms_to_protocol(self) -> None:
        registry = AgentRegistry()
        registry.register(ReferenceAgent())
        repo = _StubRepo()
        runtime = AgentRuntime(registry=registry, repository=repo, policy=_StubPolicy())
        assert isinstance(runtime, AgentRuntimeInterface)

        ctx = _ctx()
        rec = await runtime.submit("reference", AgentRequest(goal="Verify Phase 4.2 runtime"), ctx, mode="sync")
        assert rec.status == ExecutionStatus.SUCCEEDED
        assert rec.agent_id == "reference"
        assert rec.attempt_number == 1

        res = await runtime.get_result(rec.execution_id, ctx)
        assert res.status == "succeeded"
        assert res.output["goal"] == "Verify Phase 4.2 runtime"

    @pytest.mark.asyncio
    async def test_async_dispatch_and_pending_atomic_cancel(self) -> None:
        registry = AgentRegistry()
        registry.register(ReferenceAgent())
        repo = _StubRepo()
        dispatcher = _StubDispatcher()
        runtime = AgentRuntime(registry=registry, repository=repo, policy=_StubPolicy(), dispatcher=dispatcher)

        ctx = _ctx()
        rec = await runtime.submit("reference", AgentRequest(goal="Long task"), ctx, mode="async")
        assert rec.status == ExecutionStatus.PENDING
        assert dispatcher.enqueued == [rec.execution_id]

        cancelled = await runtime.cancel_execution(rec.execution_id, ctx)
        assert cancelled.status == ExecutionStatus.CANCELLED

        # Cancelling again on terminal state raises InvalidExecutionTransitionError
        with pytest.raises(InvalidExecutionTransitionError):
            await runtime.cancel_execution(rec.execution_id, ctx)

    @pytest.mark.asyncio
    async def test_timeout_and_cancellation_not_misclassified_as_failed(self) -> None:
        registry = AgentRegistry()
        registry.register(ReferenceAgent())
        ctx = _ctx()

        # Timeout
        rt_timeout = AgentRuntime(
            registry=registry,
            repository=_StubRepo(),
            policy=_StubPolicy(force_error=ExecutionTimeoutError("exec-t", 1.0)),
        )
        t_rec = await rt_timeout.submit("reference", AgentRequest(goal="Slow work"), ctx)
        assert t_rec.status == ExecutionStatus.TIMED_OUT
        assert t_rec.error_code == "EXECUTION_TIMED_OUT"

        # Cancellation
        rt_cancel = AgentRuntime(
            registry=registry,
            repository=_StubRepo(),
            policy=_StubPolicy(force_error=ExecutionCancelledError("exec-c")),
        )
        c_rec = await rt_cancel.submit("reference", AgentRequest(goal="Cancel work"), ctx)
        assert c_rec.status == ExecutionStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_idempotency_dedup_conflict_and_retry_lineage(self) -> None:
        registry = AgentRegistry()
        registry.register(ReferenceAgent())
        repo = _StubRepo()
        policy = _StubPolicy(force_error=ExecutionTimeoutError("exec-x", 1.0))
        runtime = AgentRuntime(registry=registry, repository=repo, policy=policy)
        ctx = _ctx()

        r1 = await runtime.submit("reference", AgentRequest(goal="Same goal"), ctx, idempotency_key="idem-1")
        r2 = await runtime.submit("reference", AgentRequest(goal="Same goal"), ctx, idempotency_key="idem-1")
        assert r1.execution_id == r2.execution_id

        with pytest.raises(IdempotencyConflictError):
            await runtime.submit("reference", AgentRequest(goal="Different goal"), ctx, idempotency_key="idem-1")

        # Retry creates a new attempt linked to original without mutating original
        policy.force_error = None
        retry_rec = await runtime.retry_execution(r1.execution_id, ctx)
        assert retry_rec.execution_id != r1.execution_id
        assert retry_rec.parent_execution_id == r1.execution_id
        assert retry_rec.attempt_number == 2
        assert retry_rec.status == ExecutionStatus.SUCCEEDED
        orig_after = await runtime.get_execution(r1.execution_id, ctx)
        assert orig_after.status == ExecutionStatus.TIMED_OUT

    @pytest.mark.asyncio
    async def test_reconcile_stale_running_executions(self) -> None:
        registry = AgentRegistry()
        registry.register(ReferenceAgent())
        repo = _StubRepo()
        stale = ExecutionRecord(
            task_id="t-stale",
            agent_id="reference",
            agent_version="1.0.0",
            tenant_id="org-1",
            requested_by="user-1",
            status=ExecutionStatus.RUNNING,
            goal="Crashed worker task",
            correlation_id="corr-stale",
            started_at=datetime.now(UTC) - timedelta(minutes=15),
        )
        await repo.create(stale)

        runtime = AgentRuntime(registry=registry, repository=repo, policy=_StubPolicy())
        recovered = await runtime.reconcile_stale_executions(stale_after_seconds=60)
        assert len(recovered) == 1
        assert recovered[0].status == ExecutionStatus.FAILED
