"""KEEP Phase 4.3 — Workflow Recovery, Stale Reconciliation & Safe Checkpoint Resume.

Reconciles workflows left in RUNNING state after worker crashes, validates checkpoint
safety against non-idempotent side effects, and enforces current RBAC re-authorization
prior to resuming any workflow (ADR-076).

Owner: Member 3 (Workflow Reliability, Security & Recovery)
Specification: devdocs/p4/p4.3.txt (Sections 3, 8, 9)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import (
    AgentErrorCode,
    WorkflowRecoveryNotAllowedError,
)
from backend.app.agents.orchestration.policies import KeepWorkflowPolicyEngine
from backend.app.agents.orchestration.workflow_contracts import (
    RECOVERABLE_WORKFLOW_STATUSES,
    WorkflowDefinition,
    WorkflowExecutionRecord,
    WorkflowRepositoryInterface,
    WorkflowStatus,
    WorkflowStepLink,
)
from pydantic import BaseModel, Field


class StaleReconciliationReport(BaseModel):
    """Summary of stale RUNNING workflows reconciled after a crash or timeout."""

    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reconciled_ids: list[str] = Field(default_factory=list)

    @property
    def reconciled_count(self) -> int:
        return len(self.reconciled_ids)


class WorkflowRecoveryManager:
    """Manages crash reconciliation and safe checkpoint-backed workflow resumption."""

    def __init__(
        self,
        *,
        repository: WorkflowRepositoryInterface,
        policy: KeepWorkflowPolicyEngine | None = None,
        orchestration_service: Any | None = None,
    ) -> None:
        self.repository = repository
        self.policy = policy or KeepWorkflowPolicyEngine()
        self.orchestration_service = orchestration_service

    async def reconcile_stale_workflows(
        self,
        *,
        now: datetime | None = None,
    ) -> StaleReconciliationReport:
        """Marks expired RUNNING workflows (e.g. after worker crash) as TIMED_OUT for safe recovery."""
        check_time = now or datetime.now(UTC)
        stale_records = await self.repository.list_stale_running(check_time)
        reconciled: list[str] = []

        for rec in stale_records:
            duration_ms = (
                max(0, int((check_time - rec.started_at).total_seconds() * 1000))
                if rec.started_at
                else 0
            )
            await self.repository.mark_completed(
                rec.workflow_execution_id,
                rec.tenant_id,
                status=WorkflowStatus.TIMED_OUT,
                result=None,
                completed_at=check_time,
                duration_ms=duration_ms,
                error_code=AgentErrorCode.WORKFLOW_TIMEOUT.value,
                error_message="Workflow reconciled as TIMED_OUT after exceeding deadline or worker crash.",
            )
            reconciled.append(rec.workflow_execution_id)

        return StaleReconciliationReport(checked_at=check_time, reconciled_ids=reconciled)

    def validate_safe_resume(
        self,
        definition: WorkflowDefinition,
        record: WorkflowExecutionRecord,
        steps: list[WorkflowStepLink],
        context: AgentContext,
    ) -> set[str]:
        """Re-verifies authorization and idempotency safety; returns already-completed node names."""
        if record.status not in RECOVERABLE_WORKFLOW_STATUSES:
            raise WorkflowRecoveryNotAllowedError(
                record.workflow_execution_id,
                f"Status '{record.status.value}' is not recoverable.",
            )

        # Re-verify current permissions & tenant boundary (ADR-076)
        self.policy.authorize_resume(definition, record, context)

        # Block blind replay of non-idempotent side-effecting steps
        unsafe = [
            s.node_name
            for s in steps
            if s.is_side_effecting and s.status != "SUCCEEDED"
        ]
        if unsafe:
            raise WorkflowRecoveryNotAllowedError(
                record.workflow_execution_id,
                f"Non-idempotent side-effecting step(s) cannot be replayed automatically: {', '.join(unsafe)}.",
            )

        return {s.node_name for s in steps if s.status == "SUCCEEDED"}

    async def resume(
        self,
        workflow_execution_id: str,
        context: AgentContext,
    ) -> WorkflowExecutionRecord:
        """Resumes a recoverable workflow via KeepOrchestrationService after safety & auth checks."""
        if self.orchestration_service is None:
            raise RuntimeError("WorkflowRecoveryManager requires an orchestration_service to resume.")
        return await self.orchestration_service.resume_workflow(workflow_execution_id, context)
