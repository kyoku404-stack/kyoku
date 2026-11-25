"""KEEP Phase 4.9 — Autonomous Workflow Engine Contracts & Schemas.

Defines autonomous workflow lifecycle statuses, bounded autonomy policies,
execution requests, step records, decision logs, events, budgets, evaluation
outcomes, and server-side security contexts.

Owner: Member 1 (Autonomous Controller & Lifecycle)
Specification: devdocs/p4/p4.9.txt (Sections 3, 4, 5, 7)
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, Protocol, runtime_checkable
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

AutonomyStatus = Literal[
    "pending",
    "running",
    "awaiting_approval",
    "completed",
    "failed",
    "budget_exhausted",
    "cancelled",
]

StepStatus = Literal[
    "pending",
    "running",
    "succeeded",
    "failed",
    "skipped",
    "awaiting_approval",
    "cancelled",
]

DecisionAction = Literal[
    "continue",
    "replan",
    "pause_for_approval",
    "stop_completed",
    "stop_failed",
    "stop_budget_exhausted",
    "stop_cancelled",
]

TERMINAL_AUTONOMY_STATUSES: frozenset[str] = frozenset(
    {
        "completed",
        "failed",
        "budget_exhausted",
        "cancelled",
    }
)

ALLOWED_AUTONOMY_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset(
        {"running", "awaiting_approval", "completed", "failed", "budget_exhausted", "cancelled"}
    ),
    "running": frozenset(
        {"running", "awaiting_approval", "completed", "failed", "budget_exhausted", "cancelled"}
    ),
    "awaiting_approval": frozenset({"running", "cancelled", "failed", "budget_exhausted"}),
    "completed": frozenset(),
    "failed": frozenset(),
    "budget_exhausted": frozenset(),
    "cancelled": frozenset(),
}

# Server-side maximum ceilings (ADR-092: client requests cannot exceed platform limits)
SERVER_MAX_STEPS = 25
SERVER_MAX_REPLANS = 3
SERVER_MAX_AGENT_ATTEMPTS = 3
SERVER_MAX_DEADLINE_SECONDS = 1800

DEFAULT_SUPPORTED_WORKFLOW_TYPES: frozenset[str] = frozenset(
    {
        "autonomous_research",
        "autonomous_investigation",
        "churn_investigation",
        "autonomous_collaboration",
        "knowledge_analysis",
    }
)


def is_valid_autonomy_transition(current: str, target: str) -> bool:
    """Returns True if transitioning from `current` status to `target` status is permitted."""
    return target in ALLOWED_AUTONOMY_TRANSITIONS.get(current, frozenset())


def generate_autonomous_execution_id() -> str:
    return f"auto_wf_{uuid4().hex[:16]}"


def generate_autonomous_step_id() -> str:
    return f"auto_step_{uuid4().hex[:16]}"


def generate_autonomy_decision_id() -> str:
    return f"auto_dec_{uuid4().hex[:16]}"


def generate_autonomy_event_id() -> str:
    return f"auto_evt_{uuid4().hex[:16]}"


def compute_autonomy_fingerprint(
    workflow_id: str,
    objective: str,
    context_metadata: dict[str, Any],
) -> str:
    """Computes a deterministic SHA-256 fingerprint for idempotency checks."""
    canonical = json.dumps(
        {
            "workflow_id": workflow_id,
            "objective": objective.strip(),
            "context_metadata": context_metadata,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class AutonomySecurityContext(BaseModel):
    """Server-side verified caller identity & authorization context (zero-trust)."""

    tenant_id: str = Field(..., min_length=1, max_length=128)
    user_id: str = Field(..., min_length=1, max_length=128)
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    correlation_id: str | None = Field(default=None, max_length=128)


class AutonomyPolicy(BaseModel):
    """Bounded autonomy constraints bounding steps, replans, retries, deadlines, and writes."""

    max_steps: int = Field(default=12, ge=1, le=100)
    max_replans: int = Field(default=2, ge=0, le=10)
    max_agent_attempts: int = Field(default=2, ge=1, le=5)
    deadline_seconds: int = Field(default=600, ge=1, le=3600)
    require_approval_for_writes: bool = True
    allowed_agents: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)


class AutonomousWorkflowRequest(BaseModel):
    """Client submission payload to initiate a goal-driven autonomous workflow."""

    objective: str = Field(min_length=1, max_length=4000)
    workflow_id: str = Field(default="autonomous_research", min_length=2, max_length=128)
    policy: AutonomyPolicy = Field(default_factory=AutonomyPolicy)
    context_metadata: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, max_length=128)
    mode: Literal["sync", "async"] = Field(default="sync")

    @field_validator("objective")
    @classmethod
    def normalize_objective(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Objective must not be blank.")
        return cleaned


class EvaluationResult(BaseModel):
    """Structured outcome from ProgressEvaluator checking objective & evidence sufficiency."""

    objective_satisfied: bool
    evidence_sufficient: bool
    should_replan: bool = False
    requires_human_review: bool = False
    reasons: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    missing_evidence: list[str] = Field(default_factory=list)


class PlannedStepSpec(BaseModel):
    """Candidate step produced by AutonomyPlannerAdapter (untrusted until PolicyGate approves)."""

    step_id: str = Field(default_factory=generate_autonomous_step_id)
    step_order: int = Field(default=1, ge=1)
    title: str = Field(..., min_length=1, max_length=256)
    description: str = Field(default="", max_length=2000)
    agent_id: str = Field(default="", max_length=128)
    tool_id: str | None = Field(default=None, max_length=128)
    required_capability: str = Field(default="knowledge.research", max_length=128)
    is_side_effecting: bool = Field(default=False)
    depends_on: list[str] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)


class AutonomousStepRecord(BaseModel):
    """Durable step execution record inside an autonomous workflow."""

    step_id: str = Field(default_factory=generate_autonomous_step_id)
    execution_id: str
    tenant_id: str
    plan_version: int = Field(default=1, ge=1)
    step_order: int = Field(default=1, ge=1)
    title: str
    agent_id: str
    tool_id: str | None = None
    required_capability: str = "knowledge.research"
    is_side_effecting: bool = False
    status: StepStatus = "pending"
    attempt: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=2, ge=1)
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class AutonomyDecisionRecord(BaseModel):
    """Explicit audit record of every controller transition or policy decision."""

    decision_id: str = Field(default_factory=generate_autonomy_decision_id)
    execution_id: str
    tenant_id: str
    action: DecisionAction
    reason: str
    evaluation_snapshot: dict[str, Any] = Field(default_factory=dict)
    remaining_steps: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AutonomyEventRecord(BaseModel):
    """Append-only operational event capturing lifecycle transitions, approvals, and errors."""

    event_id: str = Field(default_factory=generate_autonomy_event_id)
    execution_id: str
    tenant_id: str
    event_type: str
    actor_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AutonomyBudgetSnapshot(BaseModel):
    """Tracks bounded execution quotas and current consumption."""

    execution_id: str
    tenant_id: str
    max_steps: int = Field(..., ge=1)
    steps_consumed: int = Field(default=0, ge=0)
    max_replans: int = Field(..., ge=0)
    replans_consumed: int = Field(default=0, ge=0)
    max_agent_attempts: int = Field(..., ge=1)
    total_agent_attempts: int = Field(default=0, ge=0)
    deadline_seconds: int = Field(..., ge=1)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def remaining_steps(self) -> int:
        return max(0, self.max_steps - self.steps_consumed)

    @property
    def remaining_replans(self) -> int:
        return max(0, self.max_replans - self.replans_consumed)


class AutonomyFinalReport(BaseModel):
    """Structured outcome with traceable findings, citations, limitations, and stop rationale."""

    summary: str
    findings: list[dict[str, Any]] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    termination_reason: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class AutonomousWorkflowRecord(BaseModel):
    """Primary durable execution record for a Phase 4.9 autonomous workflow."""

    execution_id: str = Field(default_factory=generate_autonomous_execution_id)
    tenant_id: str
    requested_by: str
    workflow_id: str
    objective: str
    status: AutonomyStatus = "pending"
    policy: AutonomyPolicy = Field(default_factory=AutonomyPolicy)
    budget: AutonomyBudgetSnapshot | None = None
    current_plan: dict[str, Any] = Field(default_factory=dict)
    current_step_index: int = Field(default=0, ge=0)
    replan_count: int = Field(default=0, ge=0)
    termination_reason: str | None = None
    limitations: list[str] = Field(default_factory=list)
    final_result: dict[str, Any] = Field(default_factory=dict)
    checkpoint_ref: str | None = None
    idempotency_key: str | None = None
    idempotency_fingerprint: str | None = None
    deadline_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC) + timedelta(seconds=600)
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class CancelWorkflowRequest(BaseModel):
    """Payload to request cancellation of an active or paused autonomous workflow."""

    reason: str = Field(default="Cancelled by authenticated user", min_length=1, max_length=500)


class ResumeWorkflowRequest(BaseModel):
    """Payload to approve or resume a paused autonomous workflow."""

    approve: bool = True
    reason: str = Field(default="Approved and resumed by authorized user", min_length=1, max_length=500)


class AutonomyTimelineResponse(BaseModel):
    """Combined ordered view of controller decisions and lifecycle events."""

    execution_id: str
    decisions: list[AutonomyDecisionRecord] = Field(default_factory=list)
    events: list[AutonomyEventRecord] = Field(default_factory=list)


@runtime_checkable
class AutonomyPolicyInterface(Protocol):
    """Protocol implemented by AutonomyPolicyEngine (Member 3)."""

    def enforce_server_limits(
        self,
        requested: AutonomyPolicy,
        security_context: AutonomySecurityContext,
    ) -> AutonomyPolicy: ...

    def validate_plan(
        self,
        steps: list[PlannedStepSpec],
        policy: AutonomyPolicy,
        security_context: AutonomySecurityContext,
    ) -> tuple[bool, list[str]]: ...
