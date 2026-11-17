"""KEEP Phase 4.3 — Durable Multi-Agent Workflow Execution & Step Linkage ORM Models.

Specification Reference: devdocs/p4/p4.3.txt (Section 8) & docs/Database/database-schema.md (Section 3.26)
Owner: Member 4 (FastAPI Integration, Persistence & End-to-End QA)
"""

from __future__ import annotations

from datetime import datetime
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


class AgentWorkflowExecution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Durable KEEP business-level record for an orchestrated multi-agent workflow run."""

    __tablename__ = "agent_workflow_executions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "requested_by",
            "idempotency_key",
            name="uq_agent_wf_exec_idempotency",
        ),
        Index("idx_agent_wf_exec_tenant_status", "tenant_id", "status"),
        Index("idx_agent_wf_exec_tenant_created", "tenant_id", "created_at"),
    )

    workflow_execution_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    workflow_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    workflow_version: Mapped[str] = mapped_column(String(32), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True, nullable=False)
    mode: Mapped[str] = mapped_column(String(16), default="async", nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    input_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    result_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)
    warnings_json: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    checkpoint_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class AgentWorkflowStep(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Links a workflow graph node invocation to its Phase 4.2 agent_executions record."""

    __tablename__ = "agent_workflow_steps"
    __table_args__ = (Index("idx_agent_wf_step_exec_tenant", "workflow_execution_id", "tenant_id"),)

    step_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    workflow_execution_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    node_name: Mapped[str] = mapped_column(String(128), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_execution_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="required", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="SUCCEEDED", nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_side_effecting: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
