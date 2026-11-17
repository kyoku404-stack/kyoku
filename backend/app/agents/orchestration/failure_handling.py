"""KEEP Phase 4.3 — Explicit Workflow Failure Handling & Side-Effect Guards.

Separates agent-level failure from workflow-level failure using explicit required vs
optional step policies, bounded transient-only retries, and strict prevention of
unsafe non-idempotent side-effect replays.

Owner: Member 3 (Workflow Reliability, Security & Recovery)
Specification: devdocs/p4/p4.3.txt (Sections 3, 9)
"""

from __future__ import annotations

from enum import Enum

from backend.app.agents.errors import AgentErrorCode
from backend.app.agents.orchestration.workflow_contracts import (
    WorkflowDefinition,
    WorkflowStatus,
    WorkflowStepRole,
)
from pydantic import BaseModel

TRANSIENT_FAILURE_CODES: frozenset[str] = frozenset(
    {
        AgentErrorCode.EXECUTION_TIMED_OUT.value,
        AgentErrorCode.EXECUTION_CONCURRENCY_LIMIT.value,
        AgentErrorCode.WORKFLOW_TIMEOUT.value,
    }
)


class FailureDisposition(str, Enum):
    """Explicit workflow-level response to an individual step failure."""

    FAIL_WORKFLOW = "FAIL_WORKFLOW"
    CONTINUE_PARTIAL = "CONTINUE_PARTIAL"
    RETRY_STEP = "RETRY_STEP"
    ROUTE_FALLBACK = "ROUTE_FALLBACK"


class StepFailureDecision(BaseModel):
    """Structured outcome produced by WorkflowFailureHandler for a failed step."""

    node_name: str
    disposition: FailureDisposition
    reason: str
    warning: str | None = None
    safe_to_retry: bool = False


class WorkflowFailureHandler:
    """Evaluates step failures against workflow policy and resolves final workflow status."""

    def __init__(self, *, max_step_retries: int = 2) -> None:
        self.max_step_retries = max_step_retries

    def evaluate_step_failure(
        self,
        definition: WorkflowDefinition,
        *,
        node_name: str,
        role: WorkflowStepRole,
        error_code: str | None,
        retryable: bool = False,
        attempt_number: int = 1,
        is_side_effecting: bool = False,
    ) -> StepFailureDecision:
        """Determines whether to retry, continue with partial result, or fail the workflow."""
        # Non-idempotent side-effecting steps MUST NEVER be auto-replayed (devdocs/p4/p4.3.txt Section 3 & 8)
        if is_side_effecting:
            if role == "optional" and definition.allow_partial_success:
                return StepFailureDecision(
                    node_name=node_name,
                    disposition=FailureDisposition.CONTINUE_PARTIAL,
                    reason="Optional side-effecting step failed; auto-retry blocked to prevent duplicate side effects.",
                    warning=f"Optional step '{node_name}' failed without replay (non-idempotent side effect).",
                    safe_to_retry=False,
                )
            return StepFailureDecision(
                node_name=node_name,
                disposition=FailureDisposition.FAIL_WORKFLOW,
                reason="Required side-effecting step failed; automatic replay prohibited.",
                safe_to_retry=False,
            )

        is_transient = retryable or (error_code in TRANSIENT_FAILURE_CODES)
        if is_transient and attempt_number <= self.max_step_retries:
            return StepFailureDecision(
                node_name=node_name,
                disposition=FailureDisposition.RETRY_STEP,
                reason=f"Transient failure ({error_code or 'retryable'}) within retry budget ({attempt_number}/{self.max_step_retries}).",
                safe_to_retry=True,
            )

        if role == "optional" and definition.allow_partial_success:
            return StepFailureDecision(
                node_name=node_name,
                disposition=FailureDisposition.CONTINUE_PARTIAL,
                reason=f"Optional step '{node_name}' failed; workflow policy allows partial success.",
                warning=f"Optional step '{node_name}' failed ({error_code or 'STEP_ERROR'}); returning partial result.",
                safe_to_retry=False,
            )

        return StepFailureDecision(
            node_name=node_name,
            disposition=FailureDisposition.FAIL_WORKFLOW,
            reason=f"Required step '{node_name}' failed ({error_code or 'STEP_ERROR'}).",
            safe_to_retry=False,
        )

    def resolve_final_workflow_status(
        self,
        definition: WorkflowDefinition,
        *,
        required_failures: list[str],
        optional_failures: list[str],
    ) -> WorkflowStatus:
        """Determines canonical WorkflowStatus explicitly rather than inferring from graph termination."""
        if required_failures:
            return WorkflowStatus.FAILED
        if optional_failures:
            if definition.allow_partial_success:
                return WorkflowStatus.PARTIALLY_SUCCEEDED
            return WorkflowStatus.FAILED
        return WorkflowStatus.SUCCEEDED
