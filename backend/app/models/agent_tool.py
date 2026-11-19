"""KEEP Phase 4.6 — Tool Calling Framework SQLAlchemy ORM Models.

Persists tool invocation records (`tool_invocations`) and security audit logs
(`tool_audit_logs`) linked to Phase 4.2 agent executions and Phase 4.3 workflows.

Specification Reference: devdocs/p4/p4.6.txt (Section 11) & docs/Database/database-schema.md (Section 3.29)
Owner: Member 4 (LangGraph Integration, API, Persistence & QA)
"""

from __future__ import annotations

import datetime
from typing import Any

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class ToolInvocationModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tracks every execution of an approved platform tool."""

    __tablename__ = "tool_invocations"
    __table_args__ = (
        Index("idx_tool_invocations_tenant_status", "tenant_id", "status"),
        Index("idx_tool_invocations_tenant_tool", "tenant_id", "tool_id"),
        Index(
            "idx_tool_invocations_idempotency",
            "tenant_id",
            "requested_by",
            "idempotency_key",
        ),
    )

    call_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    tool_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tool_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    agent_execution_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    workflow_execution_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="succeeded", index=True, nullable=False)
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    output_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ToolAuditLogModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Immutable audit trail for all tool invocation decisions and security outcomes."""

    __tablename__ = "tool_audit_logs"
    __table_args__ = (
        Index("idx_tool_audit_tenant_tool", "tenant_id", "tool_id"),
        Index("idx_tool_audit_tenant_decision", "tenant_id", "decision"),
    )

    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    call_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tool_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
