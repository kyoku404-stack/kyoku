"""Phase 4.2 Member 3 — Execution Safety, Timeouts, Cancellation, Limits & Retries Unit Tests.

Verifies:
- Default & max timeout clamping (caller cannot specify unlimited timeouts).
- Slow agent execution timeout (`TIMED_OUT`) and automatic concurrency slot release.
- Cooperative cancellation while running (`CANCELLED`) and slot release.
- Global, per-agent, and per-tenant concurrency limit saturation (`429`) & recovery.
- Oversized input rejection (`EXECUTION_INPUT_TOO_LARGE`).
- Bounded transient-only retry policy & exponential backoff with jitter.

Specification: devdocs/p4/p4.2.txt (Sections 3, 9, 13)
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from backend.app.agents.contracts import AgentContext, AgentRequest, AgentResult
from backend.app.agents.errors import (
    AgentContractValidationError,
    AgentErrorCode,
    ConcurrencyLimitExceededError,
    ExecutionCancelledError,
    ExecutionTimeoutError,
)
from backend.app.agents.metadata import AgentMetadata
from backend.app.agents.persistence.execution_repository import InMemoryExecutionRepository
from backend.app.agents.registry import AgentRegistry
from backend.app.agents.runtime.executor import AgentRuntime
from backend.app.agents.runtime.lifecycle import ExecutionRecord, ExecutionStatus
from backend.app.agents.runtime.limits import ConcurrencyLimiter, ExecutionLimitsConfig
from backend.app.agents.runtime.policies import KeepExecutionPolicy, RetryPolicy


class _SlowAgent:
    metadata = AgentMetadata(agent_id="slow-agent", name="Slow Agent", version="1.0.0")

    def __init__(self, delay_seconds: float = 0.5) -> None:
        self.delay_seconds = delay_seconds
        self.started = asyncio.Event()

    async def invoke(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        self.started.set()
        await asyncio.sleep(self.delay_seconds)
        return AgentResult(status="succeeded", output={"done": True})


def _member_ctx(tenant_id: str | None = None) -> AgentContext:
    return AgentContext(
        user_id=str(uuid4()),
        tenant_id=tenant_id or str(uuid4()),
        correlation_id="corr-safety-1",
        roles=["Member"],
        permissions={"agent.view", "agent.invoke", "tool:execute"},
    )


class TestExecutionSafetyAndLimits:
    def test_timeout_clamping_and_input_size_limit(self) -> None:
        cfg = ExecutionLimitsConfig(
            default_timeout_seconds=20.0,
            max_timeout_seconds=120.0,
            max_input_bytes=256,
        )
        policy = KeepExecutionPolicy(config=cfg)
        assert policy.resolve_timeout(None) == 20.0
        assert policy.resolve_timeout(9999.0) == 120.0
        assert policy.resolve_timeout(0.001) == cfg.min_timeout_seconds

        policy.validate_request_limits(AgentRequest(goal="Short goal", input={"a": 1}))
        with pytest.raises(AgentContractValidationError) as exc_info:
            policy.validate_request_limits(
                AgentRequest(goal="Huge", input={"blob": "x" * 500})
            )
        assert exc_info.value.code == AgentErrorCode.EXECUTION_INPUT_TOO_LARGE

    @pytest.mark.asyncio
    async def test_slow_agent_times_out_and_releases_concurrency_slot(self) -> None:
        cfg = ExecutionLimitsConfig(default_timeout_seconds=0.1, max_per_agent=1)
        limiter = ConcurrencyLimiter(cfg)
        policy = KeepExecutionPolicy(config=cfg, concurrency_limiter=limiter)
        registry = AgentRegistry()
        registry.register(_SlowAgent(delay_seconds=1.0))
        runtime = AgentRuntime(
            registry=registry,
            repository=InMemoryExecutionRepository(),
            policy=policy,
        )

        rec = await runtime.submit("slow-agent", AgentRequest(goal="Slow op"), _member_ctx(), timeout_seconds=0.08)
        assert rec.status == ExecutionStatus.TIMED_OUT
        assert rec.error_code == AgentErrorCode.EXECUTION_TIMED_OUT.value
        assert limiter.active_total == 0
        assert limiter.active_for_agent("slow-agent") == 0

    @pytest.mark.asyncio
    async def test_cooperative_cancellation_of_running_execution(self) -> None:
        policy = KeepExecutionPolicy()
        slow = _SlowAgent(delay_seconds=2.0)
        registry = AgentRegistry()
        registry.register(slow)
        repo = InMemoryExecutionRepository()
        runtime = AgentRuntime(registry=registry, repository=repo, policy=policy)
        ctx = _member_ctx()

        # Pre-create PENDING record so we know execution_id while it runs
        req = AgentRequest(goal="Cancellable task")
        pending = ExecutionRecord(
            task_id=req.task_id,
            agent_id="slow-agent",
            agent_version="1.0.0",
            tenant_id=ctx.tenant_id,
            requested_by=ctx.user_id,
            goal=req.goal,
            correlation_id=ctx.correlation_id,
        )
        await repo.create(pending)

        run_task = asyncio.create_task(runtime.execute_existing(pending.execution_id, req, ctx))
        await asyncio.wait_for(slow.started.wait(), timeout=2.0)

        # Request cancel while RUNNING
        cancel_ack = await runtime.cancel_execution(pending.execution_id, ctx)
        assert cancel_ack.cancel_requested is True

        final_rec = await run_task
        assert final_rec.status == ExecutionStatus.CANCELLED
        assert policy.concurrency_limiter.active_total == 0

    @pytest.mark.asyncio
    async def test_concurrency_saturation_enforced_across_agent_tenant_and_global(self) -> None:
        cfg = ExecutionLimitsConfig(max_total_active=2, max_per_agent=1, max_per_tenant=1)
        limiter = ConcurrencyLimiter(cfg)

        await limiter.acquire(agent_id="a1", tenant_id="t1")
        # Per-agent limit hit
        with pytest.raises(ConcurrencyLimitExceededError):
            await limiter.acquire(agent_id="a1", tenant_id="t2")
        # Per-tenant limit hit
        with pytest.raises(ConcurrencyLimitExceededError):
            await limiter.acquire(agent_id="a2", tenant_id="t1")
        # Different agent & tenant succeeds -> global limit (2) now full
        await limiter.acquire(agent_id="a2", tenant_id="t2")
        with pytest.raises(ConcurrencyLimitExceededError):
            await limiter.acquire(agent_id="a3", tenant_id="t3")

        await limiter.release(agent_id="a1", tenant_id="t1")
        await limiter.release(agent_id="a2", tenant_id="t2")
        assert limiter.active_total == 0

    def test_retry_policy_eligibility_and_backoff_bounds(self) -> None:
        cfg = ExecutionLimitsConfig(max_retries=3, base_backoff_seconds=0.5, max_backoff_seconds=4.0)
        retry_policy = RetryPolicy(cfg)

        def _rec(status: ExecutionStatus, attempt: int = 1, error_code: str | None = None) -> ExecutionRecord:
            return ExecutionRecord(
                task_id="t1",
                agent_id="reference",
                agent_version="1.0.0",
                tenant_id="org-1",
                requested_by="u1",
                status=status,
                goal="test",
                correlation_id="c1",
                attempt_number=attempt,
                error_code=error_code,
            )

        assert retry_policy.is_eligible(_rec(ExecutionStatus.TIMED_OUT, 1, "EXECUTION_TIMED_OUT"))[0] is True
        assert retry_policy.is_eligible(_rec(ExecutionStatus.FAILED, 2, "AGENT_EXECUTION_FAILED"))[0] is True
        assert retry_policy.is_eligible(_rec(ExecutionStatus.SUCCEEDED, 1))[0] is False
        assert retry_policy.is_eligible(_rec(ExecutionStatus.RUNNING, 1))[0] is False
        assert retry_policy.is_eligible(_rec(ExecutionStatus.FAILED, 3, "AGENT_EXECUTION_FAILED"))[0] is False
        assert retry_policy.is_eligible(_rec(ExecutionStatus.FAILED, 1, AgentErrorCode.AGENT_UNAUTHORIZED.value))[0] is False
        assert retry_policy.is_eligible(_rec(ExecutionStatus.FAILED, 1, AgentErrorCode.AGENT_PROMPT_INJECTION_BLOCKED.value))[0] is False

        d1 = retry_policy.compute_backoff_seconds(1, seed="exec-1")
        d2 = retry_policy.compute_backoff_seconds(2, seed="exec-1")
        d5 = retry_policy.compute_backoff_seconds(5, seed="exec-1")
        assert 0.5 <= d1 <= 0.6
        assert 1.0 <= d2 <= 1.2
        assert d5 <= 4.0

    @pytest.mark.asyncio
    async def test_direct_policy_run_raises_timeout_and_cancel_cleanly(self) -> None:
        policy = KeepExecutionPolicy()

        async def _hang() -> AgentResult:
            await asyncio.sleep(5.0)
            return AgentResult(status="succeeded")

        with pytest.raises(ExecutionTimeoutError):
            await policy.run_with_controls(
                _hang(),
                execution_id="exec-direct-to",
                agent_id="reference",
                tenant_id="org-1",
                timeout_seconds=0.05,
            )

        # Pre-cancelled token triggers ExecutionCancelledError immediately
        policy.cancellation_registry.register("exec-pre-cancel").cancel()
        coro = _hang()
        try:
            with pytest.raises(ExecutionCancelledError):
                await policy.run_with_controls(
                    coro,
                    execution_id="exec-pre-cancel",
                    agent_id="reference",
                    tenant_id="org-1",
                    timeout_seconds=5.0,
                )
        finally:
            coro.close()
