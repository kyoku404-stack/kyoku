"""KEEP Phase 4.9 — Autonomous Workflow Controller.

Manages workflow lifecycle states, objectives, budgets, deadlines, supported
workflow validation, stopping conditions, and explicit decision/event trails.

Owner: Member 1 (Autonomous Controller & Lifecycle)
Specification: devdocs/p4/p4.9.txt (Sections 3, 4, 5)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from backend.app.agents.autonomy.contracts import (
    DEFAULT_SUPPORTED_WORKFLOW_TYPES,
    SERVER_MAX_AGENT_ATTEMPTS,
    SERVER_MAX_DEADLINE_SECONDS,
    SERVER_MAX_REPLANS,
    SERVER_MAX_STEPS,
    TERMINAL_AUTONOMY_STATUSES,
    AutonomousWorkflowRecord,
    AutonomousWorkflowRequest,
    AutonomyBudgetSnapshot,
    AutonomyDecisionRecord,
    AutonomyEventRecord,
    AutonomyPolicy,
    AutonomySecurityContext,
    AutonomyStatus,
    DecisionAction,
    EvaluationResult,
    compute_autonomy_fingerprint,
    generate_autonomous_execution_id,
    is_valid_autonomy_transition,
)
from backend.app.agents.autonomy.repository import BaseAutonomyRepository
from backend.app.agents.errors import (
    AutonomousWorkflowAccessDeniedError,
    AutonomousWorkflowBudgetExhaustedError,
    AutonomousWorkflowDeadlineExceededError,
    AutonomousWorkflowIdempotencyConflictError,
    AutonomousWorkflowInvalidStateError,
    AutonomousWorkflowNotFoundError,
    AutonomousWorkflowReplanLimitError,
    AutonomousWorkflowUnsupportedTypeError,
)


class AutonomousWorkflowController:
    """Lifecycle controller enforcing budgets, deadlines, stop criteria, and Phase 4.3 validation."""

    def __init__(
        self,
        repository: BaseAutonomyRepository,
        *,
        workflow_registry: Any | None = None,
        supported_workflow_types: frozenset[str] | None = None,
    ) -> None:
        self.repository = repository
        self.workflow_registry = workflow_registry
        self.supported_workflow_types = (
            supported_workflow_types or DEFAULT_SUPPORTED_WORKFLOW_TYPES
        )

    def validate_workflow_type(self, workflow_id: str) -> None:
        """Ensures requested workflow_id is either a supported autonomous type or registered in Phase 4.3."""
        if workflow_id in self.supported_workflow_types:
            return
        if (
            self.workflow_registry is not None
            and hasattr(self.workflow_registry, "is_registered")
            and self.workflow_registry.is_registered(workflow_id)
        ):
            definition = self.workflow_registry.get(workflow_id)
            if getattr(definition, "enabled", True):
                return
        raise AutonomousWorkflowUnsupportedTypeError(workflow_id)

    @staticmethod
    def clamp_policy_server_side(policy: AutonomyPolicy) -> AutonomyPolicy:
        """Applies non-bypassable server-side ceilings onto client-supplied policies (ADR-092)."""
        return policy.model_copy(
            update={
                "max_steps": min(policy.max_steps, SERVER_MAX_STEPS),
                "max_replans": min(policy.max_replans, SERVER_MAX_REPLANS),
                "max_agent_attempts": min(policy.max_agent_attempts, SERVER_MAX_AGENT_ATTEMPTS),
                "deadline_seconds": min(policy.deadline_seconds, SERVER_MAX_DEADLINE_SECONDS),
            }
        )

    async def initialize_workflow(
        self,
        request: AutonomousWorkflowRequest,
        security_context: AutonomySecurityContext,
    ) -> AutonomousWorkflowRecord:
        """Validates type & idempotency, creates durable record & budget, and emits start event."""
        if not security_context.tenant_id or not security_context.user_id:
            raise AutonomousWorkflowAccessDeniedError("Verified tenant and user context required.")

        self.validate_workflow_type(request.workflow_id)
        bounded_policy = self.clamp_policy_server_side(request.policy)
        fingerprint = compute_autonomy_fingerprint(
            request.workflow_id,
            request.objective,
            request.context_metadata,
        )

        if request.idempotency_key:
            existing = await self.repository.find_by_idempotency_key(
                tenant_id=security_context.tenant_id,
                requested_by=security_context.user_id,
                idempotency_key=request.idempotency_key,
            )
            if existing is not None:
                if existing.idempotency_fingerprint != fingerprint:
                    raise AutonomousWorkflowIdempotencyConflictError(request.idempotency_key)
                return existing

        now = datetime.now(UTC)
        execution_id = generate_autonomous_execution_id()
        budget = AutonomyBudgetSnapshot(
            execution_id=execution_id,
            tenant_id=security_context.tenant_id,
            max_steps=bounded_policy.max_steps,
            steps_consumed=0,
            max_replans=bounded_policy.max_replans,
            replans_consumed=0,
            max_agent_attempts=bounded_policy.max_agent_attempts,
            total_agent_attempts=0,
            deadline_seconds=bounded_policy.deadline_seconds,
            updated_at=now,
        )
        record = AutonomousWorkflowRecord(
            execution_id=execution_id,
            tenant_id=security_context.tenant_id,
            requested_by=security_context.user_id,
            workflow_id=request.workflow_id,
            objective=request.objective,
            status="pending",
            policy=bounded_policy,
            budget=budget,
            idempotency_key=request.idempotency_key,
            idempotency_fingerprint=fingerprint,
            deadline_at=now + timedelta(seconds=bounded_policy.deadline_seconds),
            created_at=now,
            updated_at=now,
        )
        persisted = await self.repository.create_workflow(record, budget)
        await self.record_event(
            execution_id=execution_id,
            tenant_id=security_context.tenant_id,
            event_type="workflow.created",
            actor_id=security_context.user_id,
            details={
                "workflow_id": request.workflow_id,
                "max_steps": bounded_policy.max_steps,
                "max_replans": bounded_policy.max_replans,
                "deadline_seconds": bounded_policy.deadline_seconds,
            },
        )
        return persisted

    async def get_workflow_or_raise(
        self,
        execution_id: str,
        security_context: AutonomySecurityContext,
    ) -> AutonomousWorkflowRecord:
        record = await self.repository.get_workflow(execution_id, security_context.tenant_id)
        if record is None:
            raise AutonomousWorkflowNotFoundError(execution_id)
        return record

    async def check_budget_and_deadline(
        self,
        execution_id: str,
        security_context: AutonomySecurityContext,
        *,
        now: datetime | None = None,
        require_step_capacity: bool = True,
    ) -> AutonomyBudgetSnapshot:
        """Evaluates remaining step quota and wall-clock deadline at transition time."""
        record = await self.get_workflow_or_raise(execution_id, security_context)
        budget = await self.repository.get_budget(execution_id, security_context.tenant_id)
        if budget is None:
            raise AutonomousWorkflowNotFoundError(execution_id)

        current_time = now or datetime.now(UTC)
        deadline_at = record.deadline_at
        if deadline_at.tzinfo is None:
            deadline_at = deadline_at.replace(tzinfo=UTC)
        if current_time > deadline_at:
            await self.terminate(
                execution_id,
                security_context,
                target_status="budget_exhausted",
                reason=f"Execution deadline exceeded ({budget.deadline_seconds}s)",
            )
            raise AutonomousWorkflowDeadlineExceededError(execution_id, budget.deadline_seconds)

        if require_step_capacity and budget.steps_consumed >= budget.max_steps:
            await self.terminate(
                execution_id,
                security_context,
                target_status="budget_exhausted",
                reason=f"Step budget exhausted ({budget.steps_consumed}/{budget.max_steps})",
            )
            raise AutonomousWorkflowBudgetExhaustedError(
                execution_id,
                f"Step budget exhausted ({budget.steps_consumed}/{budget.max_steps})",
            )
        return budget

    async def consume_step_budget(
        self,
        execution_id: str,
        security_context: AutonomySecurityContext,
        *,
        attempts_used: int = 1,
    ) -> AutonomyBudgetSnapshot:
        """Increments step & agent attempt counters atomically and saves budget."""
        budget = await self.check_budget_and_deadline(
            execution_id, security_context, require_step_capacity=True
        )
        budget.steps_consumed += 1
        budget.total_agent_attempts += max(1, attempts_used)
        return await self.repository.update_budget(budget)

    async def consume_replan_budget(
        self,
        execution_id: str,
        security_context: AutonomySecurityContext,
    ) -> AutonomyBudgetSnapshot:
        """Validates and consumes a single bounded replan slot."""
        budget = await self.check_budget_and_deadline(
            execution_id, security_context, require_step_capacity=False
        )
        if budget.replans_consumed >= budget.max_replans:
            raise AutonomousWorkflowReplanLimitError(execution_id, budget.max_replans)
        budget.replans_consumed += 1
        updated_budget = await self.repository.update_budget(budget)
        record = await self.get_workflow_or_raise(execution_id, security_context)
        record.replan_count = updated_budget.replans_consumed
        await self.repository.update_workflow(record)
        return updated_budget

    async def transition_status(
        self,
        execution_id: str,
        target_status: AutonomyStatus,
        security_context: AutonomySecurityContext,
        *,
        reason: str | None = None,
        actor_id: str | None = None,
    ) -> AutonomousWorkflowRecord:
        record = await self.get_workflow_or_raise(execution_id, security_context)
        if not is_valid_autonomy_transition(record.status, target_status):
            raise AutonomousWorkflowInvalidStateError(execution_id, record.status, target_status)

        record.status = target_status
        if target_status in TERMINAL_AUTONOMY_STATUSES:
            record.completed_at = datetime.now(UTC)
        if reason:
            record.termination_reason = reason
        updated = await self.repository.update_workflow(record)

        await self.record_event(
            execution_id=execution_id,
            tenant_id=security_context.tenant_id,
            event_type=f"workflow.{target_status}",
            actor_id=actor_id or security_context.user_id,
            details={"status": target_status, "reason": reason or ""},
        )
        return updated

    async def decide_next_action(
        self,
        execution_id: str,
        evaluation: EvaluationResult,
        security_context: AutonomySecurityContext,
        *,
        has_remaining_steps: bool = True,
        pending_write_requires_approval: bool = False,
        now: datetime | None = None,
    ) -> DecisionAction:
        """Determines continue / replan / pause_for_approval / stop_* and persists decision."""
        budget = await self.repository.get_budget(execution_id, security_context.tenant_id)
        record = await self.get_workflow_or_raise(execution_id, security_context)
        remaining = budget.remaining_steps if budget is not None else 0

        current_time = now or datetime.now(UTC)
        deadline_at = record.deadline_at
        if deadline_at.tzinfo is None:
            deadline_at = deadline_at.replace(tzinfo=UTC)

        action: DecisionAction
        reason: str

        if record.status == "cancelled":
            action = "stop_cancelled"
            reason = record.termination_reason or "Workflow was cancelled."
        elif current_time > deadline_at:
            action = "stop_budget_exhausted"
            reason = f"Wall-clock deadline exceeded ({record.policy.deadline_seconds}s)."
        elif evaluation.objective_satisfied and evaluation.evidence_sufficient:
            action = "stop_completed"
            reason = "; ".join(evaluation.reasons) or "Objective satisfied with sufficient evidence."
        elif pending_write_requires_approval or evaluation.requires_human_review:
            action = "pause_for_approval"
            reason = (
                "; ".join(evaluation.reasons)
                or "Side-effecting action or human review threshold reached."
            )
        elif budget is not None and budget.steps_consumed >= budget.max_steps:
            action = "stop_budget_exhausted"
            reason = f"Step budget exhausted ({budget.steps_consumed}/{budget.max_steps})."
        elif evaluation.should_replan:
            if budget is not None and budget.replans_consumed < budget.max_replans:
                action = "replan"
                reason = "; ".join(evaluation.reasons) or "Insufficient evidence; bounded replan permitted."
            else:
                action = "stop_budget_exhausted"
                reason = (
                    f"Replan needed but max_replans ({record.policy.max_replans}) exhausted."
                )
        elif has_remaining_steps:
            action = "continue"
            reason = "; ".join(evaluation.reasons) or "Proceeding to next planned step."
        elif evaluation.objective_satisfied:
            action = "stop_completed"
            reason = (
                "; ".join(evaluation.reasons)
                or "All planned steps executed; completing with noted evidence limitations."
            )
        else:
            action = "stop_failed"
            reason = "; ".join(evaluation.reasons) or "No safe remaining progress possible."

        await self.repository.append_decision(
            AutonomyDecisionRecord(
                execution_id=execution_id,
                tenant_id=security_context.tenant_id,
                action=action,
                reason=reason,
                evaluation_snapshot=evaluation.model_dump(),
                remaining_steps=remaining,
            )
        )
        return action

    async def terminate(
        self,
        execution_id: str,
        security_context: AutonomySecurityContext,
        *,
        target_status: AutonomyStatus,
        reason: str,
        final_result: dict[str, Any] | None = None,
        limitations: list[str] | None = None,
        actor_id: str | None = None,
    ) -> AutonomousWorkflowRecord:
        record = await self.get_workflow_or_raise(execution_id, security_context)
        if record.status in TERMINAL_AUTONOMY_STATUSES:
            return record
        record.status = target_status
        record.termination_reason = reason
        record.completed_at = datetime.now(UTC)
        if final_result is not None:
            record.final_result = final_result
        if limitations is not None:
            record.limitations = list(limitations)
        updated = await self.repository.update_workflow(record)
        await self.record_event(
            execution_id=execution_id,
            tenant_id=security_context.tenant_id,
            event_type=f"workflow.terminated.{target_status}",
            actor_id=actor_id or security_context.user_id,
            details={"reason": reason, "limitations": record.limitations},
        )
        return updated

    async def cancel(
        self,
        execution_id: str,
        reason: str,
        security_context: AutonomySecurityContext,
    ) -> AutonomousWorkflowRecord:
        record = await self.get_workflow_or_raise(execution_id, security_context)
        if record.status in TERMINAL_AUTONOMY_STATUSES:
            raise AutonomousWorkflowInvalidStateError(execution_id, record.status, "cancel")
        await self.repository.append_decision(
            AutonomyDecisionRecord(
                execution_id=execution_id,
                tenant_id=security_context.tenant_id,
                action="stop_cancelled",
                reason=reason,
                remaining_steps=record.budget.remaining_steps if record.budget else 0,
            )
        )
        return await self.terminate(
            execution_id,
            security_context,
            target_status="cancelled",
            reason=reason,
            limitations=[*record.limitations, f"Cancelled early: {reason}"],
            actor_id=security_context.user_id,
        )

    async def record_event(
        self,
        *,
        execution_id: str,
        tenant_id: str,
        event_type: str,
        actor_id: str,
        details: dict[str, Any] | None = None,
    ) -> AutonomyEventRecord:
        return await self.repository.append_event(
            AutonomyEventRecord(
                execution_id=execution_id,
                tenant_id=tenant_id,
                event_type=event_type,
                actor_id=actor_id,
                details=details or {},
            )
        )
