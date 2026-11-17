"""KEEP Phase 4.2 — Runtime Execution Context & Deadline Propagation.

Wraps Phase 4.1's trusted `AgentContext` with runtime-specific execution metadata
(`execution_id`, `attempt_number`, `deadline_at`, remaining budget) while preserving
strict zero-trust identity guarantees.

Owner: Member 1 (Runtime Architecture & Execution Lifecycle)
Specification: devdocs/p4/p4.2.txt (Sections 3, 5, 9)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from backend.app.agents.contracts import AgentContext
from pydantic import BaseModel, Field


class RuntimeExecutionContext(BaseModel):
    """Execution-scoped envelope wrapping a trusted Phase 4.1 AgentContext."""

    execution_id: str
    attempt_number: int = Field(default=1, ge=1)
    agent_context: AgentContext
    timeout_seconds: float = Field(default=30.0, gt=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deadline_at: datetime

    @property
    def tenant_id(self) -> str:
        return self.agent_context.tenant_id

    @property
    def user_id(self) -> str:
        return self.agent_context.user_id

    @property
    def correlation_id(self) -> str:
        return self.agent_context.correlation_id

    def remaining_seconds(self, *, now: datetime | None = None) -> float:
        """Computes remaining wall-clock budget before the execution deadline."""
        ref = now or datetime.now(UTC)
        delta = (self.deadline_at - ref).total_seconds()
        return max(0.0, delta)

    def is_expired(self, *, now: datetime | None = None) -> bool:
        """Returns True if the execution deadline has already elapsed."""
        return self.remaining_seconds(now=now) <= 0.0


def build_runtime_context(
    *,
    execution_id: str,
    agent_context: AgentContext,
    timeout_seconds: float,
    attempt_number: int = 1,
) -> RuntimeExecutionContext:
    """Constructs a deadline-bound RuntimeExecutionContext from a trusted AgentContext."""
    now = datetime.now(UTC)
    effective_context = agent_context.model_copy(
        update={"deadline_seconds": max(1, int(timeout_seconds))}
    )
    return RuntimeExecutionContext(
        execution_id=execution_id,
        attempt_number=attempt_number,
        agent_context=effective_context,
        timeout_seconds=timeout_seconds,
        created_at=now,
        deadline_at=now + timedelta(seconds=timeout_seconds),
    )
