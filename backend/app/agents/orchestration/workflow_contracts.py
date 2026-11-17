"""KEEP Phase 4.3 — Multi-Agent Workflow Contracts, Lifecycle & Interfaces.

Defines KEEP-owned workflow schemas, explicit lifecycle state transitions,
step-to-execution linkage records, and protocol seams for Member 2 (Graph State/Nodes),
Member 3 (Reliability/Policies/Recovery), Member 4 (Persistence/API/Observability),
and Phase 4.4 (Planning & Reasoning Engine).

Owner: Member 1 (Orchestration Architecture & Workflow Registry)
Specification: devdocs/p4/p4.3.txt (Sections 3, 4, 8, 9, 11)
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal, Protocol, runtime_checkable
from uuid import uuid4

from backend.app.agents.contracts import AgentContext, EvidenceReference
from backend.app.agents.errors import sanitize_error_message
from pydantic import BaseModel, Field, field_validator

_WORKFLOW_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")
_SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?$")

WorkflowMode = Literal["sync", "async"]
WorkflowStepRole = Literal["required", "optional"]


class WorkflowStatus(str, Enum):
    """Canonical lifecycle states for a Phase 4.3 multi-agent workflow execution."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    PARTIALLY_SUCCEEDED = "PARTIALLY_SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


TERMINAL_WORKFLOW_STATUSES: frozenset[WorkflowStatus] = frozenset(
    {
        WorkflowStatus.SUCCEEDED,
        WorkflowStatus.PARTIALLY_SUCCEEDED,
        WorkflowStatus.FAILED,
        WorkflowStatus.CANCELLED,
        WorkflowStatus.TIMED_OUT,
    }
)

RECOVERABLE_WORKFLOW_STATUSES: frozenset[WorkflowStatus] = frozenset(
    {
        WorkflowStatus.RUNNING,
        WorkflowStatus.FAILED,
        WorkflowStatus.TIMED_OUT,
    }
)

ALLOWED_WORKFLOW_TRANSITIONS: dict[WorkflowStatus, frozenset[WorkflowStatus]] = {
    WorkflowStatus.PENDING: frozenset(
        {
            WorkflowStatus.RUNNING,
            WorkflowStatus.CANCELLED,
            WorkflowStatus.FAILED,
        }
    ),
    WorkflowStatus.RUNNING: frozenset(
        {
            WorkflowStatus.SUCCEEDED,
            WorkflowStatus.PARTIALLY_SUCCEEDED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
            WorkflowStatus.TIMED_OUT,
        }
    ),
    WorkflowStatus.SUCCEEDED: frozenset(),
    WorkflowStatus.PARTIALLY_SUCCEEDED: frozenset(),
    WorkflowStatus.FAILED: frozenset({WorkflowStatus.RUNNING}),  # explicit checkpoint resume only
    WorkflowStatus.CANCELLED: frozenset(),
    WorkflowStatus.TIMED_OUT: frozenset({WorkflowStatus.RUNNING}),  # explicit checkpoint resume only
}


def is_valid_workflow_transition(
    current: WorkflowStatus,
    target: WorkflowStatus,
) -> bool:
    """Returns True iff transitioning a workflow execution from `current` to `target` is allowed."""
    return target in ALLOWED_WORKFLOW_TRANSITIONS.get(current, frozenset())


def compute_workflow_fingerprint(
    workflow_id: str,
    version: str,
    goal: str,
    input_data: dict[str, Any],
) -> str:
    """Computes a deterministic SHA-256 fingerprint for scoped workflow idempotency verification."""
    canonical = json.dumps(
        {
            "workflow_id": workflow_id,
            "version": version,
            "goal": goal,
            "input": input_data,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class WorkflowDefinition(BaseModel):
    """Versioned metadata describing an approved multi-agent workflow in KEEP."""

    workflow_id: str = Field(..., min_length=2, max_length=64)
    name: str = Field(..., min_length=2, max_length=128)
    version: str = Field(..., min_length=5, max_length=32)
    description: str = Field(default="", max_length=1024)
    task_type: str = Field(default="general", min_length=1, max_length=64)
    required_capabilities: list[str] = Field(default_factory=list)
    required_agents: list[str] = Field(default_factory=list)
    optional_agents: list[str] = Field(default_factory=list)
    allow_partial_success: bool = Field(default=False)
    enabled: bool = Field(default=True)
    input_schema_version: str = Field(default="1.0", max_length=16)
    output_schema_version: str = Field(default="1.0", max_length=16)
    default_timeout_seconds: float = Field(default=120.0, gt=0.0, le=3600.0)
    max_timeout_seconds: float = Field(default=600.0, gt=0.0, le=3600.0)
    max_agent_invocations: int = Field(default=12, ge=1, le=100)
    tags: list[str] = Field(default_factory=list)

    @field_validator("workflow_id")
    @classmethod
    def validate_workflow_id(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _WORKFLOW_ID_PATTERN.match(normalized):
            raise ValueError(
                "workflow_id must be 2-64 lowercase alphanumeric characters, dots, underscores, or hyphens."
            )
        return normalized

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        normalized = value.strip()
        if not _SEMVER_PATTERN.match(normalized):
            raise ValueError("version must follow semantic versioning (e.g. '1.0.0').")
        return normalized


class WorkflowRequest(BaseModel):
    """Caller request to execute an approved multi-agent workflow."""

    goal: str = Field(..., min_length=1, max_length=4096)
    input: dict[str, Any] = Field(default_factory=dict)
    version: str | None = Field(default=None, max_length=32)
    mode: WorkflowMode = Field(default="async")
    timeout_seconds: float | None = Field(default=None, gt=0.0)
    idempotency_key: str | None = Field(default=None, max_length=128)
    correlation_id: str | None = Field(default=None, max_length=128)


class WorkflowStepLink(BaseModel):
    """Links a single graph node invocation to its durable Phase 4.2 agent execution record."""

    step_id: str = Field(default_factory=lambda: f"wfstep_{uuid4().hex[:16]}")
    workflow_execution_id: str
    tenant_id: str
    node_name: str
    agent_id: str
    agent_execution_id: str
    role: WorkflowStepRole = "required"
    status: str = "SUCCEEDED"
    attempt_number: int = 1
    duration_ms: int | None = None
    error_code: str | None = None
    is_side_effecting: bool = False
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class WorkflowResult(BaseModel):
    """Validated final or permitted partial result produced by a multi-agent workflow."""

    workflow_execution_id: str
    workflow_id: str
    workflow_version: str
    status: str
    output: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    execution_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    failed_optional_steps: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    schema_version: str = Field(default="1.0")

    @field_validator("error_message")
    @classmethod
    def sanitize_message(cls, value: str | None) -> str | None:
        return sanitize_error_message(value) if value else value


class WorkflowExecutionRecord(BaseModel):
    """Durable KEEP business-level record for an entire multi-agent workflow run."""

    workflow_execution_id: str = Field(default_factory=lambda: f"wfexec_{uuid4().hex[:16]}")
    workflow_id: str
    workflow_version: str
    tenant_id: str
    requested_by: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    mode: WorkflowMode = "async"
    goal: str
    input: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str
    idempotency_key: str | None = None
    request_fingerprint: str | None = None
    execution_ids: list[str] = Field(default_factory=list)
    steps: list[WorkflowStepLink] = Field(default_factory=list)
    result: WorkflowResult | None = None
    result_ref: str | None = None
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    checkpoint_ref: str | None = None
    cancel_requested: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    deadline_at: datetime | None = None
    duration_ms: int | None = None

    @property
    def status_url(self) -> str:
        return f"/api/v1/workflow-executions/{self.workflow_execution_id}"

    @property
    def result_url(self) -> str:
        return f"/api/v1/workflow-executions/{self.workflow_execution_id}/result"

    @property
    def steps_url(self) -> str:
        return f"/api/v1/workflow-executions/{self.workflow_execution_id}/steps"


# ============================================================================
# Protocol Seams (Members 2, 3, 4 & Phase 4.4 Planner Extension Points)
# ============================================================================


@runtime_checkable
class WorkflowGraphRunner(Protocol):
    """Compiled multi-agent graph runnable invoked by KeepOrchestrationService."""

    async def arun(
        self,
        initial_state: dict[str, Any],
        *,
        context: AgentContext,
        resume_from_node: str | None = None,
        completed_nodes: set[str] | None = None,
        checkpoint_callback: Any | None = None,
        cancel_checker: Callable[[], bool] | None = None,
    ) -> dict[str, Any]:
        ...


WorkflowGraphFactory = Callable[..., WorkflowGraphRunner]


@runtime_checkable
class WorkflowRepositoryInterface(Protocol):
    """Durable persistence boundary for workflow executions and linked agent steps."""

    async def create(self, record: WorkflowExecutionRecord) -> WorkflowExecutionRecord: ...

    async def get(
        self, workflow_execution_id: str, tenant_id: str
    ) -> WorkflowExecutionRecord | None: ...

    async def get_by_idempotency_key(
        self, tenant_id: str, requested_by: str, idempotency_key: str
    ) -> WorkflowExecutionRecord | None: ...

    async def list_executions(
        self,
        tenant_id: str,
        *,
        workflow_id: str | None = None,
        status: WorkflowStatus | None = None,
        limit: int = 50,
    ) -> list[WorkflowExecutionRecord]: ...

    async def mark_running(
        self,
        workflow_execution_id: str,
        tenant_id: str,
        *,
        started_at: datetime,
        deadline_at: datetime | None = None,
        allow_from_recoverable: bool = False,
    ) -> WorkflowExecutionRecord: ...

    async def append_step(
        self,
        workflow_execution_id: str,
        tenant_id: str,
        step: WorkflowStepLink,
    ) -> None: ...

    async def update_checkpoint_ref(
        self,
        workflow_execution_id: str,
        tenant_id: str,
        checkpoint_ref: str,
    ) -> None: ...

    async def mark_completed(
        self,
        workflow_execution_id: str,
        tenant_id: str,
        *,
        status: WorkflowStatus,
        result: WorkflowResult | None,
        completed_at: datetime,
        duration_ms: int,
        error_code: str | None = None,
        error_message: str | None = None,
        warnings: list[str] | None = None,
    ) -> WorkflowExecutionRecord: ...

    async def request_cancel(
        self,
        workflow_execution_id: str,
        tenant_id: str,
        *,
        cancelled_at: datetime,
    ) -> WorkflowExecutionRecord: ...

    async def list_steps(
        self, workflow_execution_id: str, tenant_id: str
    ) -> list[WorkflowStepLink]: ...

    async def list_stale_running(self, now: datetime) -> list[WorkflowExecutionRecord]: ...


@runtime_checkable
class WorkflowObserverInterface(Protocol):
    """Structured workflow-level tracing & metrics sink."""

    def record_event(
        self,
        event_type: str,
        *,
        record: WorkflowExecutionRecord,
        details: dict[str, Any] | None = None,
    ) -> None: ...

    def record_step(self, step: WorkflowStepLink, *, correlation_id: str) -> None: ...


@runtime_checkable
class WorkflowBackgroundDispatcher(Protocol):
    """Async background dispatcher for non-blocking workflow executions."""

    async def enqueue(
        self, workflow_execution_id: str, request: Any, context: AgentContext
    ) -> None: ...
