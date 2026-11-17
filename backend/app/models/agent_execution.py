"""KEEP Phase 4.2 — Durable Agent Execution & Checkpoint SQLAlchemy ORM Models.

Specification Reference: devdocs/p4/p4.2.txt (Sections 6, 8) & docs/database/database-schema.md (Section 3.25)
Owner: Member 2 (Execution State, Persistence & Result Management)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class AgentExecution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Durable business-level execution record for a KEEP agent invocation attempt."""

    __tablename__ = "agent_executions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "requested_by",
            "idempotency_key",
            name="uq_agent_exec_idempotency",
        ),
        Index("idx_agent_exec_tenant_status", "tenant_id", "status"),
        Index("idx_agent_exec_tenant_created", "tenant_id", "created_at"),
    )

    execution_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    task_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    agent_version: Mapped[str] = mapped_column(String(32), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True, nullable=False)
    mode: Mapped[str] = mapped_column(String(16), default="sync", nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    input_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    input_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    result_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    parent_execution_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancel_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=True,
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    queue_wait_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checkpoint_thread_id: Mapped[str | None] = mapped_column(String(128), nullable=True)


class AgentCheckpoint(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Scoped LangGraph state snapshot separate from KEEP business authorization records."""

    __tablename__ = "agent_checkpoints"
    __table_args__ = (
        Index("idx_agent_chk_exec_step", "execution_id", "step_number"),
        Index("idx_agent_chk_tenant_thread", "tenant_id", "thread_id"),
    )

    checkpoint_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    execution_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    thread_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    step_name: Mapped[str] = mapped_column(String(128), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    state_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
