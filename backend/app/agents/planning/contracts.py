"""KEEP Phase 4.4 — Planning & Reasoning Engine Data Contracts & Protocols.

Defines `GoalSpec`, `PlannedTask`, `ExecutionPlan`, validation finding models,
immutable revision & event records, and protocol seams shared across Members 1–4
and the Phase 4.3 Orchestration Engine bridge.

Owner: Member 1 (Goal Understanding & Plan Generation)
Specification: devdocs/p4/p4.4.txt (Sections 3, 4, 8, 9, 10)
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal, Protocol, runtime_checkable
from uuid import uuid4

from backend.app.agents.contracts import AgentContext
from backend.app.agents.orchestration.workflow_contracts import WorkflowMode
from pydantic import BaseModel, Field, field_validator, model_validator

PlanStatusLiteral = Literal[
    "draft",
    "validated",
    "approval_required",
    "clarification_required",
    "rejected",
    "submitted",
]


class PlanStatus(str, Enum):
    """Canonical lifecycle statuses for a Phase 4.4 ExecutionPlan."""

    DRAFT = "draft"
    VALIDATED = "validated"
    APPROVAL_REQUIRED = "approval_required"
    CLARIFICATION_REQUIRED = "clarification_required"
    REJECTED = "rejected"
    SUBMITTED = "submitted"


class ValidationSeverity(str, Enum):
    """Severity levels for structured PlanValidator findings."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ValidationFinding(BaseModel):
    """Structured diagnostic emitted by KEEP's deterministic 9-point plan validation gate."""

    code: str = Field(..., min_length=2, max_length=128)
    check: str = Field(..., min_length=2, max_length=64)
    severity: ValidationSeverity = ValidationSeverity.ERROR
    message: str = Field(..., min_length=1, max_length=512)
    task_id: str | None = Field(default=None, max_length=64)
    details: dict[str, Any] = Field(default_factory=dict)


class GoalSpec(BaseModel):
    """Structured representation of a normalized natural-language user request."""

    goal: str = Field(..., min_length=1, max_length=4000)
    expected_output: str = Field(
        default="A structured, evidence-backed response.", min_length=1, max_length=1000
    )
    constraints: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    scope: str = Field(default="tenant_authorized_knowledge", max_length=256)
    requires_evidence: bool = Field(default=True)
    is_ambiguous: bool = Field(default=False)
    clarification_questions: list[str] = Field(default_factory=list)

    @field_validator("goal")
    @classmethod
    def strip_goal(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Goal cannot be empty or whitespace.")
        return cleaned


class PlannedTask(BaseModel):
    """Atomic executable task inside an ExecutionPlan, bound by capabilities rather than LLM guesses."""

    task_id: str = Field(..., min_length=2, max_length=64)
    description: str = Field(..., min_length=3, max_length=1000)
    required_capabilities: list[str] = Field(..., min_length=1)
    depends_on: list[str] = Field(default_factory=list)
    input_refs: list[str] = Field(default_factory=list)
    output_key: str = Field(..., min_length=2, max_length=128)
    required: bool = Field(default=True)
    requires_evidence: bool = Field(default=False)
    is_side_effecting: bool = Field(default=False)
    estimated_tokens: int = Field(default=1500, ge=0, le=50_000)
    estimated_duration_seconds: float = Field(default=10.0, gt=0.0, le=300.0)
    # Populated strictly by KEEP's CapabilityAgentSelector (Member 3) — NEVER trusted from LLM
    resolved_agent_id: str | None = Field(default=None, max_length=64)
    resolved_agent_version: str | None = Field(default=None, max_length=32)
    parallel_group: int = Field(default=0, ge=0)

    @field_validator("task_id", "output_key")
    @classmethod
    def normalize_identifier(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Identifier cannot be empty.")
        return cleaned


class ExecutionPlan(BaseModel):
    """Versioned, KEEP-validated execution plan ready for inspection, revision, or Phase 4.3 handoff."""

    plan_id: str = Field(default_factory=lambda: f"plan_{uuid4().hex[:16]}")
    version: int = Field(default=1, ge=1)
    goal: GoalSpec
    tasks: list[PlannedTask] = Field(default_factory=list, max_length=20)
    execution_layers: list[list[str]] = Field(default_factory=list)
    max_steps: int = Field(default=20, ge=1, le=20)
    max_replans: int = Field(default=2, ge=0, le=3)
    replan_count: int = Field(default=0, ge=0)
    status: PlanStatus = Field(default=PlanStatus.DRAFT)
    input: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str = Field(default="")
    requested_by: str = Field(default="")
    correlation_id: str = Field(default="")
    source_request_id: str | None = Field(default=None)
    policy_version: str = Field(default="1.0.0")
    validation_findings: list[ValidationFinding] = Field(default_factory=list)
    approval_required: bool = Field(default=False)
    approval_reasons: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    workflow_execution_id: str | None = Field(default=None)
    revision_reason: str = Field(default="Initial plan generation")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_structural_basics(self) -> ExecutionPlan:
        """Catches duplicate IDs, self-dependencies, and missing task references at contract boundary."""
        # Clarification-required plans may intentionally carry zero tasks
        if self.status == PlanStatus.CLARIFICATION_REQUIRED and not self.tasks:
            return self

        if len(self.tasks) > self.max_steps:
            raise ValueError(
                f"Plan contains {len(self.tasks)} tasks, exceeding max_steps={self.max_steps}."
            )

        seen_ids: set[str] = set()
        seen_outputs: set[str] = set()
        for task in self.tasks:
            if task.task_id in seen_ids:
                raise ValueError(f"Duplicate task_id detected in plan: '{task.task_id}'.")
            seen_ids.add(task.task_id)
            if task.output_key in seen_outputs:
                raise ValueError(f"Duplicate output_key detected in plan: '{task.output_key}'.")
            seen_outputs.add(task.output_key)

        for task in self.tasks:
            for dep in task.depends_on:
                if dep == task.task_id:
                    raise ValueError(f"Self-dependency detected on task '{task.task_id}'.")
                if dep not in seen_ids:
                    raise ValueError(
                        f"Task '{task.task_id}' depends on missing task_id '{dep}'."
                    )

        return self


class PlanCreateRequest(BaseModel):
    """Caller request to parse a complex goal, generate a task DAG, and validate it."""

    goal: str = Field(..., min_length=1, max_length=4000)
    expected_output: str | None = Field(default=None, max_length=1000)
    constraints: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    input: dict[str, Any] = Field(default_factory=dict)
    max_steps: int = Field(default=20, ge=1, le=20)
    max_replans: int = Field(default=2, ge=0, le=3)
    correlation_id: str | None = Field(default=None, max_length=128)


class PlanReviseRequest(BaseModel):
    """Caller request to revise an existing plan within its bounded replan budget."""

    reason: str = Field(..., min_length=3, max_length=512)
    updated_goal: str | None = Field(default=None, max_length=4000)
    expected_output: str | None = Field(default=None, max_length=1000)
    constraints: list[str] | None = Field(default=None)
    input_updates: dict[str, Any] = Field(default_factory=dict)


class PlanExecuteRequest(BaseModel):
    """Caller request to submit a validated plan to the Phase 4.3 Orchestration Engine."""

    mode: WorkflowMode = Field(default="sync")
    timeout_seconds: float | None = Field(default=None, gt=0.0, le=600.0)


class PlanRevisionSnapshot(BaseModel):
    """Immutable persisted snapshot of a specific plan version & its validation findings."""

    revision_id: str = Field(default_factory=lambda: f"planrev_{uuid4().hex[:16]}")
    plan_id: str
    version: int
    tenant_id: str
    status: PlanStatus
    revision_reason: str
    policy_version: str
    snapshot: dict[str, Any]
    validation_findings: list[ValidationFinding] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PlanEventRecord(BaseModel):
    """Append-only audit record for planning lifecycle & submission events."""

    event_id: str = Field(default_factory=lambda: f"planevt_{uuid4().hex[:16]}")
    plan_id: str
    tenant_id: str
    event_type: str
    actor_id: str
    correlation_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ============================================================================
# Protocol Seams (Members 1–4 & Phase 4.3 Bridge)
# ============================================================================


@runtime_checkable
class StructuredPlanLLMClient(Protocol):
    """Abstract structured LLM client allowing deterministic mocks and real providers."""

    async def propose_tasks(
        self,
        goal: GoalSpec,
        *,
        available_capabilities: list[str],
        feedback: str | None = None,
        attempt: int = 1,
    ) -> list[PlannedTask]: ...


@runtime_checkable
class PlanRepositoryInterface(Protocol):
    """Tenant-scoped durable persistence for plans, immutable revisions, tasks, and events."""

    async def save_plan(
        self,
        plan: ExecutionPlan,
        *,
        revision_reason: str,
    ) -> ExecutionPlan: ...

    async def get_plan(self, plan_id: str, tenant_id: str) -> ExecutionPlan | None: ...

    async def list_plans(
        self,
        tenant_id: str,
        *,
        status: PlanStatus | None = None,
        limit: int = 50,
    ) -> list[ExecutionPlan]: ...

    async def list_revisions(
        self, plan_id: str, tenant_id: str
    ) -> list[PlanRevisionSnapshot]: ...

    async def append_event(self, event: PlanEventRecord) -> None: ...

    async def list_events(self, plan_id: str, tenant_id: str) -> list[PlanEventRecord]: ...

    async def mark_submitted(
        self,
        plan_id: str,
        tenant_id: str,
        *,
        workflow_execution_id: str,
    ) -> ExecutionPlan: ...


@runtime_checkable
class PlanToWorkflowExecutorInterface(Protocol):
    """Seam submitting a validated ExecutionPlan into KEEP's Phase 4.3 Orchestration Engine."""

    async def execute_plan(
        self,
        plan: ExecutionPlan,
        context: AgentContext,
        *,
        mode: WorkflowMode = "sync",
        timeout_seconds: float | None = None,
    ) -> Any: ...
