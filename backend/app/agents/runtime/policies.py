"""KEEP Phase 4.2 — Execution Safety Policies, Timeout Wrapper & Bounded Retry Engine.

Combines Phase 4.1's `KeepAgentPolicyEngine` (RBAC, tenant isolation, prompt guardrails)
with Phase 4.2 runtime safety controls:
- Default & maximum execution timeout clamping.
- Input byte-size ceiling validation.
- Cooperative cancellation & clean timeout-vs-cancellation classification.
- Global, per-agent, and per-tenant concurrency slot reservation with guaranteed release.
- Bounded transient-only retry eligibility with exponential backoff and jitter.

Owner: Member 3 (Execution Safety & Resource Control)
Specification: devdocs/p4/p4.2.txt (Sections 3, 5, 9, 13)
"""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Awaitable

from backend.app.agents.contracts import AgentContext, AgentRequest, AgentResult
from backend.app.agents.errors import (
    AgentErrorCode,
    ExecutionCancelledError,
    ExecutionTimeoutError,
)
from backend.app.agents.metadata import AgentMetadata
from backend.app.agents.runtime.cancellation import CancellationRegistry
from backend.app.agents.runtime.lifecycle import ExecutionRecord, ExecutionStatus
from backend.app.agents.runtime.limits import (
    ConcurrencyLimiter,
    ExecutionLimitsConfig,
    validate_input_size,
)
from backend.app.services.security.agent_policy import (
    AgentPolicyInterface,
    KeepAgentPolicyEngine,
)

NON_RETRYABLE_ERROR_CODES: frozenset[str] = frozenset(
    {
        AgentErrorCode.AGENT_NOT_FOUND.value,
        AgentErrorCode.AGENT_DISABLED.value,
        AgentErrorCode.AGENT_CONTRACT_INVALID.value,
        AgentErrorCode.AGENT_SCHEMA_VERSION_UNSUPPORTED.value,
        AgentErrorCode.AGENT_UNTRUSTED_CONTEXT.value,
        AgentErrorCode.AGENT_UNAUTHORIZED.value,
        AgentErrorCode.AGENT_CAPABILITY_DENIED.value,
        AgentErrorCode.AGENT_TENANT_ISOLATION_VIOLATION.value,
        AgentErrorCode.AGENT_PROMPT_INJECTION_BLOCKED.value,
        AgentErrorCode.AGENT_TOOL_UNAUTHORIZED.value,
        AgentErrorCode.EXECUTION_INPUT_TOO_LARGE.value,
    }
)


class RetryPolicy:
    """Bounded transient-only retry evaluator with deterministic exponential backoff + jitter."""

    def __init__(self, config: ExecutionLimitsConfig | None = None) -> None:
        self.config = config or ExecutionLimitsConfig()

    def is_eligible(self, record: ExecutionRecord) -> tuple[bool, str]:
        """Determines whether a completed execution attempt may be safely retried."""
        if not record.is_terminal:
            return False, f"Execution is still active (status={record.status.value})."
        if record.status == ExecutionStatus.SUCCEEDED:
            return False, "Succeeded executions cannot be retried."
        if record.attempt_number >= self.config.max_retries:
            return (
                False,
                f"Maximum retry attempts ({self.config.max_retries}) reached.",
            )
        if record.error_code and record.error_code in NON_RETRYABLE_ERROR_CODES:
            return (
                False,
                f"Error category '{record.error_code}' is non-retryable.",
            )
        return True, "Eligible for bounded retry."

    def compute_backoff_seconds(self, attempt_number: int, *, seed: str = "") -> float:
        """Computes bounded exponential backoff with deterministic bounded jitter (0-20%)."""
        exponent = max(0, attempt_number - 1)
        raw_delay = min(
            self.config.max_backoff_seconds,
            self.config.base_backoff_seconds * (2**exponent),
        )
        digest = hashlib.sha256(f"{seed}:{attempt_number}".encode()).digest()
        jitter_ratio = (digest[0] / 255.0) * 0.2
        return round(min(self.config.max_backoff_seconds, raw_delay * (1.0 + jitter_ratio)), 4)


class KeepExecutionPolicy:
    """Default Phase 4.2 ExecutionPolicy combining security, limits, cancellation, and retries."""

    def __init__(
        self,
        *,
        config: ExecutionLimitsConfig | None = None,
        security_policy: AgentPolicyInterface | None = None,
        concurrency_limiter: ConcurrencyLimiter | None = None,
        cancellation_registry: CancellationRegistry | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.config = config or ExecutionLimitsConfig()
        self.security_policy: AgentPolicyInterface = security_policy or KeepAgentPolicyEngine()
        self.concurrency_limiter = concurrency_limiter or ConcurrencyLimiter(self.config)
        self.cancellation_registry = cancellation_registry or CancellationRegistry()
        self.retry_policy = retry_policy or RetryPolicy(self.config)

    def resolve_timeout(self, requested_timeout: float | None) -> float:
        """Clamps caller timeout within `[min_timeout_seconds, max_timeout_seconds]`."""
        if requested_timeout is None:
            return self.config.default_timeout_seconds
        clamped = max(self.config.min_timeout_seconds, float(requested_timeout))
        return min(self.config.max_timeout_seconds, clamped)

    def validate_request_limits(self, request: AgentRequest) -> None:
        """Enforces input payload size limits prior to execution or persistence."""
        validate_input_size(request, max_bytes=self.config.max_input_bytes)

    def authorize(
        self,
        metadata: AgentMetadata,
        request: AgentRequest,
        context: AgentContext,
    ) -> None:
        """Delegates identity, RBAC capability, tenant, and guardrail checks to Phase 4.1 policy."""
        self.security_policy.authorize_invocation(metadata, request, context)

    def can_retry(self, record: ExecutionRecord) -> tuple[bool, str]:
        """Evaluates retry eligibility via RetryPolicy."""
        return self.retry_policy.is_eligible(record)

    def signal_cancel(self, execution_id: str) -> bool:
        """Signals cooperative cancellation on a running execution."""
        return self.cancellation_registry.request_cancel(execution_id)

    async def run_with_controls(
        self,
        coro: Awaitable[AgentResult],
        *,
        execution_id: str,
        agent_id: str,
        tenant_id: str,
        timeout_seconds: float,
    ) -> AgentResult:
        """Runs an agent coroutine under concurrency limits, timeout, and cancellation tracking."""
        effective_timeout = self.resolve_timeout(timeout_seconds)
        async with self.concurrency_limiter.slot(agent_id=agent_id, tenant_id=tenant_id):
            token = self.cancellation_registry.register(execution_id)
            task = asyncio.ensure_future(coro)
            self.cancellation_registry.bind_task(execution_id, task)
            try:
                if token.is_cancelled:
                    task.cancel()
                    raise ExecutionCancelledError(execution_id)
                return await asyncio.wait_for(task, timeout=effective_timeout)
            except TimeoutError as exc:
                token.cancel("Execution timeout exceeded.")
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except (asyncio.CancelledError, RuntimeError, ValueError, TypeError, OSError):
                        pass
                raise ExecutionTimeoutError(execution_id, effective_timeout) from exc
            except asyncio.CancelledError as exc:
                if token.is_cancelled:
                    token.acknowledge()
                    raise ExecutionCancelledError(execution_id) from exc
                raise
            finally:
                self.cancellation_registry.unregister(execution_id)
