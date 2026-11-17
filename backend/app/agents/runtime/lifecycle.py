"""KEEP Phase 4.2 — Agent Execution Lifecycle State Machine & Domain DTOs.

Defines canonical persistent execution statuses, strict transition validation,
immutable terminal state invariants, and the `ExecutionRecord` domain model.

Owner: Member 1 (Runtime Architecture & Execution Lifecycle)
Specification: devdocs/p4/p4.2.txt (Sections 3, 4, 6)
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from backend.app.agents.errors import InvalidExecutionTransitionError
from pydantic import BaseModel, Field

ExecutionMode = Literal["sync", "async"]


def generate_execution_id() -> str:
    """Generates a globally unique, traceable KEEP execution identifier."""
    return f"exec_{uuid4().hex}"


class ExecutionStatus(str, Enum):
    """Canonical lifecycle states for every KEEP agent execution attempt."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"


TERMINAL_STATUSES: frozenset[ExecutionStatus] = frozenset(
    {
        ExecutionStatus.SUCCEEDED,
        ExecutionStatus.FAILED,
        ExecutionStatus.TIMED_OUT,
        ExecutionStatus.CANCELLED,
    }
)

ACTIVE_STATUSES: frozenset[ExecutionStatus] = frozenset(
    {
        ExecutionStatus.PENDING,
        ExecutionStatus.RUNNING,
    }
)

ALLOWED_TRANSITIONS: dict[ExecutionStatus, frozenset[ExecutionStatus]] = {
    ExecutionStatus.PENDING: frozenset(
        {
            ExecutionStatus.RUNNING,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.FAILED,
        }
    ),
    ExecutionStatus.RUNNING: frozenset(
        {
            ExecutionStatus.SUCCEEDED,
            ExecutionStatus.FAILED,
            ExecutionStatus.TIMED_OUT,
            ExecutionStatus.CANCELLED,
        }
    ),
    ExecutionStatus.SUCCEEDED: frozenset(),
    ExecutionStatus.FAILED: frozenset(),
    ExecutionStatus.TIMED_OUT: frozenset(),
    ExecutionStatus.CANCELLED: frozenset(),
}


def is_terminal_status(status: ExecutionStatus | str) -> bool:
    """Returns True if `status` is an immutable terminal execution state."""
    enum_status = status if isinstance(status, ExecutionStatus) else ExecutionStatus(str(status).upper())
    return enum_status in TERMINAL_STATUSES


def can_transition(current: ExecutionStatus | str, target: ExecutionStatus | str) -> bool:
    """Returns True if transitioning from `current` to `target` is valid."""
    curr = current if isinstance(current, ExecutionStatus) else ExecutionStatus(str(current).upper())
    nxt = target if isinstance(target, ExecutionStatus) else ExecutionStatus(str(target).upper())
    return nxt in ALLOWED_TRANSITIONS[curr]


def assert_valid_transition(
    execution_id: str,
    current: ExecutionStatus | str,
    target: ExecutionStatus | str,
) -> None:
    """Raises InvalidExecutionTransitionError if `current -> target` violates the state machine."""
    curr = current if isinstance(current, ExecutionStatus) else ExecutionStatus(str(current).upper())
    nxt = target if isinstance(target, ExecutionStatus) else ExecutionStatus(str(target).upper())
    if nxt not in ALLOWED_TRANSITIONS[curr]:
        raise InvalidExecutionTransitionError(execution_id, curr.value, nxt.value)


class ExecutionRecord(BaseModel):
    """Canonical KEEP execution record shared across runtime, persistence, and API layers."""

    execution_id: str = Field(default_factory=generate_execution_id)
    task_id: str
    agent_id: str
    agent_version: str
    tenant_id: str
    requested_by: str
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)
    mode: ExecutionMode = Field(default="sync")
    goal: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    input_ref: str | None = None
    result_payload: dict[str, Any] | None = None
    result_ref: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    correlation_id: str
    attempt_number: int = Field(default=1, ge=1)
    parent_execution_id: str | None = None
    idempotency_key: str | None = None
    request_fingerprint: str | None = None
    cancel_requested: bool = False
    cancel_requested_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    deadline_at: datetime | None = None
    duration_ms: int | None = None
    queue_wait_ms: int | None = None
    checkpoint_thread_id: str | None = None

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    @property
    def status_url(self) -> str:
        return f"/api/v1/executions/{self.execution_id}"

    @property
    def result_url(self) -> str:
        return f"/api/v1/executions/{self.execution_id}/result"
