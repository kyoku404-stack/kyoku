"""KEEP Phase 4.2 — AgentRuntime Core Execution Coordinator.

Coordinates agent resolution via Phase 4.1 `AgentRegistry`, authorization and
safety controls via `ExecutionPolicyInterface`, durable state transitions via
`ExecutionRepository`, background dispatch, cancellation, bounded retries, and
crash recovery — completely decoupled from FastAPI route handlers.

Owner: Member 1 (Runtime Architecture & Execution Lifecycle)
Specification: devdocs/p4/p4.2.txt (Sections 3, 4, 5, 9, 13)
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from backend.app.agents.contracts import AgentContext, AgentRequest, AgentResult
from backend.app.agents.errors import (
    AgentContractValidationError,
    AgentErrorCode,
    AgentLayerError,
    ExecutionCancelledError,
    ExecutionNotFoundError,
    ExecutionNotRetryableError,
    ExecutionResultNotReadyError,
    ExecutionTimeoutError,
    IdempotencyConflictError,
    InvalidExecutionTransitionError,
    sanitize_error_message,
)
from backend.app.agents.registry import AgentRegistry
from backend.app.agents.runtime.context import build_runtime_context
from backend.app.agents.runtime.interfaces import (
    BackgroundDispatcher,
    ExecutionPolicyInterface,
    ExecutionRepository,
    RuntimeObserver,
)
from backend.app.agents.runtime.lifecycle import (
    ExecutionMode,
    ExecutionRecord,
    ExecutionStatus,
    generate_execution_id,
)


def compute_request_fingerprint(
    *,
    agent_id: str,
    goal: str,
    input_payload: dict[str, Any],
) -> str:
    """Computes a deterministic SHA-256 fingerprint for idempotency conflict detection."""
    canonical = json.dumps(
        {
            "agent_id": agent_id.strip().lower(),
            "goal": goal.strip(),
            "input": input_payload,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class _NoOpObserver:
    """Default observer used when no metrics/logging collector is injected."""

    def record_event(
        self,
        event_type: str,
        *,
        record: ExecutionRecord,
        details: dict[str, Any] | None = None,
    ) -> None:
        return None

    def record_validation_failure(self, *, execution_id: str, agent_id: str) -> None:
        return None


class AgentRuntime:
    """Framework-agnostic KEEP Agent Runtime & Execution Engine (Phase 4.2)."""

    def __init__(
        self,
        *,
        registry: AgentRegistry,
        repository: ExecutionRepository,
        policy: ExecutionPolicyInterface,
        dispatcher: BackgroundDispatcher | None = None,
        observer: RuntimeObserver | None = None,
    ) -> None:
        self.registry = registry
        self.repository = repository
        self.policy = policy
        self.dispatcher = dispatcher
        self.observer: RuntimeObserver = observer or _NoOpObserver()

    async def submit(
        self,
        agent_id: str,
        request: AgentRequest,
        context: AgentContext,
        *,
        mode: ExecutionMode = "sync",
        idempotency_key: str | None = None,
        timeout_seconds: float | None = None,
        parent_execution_id: str | None = None,
        attempt_number: int = 1,
    ) -> ExecutionRecord:
        """Validates, authorizes, persists, and executes (or enqueues) an agent task."""
        normalized_agent_id = agent_id.strip().lower()
        agent = self.registry.get(normalized_agent_id)
        metadata = self.registry.get_metadata(normalized_agent_id)

        # 1. Enforce input/resource limits & Phase 4.1 security authorization BEFORE persistence
        self.policy.validate_request_limits(request)
        self.policy.authorize(metadata, request, context)

        effective_timeout = self.policy.resolve_timeout(timeout_seconds)
        effective_request = (
            request
            if request.correlation_id
            else request.model_copy(update={"correlation_id": context.correlation_id})
        )
        cleaned_key = idempotency_key.strip() if idempotency_key and idempotency_key.strip() else None
        fingerprint = compute_request_fingerprint(
            agent_id=normalized_agent_id,
            goal=effective_request.goal,
            input_payload=effective_request.input,
        )

        # 2. Scoped idempotency check (tenant_id + requested_by + key) with fingerprint verification
        if cleaned_key is not None:
            existing = await self.repository.find_by_idempotency_key(
                tenant_id=context.tenant_id,
                requested_by=context.user_id,
                idempotency_key=cleaned_key,
            )
            if existing is not None:
                if existing.request_fingerprint != fingerprint:
                    raise IdempotencyConflictError(cleaned_key)
                return existing

        # 3. Create durable PENDING execution record BEFORE invocation or dispatch
        now = datetime.now(UTC)
        execution_id = generate_execution_id()
        record = ExecutionRecord(
            execution_id=execution_id,
            task_id=effective_request.task_id,
            agent_id=normalized_agent_id,
            agent_version=agent.metadata.version,
            tenant_id=context.tenant_id,
            requested_by=context.user_id,
            status=ExecutionStatus.PENDING,
            mode=mode,
            goal=effective_request.goal,
            input_payload=dict(effective_request.input),
            correlation_id=effective_request.correlation_id or context.correlation_id,
            attempt_number=attempt_number,
            parent_execution_id=parent_execution_id,
            idempotency_key=cleaned_key,
            request_fingerprint=fingerprint,
            created_at=now,
            deadline_at=now + timedelta(seconds=effective_timeout),
            checkpoint_thread_id=f"{context.tenant_id}:{effective_request.task_id}:{execution_id}",
        )

        try:
            persisted = await self.repository.create(record)
        except IdempotencyConflictError:
            # Handle race condition on simultaneous identical submissions gracefully
            if cleaned_key is not None:
                existing = await self.repository.find_by_idempotency_key(
                    tenant_id=context.tenant_id,
                    requested_by=context.user_id,
                    idempotency_key=cleaned_key,
                )
                if existing is not None and existing.request_fingerprint == fingerprint:
                    return existing
            raise

        self.observer.record_event("execution.created", record=persisted)

        # 4. Async background mode vs Synchronous execution
        if mode == "async" and self.dispatcher is not None:
            try:
                await self.dispatcher.enqueue(persisted.execution_id, effective_request, context)
            except (RuntimeError, ValueError, OSError) as exc:
                failed = await self.repository.mark_failed(
                    persisted.execution_id,
                    error_code=AgentErrorCode.AGENT_EXECUTION_FAILED.value,
                    error_message=sanitize_error_message(f"Failed to enqueue execution: {exc}"),
                )
                self.observer.record_event("execution.failed", record=failed)
                raise
            self.observer.record_event("execution.queued", record=persisted)
            return persisted

        return await self.execute_existing(
            persisted.execution_id,
            effective_request,
            context,
            timeout_seconds=effective_timeout,
        )

    async def execute_existing(
        self,
        execution_id: str,
        request: AgentRequest,
        context: AgentContext,
        *,
        timeout_seconds: float | None = None,
    ) -> ExecutionRecord:
        """Executes a previously persisted PENDING record with atomic lifecycle tracking."""
        record = await self.repository.get(execution_id, tenant_id=context.tenant_id)
        if record is None:
            raise ExecutionNotFoundError(execution_id)

        # If already cancelled or terminal before worker picked it up, do NOT overwrite!
        if record.is_terminal:
            return record
        if record.cancel_requested:
            cancelled = await self.repository.mark_cancelled(
                execution_id,
                reason="Cancelled prior to execution start.",
            )
            self.observer.record_event("execution.cancelled", record=cancelled)
            return cancelled

        # Re-verify agent availability and authorization before starting (handles revoked access)
        agent = self.registry.get(record.agent_id)
        metadata = self.registry.get_metadata(record.agent_id)
        self.policy.authorize(metadata, request, context)

        # Atomic PENDING -> RUNNING transition
        try:
            running_record = await self.repository.mark_running(execution_id)
        except InvalidExecutionTransitionError:
            # Another worker or cancellation raced ahead; return authoritative record
            latest = await self.repository.get(execution_id, tenant_id=context.tenant_id)
            if latest is None:
                raise ExecutionNotFoundError(execution_id) from None
            return latest

        self.observer.record_event("execution.started", record=running_record)

        effective_timeout = self.policy.resolve_timeout(timeout_seconds)
        runtime_ctx = build_runtime_context(
            execution_id=execution_id,
            agent_context=context,
            timeout_seconds=effective_timeout,
            attempt_number=running_record.attempt_number,
        )

        try:
            raw_result = await self.policy.run_with_controls(
                agent.invoke(request, runtime_ctx.agent_context),
                execution_id=execution_id,
                agent_id=record.agent_id,
                tenant_id=context.tenant_id,
                timeout_seconds=effective_timeout,
            )
        except ExecutionTimeoutError as exc:
            timed_out = await self._safe_mark_terminal(
                execution_id,
                context.tenant_id,
                self.repository.mark_timed_out(
                    execution_id,
                    error_code=exc.code.value,
                    error_message=exc.safe_message,
                ),
            )
            self.observer.record_event("execution.timed_out", record=timed_out)
            return timed_out
        except ExecutionCancelledError as exc:
            cancelled = await self._safe_mark_terminal(
                execution_id,
                context.tenant_id,
                self.repository.mark_cancelled(
                    execution_id,
                    reason=exc.safe_message,
                ),
            )
            self.observer.record_event("execution.cancelled", record=cancelled)
            return cancelled
        except AgentLayerError as exc:
            # Propagate concurrency saturation (429) vs record failure
            if exc.code == AgentErrorCode.EXECUTION_CONCURRENCY_LIMIT:
                failed = await self._safe_mark_terminal(
                    execution_id,
                    context.tenant_id,
                    self.repository.mark_failed(
                        execution_id,
                        error_code=exc.code.value,
                        error_message=exc.safe_message,
                    ),
                )
                self.observer.record_event("execution.failed", record=failed)
                raise
            failed = await self._safe_mark_terminal(
                execution_id,
                context.tenant_id,
                self.repository.mark_failed(
                    execution_id,
                    error_code=exc.code.value,
                    error_message=exc.safe_message,
                ),
            )
            self.observer.record_event("execution.failed", record=failed)
            return failed
        except (RuntimeError, ValueError, TypeError, KeyError, LookupError, OSError) as exc:
            safe_msg = sanitize_error_message(
                f"Agent '{record.agent_id}' failed during execution: {exc}"
            )
            failed = await self._safe_mark_terminal(
                execution_id,
                context.tenant_id,
                self.repository.mark_failed(
                    execution_id,
                    error_code=AgentErrorCode.AGENT_EXECUTION_FAILED.value,
                    error_message=safe_msg,
                ),
            )
            self.observer.record_event("execution.failed", record=failed)
            return failed

        # Validate returned AgentResult contract strictly before persistence
        try:
            if not isinstance(raw_result, AgentResult):
                raise AgentContractValidationError(
                    f"Agent '{record.agent_id}' returned invalid result type '{type(raw_result).__name__}'."
                )
            validated = AgentResult.model_validate(raw_result.model_dump())
        except (AgentContractValidationError, ValueError) as exc:
            self.observer.record_validation_failure(
                execution_id=execution_id,
                agent_id=record.agent_id,
            )
            failed = await self._safe_mark_terminal(
                execution_id,
                context.tenant_id,
                self.repository.mark_failed(
                    execution_id,
                    error_code=AgentErrorCode.AGENT_CONTRACT_INVALID.value,
                    error_message=sanitize_error_message(str(exc)),
                ),
            )
            self.observer.record_event("execution.failed", record=failed)
            return failed

        # Check whether cancellation raced with completion
        latest_before_finish = await self.repository.get(execution_id, tenant_id=context.tenant_id)
        if latest_before_finish is not None and latest_before_finish.status == ExecutionStatus.CANCELLED:
            return latest_before_finish

        if validated.status == "succeeded":
            done = await self._safe_mark_terminal(
                execution_id,
                context.tenant_id,
                self.repository.mark_succeeded(
                    execution_id,
                    result_payload=validated.model_dump(mode="json"),
                ),
            )
            self.observer.record_event("execution.succeeded", record=done)
            return done

        failed = await self._safe_mark_terminal(
            execution_id,
            context.tenant_id,
            self.repository.mark_failed(
                execution_id,
                error_code=validated.error_code or AgentErrorCode.AGENT_EXECUTION_FAILED.value,
                error_message=validated.error_message or "Agent returned failed status.",
                result_payload=validated.model_dump(mode="json"),
            ),
        )
        self.observer.record_event("execution.failed", record=failed)
        return failed

    async def _safe_mark_terminal(
        self,
        execution_id: str,
        tenant_id: str,
        transition_coro,
    ) -> ExecutionRecord:
        """Applies a terminal state transition safely, respecting terminal immutability on races."""
        try:
            return await transition_coro
        except InvalidExecutionTransitionError:
            latest = await self.repository.get(execution_id, tenant_id=tenant_id)
            if latest is None:
                raise ExecutionNotFoundError(execution_id) from None
            return latest

    async def get_execution(
        self,
        execution_id: str,
        context: AgentContext,
    ) -> ExecutionRecord:
        """Retrieves an execution record strictly within `context.tenant_id` (404 concealment)."""
        record = await self.repository.get(execution_id, tenant_id=context.tenant_id)
        if record is None:
            raise ExecutionNotFoundError(execution_id)
        return record

    async def list_executions(
        self,
        context: AgentContext,
        *,
        agent_id: str | None = None,
        status: ExecutionStatus | None = None,
        limit: int = 50,
    ) -> list[ExecutionRecord]:
        """Lists execution records strictly scoped to `context.tenant_id`."""
        return await self.repository.list_executions(
            tenant_id=context.tenant_id,
            agent_id=agent_id,
            status=status,
            limit=limit,
        )

    async def get_result(
        self,
        execution_id: str,
        context: AgentContext,
    ) -> AgentResult:
        """Retrieves the validated AgentResult for a completed execution."""
        record = await self.get_execution(execution_id, context)
        if not record.is_terminal:
            raise ExecutionResultNotReadyError(execution_id, record.status.value)

        if record.result_payload is not None:
            return AgentResult.model_validate(record.result_payload)

        # Synthesize canonical failed AgentResult for timed_out / cancelled / failed without payload
        code_value = record.error_code or AgentErrorCode.AGENT_EXECUTION_FAILED.value
        try:
            err_code = AgentErrorCode(code_value)
        except ValueError:
            err_code = AgentErrorCode.AGENT_EXECUTION_FAILED
        return AgentResult.failure(
            code=err_code,
            message=record.error_message or f"Execution ended with status {record.status.value}.",
        )

    async def cancel_execution(
        self,
        execution_id: str,
        context: AgentContext,
    ) -> ExecutionRecord:
        """Requests cancellation: atomically cancels PENDING, cooperatively signals RUNNING."""
        record = await self.get_execution(execution_id, context)
        if record.is_terminal:
            raise InvalidExecutionTransitionError(
                execution_id,
                record.status.value,
                ExecutionStatus.CANCELLED.value,
            )

        updated = await self.repository.request_cancel(execution_id, tenant_id=context.tenant_id)
        self.observer.record_event("execution.cancel_requested", record=updated)

        if updated.status == ExecutionStatus.CANCELLED:
            self.observer.record_event("execution.cancelled", record=updated)
            return updated

        # Running execution: signal cooperative cancellation token
        self.policy.signal_cancel(execution_id)
        return updated

    async def retry_execution(
        self,
        execution_id: str,
        context: AgentContext,
        *,
        mode: ExecutionMode | None = None,
        timeout_seconds: float | None = None,
    ) -> ExecutionRecord:
        """Creates a new linked execution attempt without mutating the original terminal record."""
        original = await self.get_execution(execution_id, context)
        eligible, reason = self.policy.can_retry(original)
        if not eligible:
            raise ExecutionNotRetryableError(execution_id, reason)

        retry_request = AgentRequest(
            task_id=original.task_id,
            goal=original.goal,
            input=dict(original.input_payload),
            correlation_id=context.correlation_id,
        )
        self.observer.record_event(
            "execution.retry_scheduled",
            record=original,
            details={"next_attempt": original.attempt_number + 1},
        )
        return await self.submit(
            original.agent_id,
            retry_request,
            context,
            mode=mode or original.mode,
            timeout_seconds=timeout_seconds,
            parent_execution_id=original.execution_id,
            attempt_number=original.attempt_number + 1,
        )

    async def reconcile_stale_executions(
        self,
        *,
        stale_after_seconds: int = 300,
    ) -> list[ExecutionRecord]:
        """Reconciles abandoned RUNNING executions left behind by worker crashes."""
        cutoff = datetime.now(UTC) - timedelta(seconds=stale_after_seconds)
        stale = await self.repository.find_stale_running(stale_before=cutoff)
        reconciled: list[ExecutionRecord] = []
        for record in stale:
            try:
                updated = await self.repository.mark_failed(
                    record.execution_id,
                    error_code=AgentErrorCode.AGENT_EXECUTION_FAILED.value,
                    error_message="Execution reconciled after worker crash or heartbeat timeout.",
                )
                self.observer.record_event("execution.failed", record=updated, details={"recovered": True})
                reconciled.append(updated)
            except InvalidExecutionTransitionError:
                continue
        return reconciled
