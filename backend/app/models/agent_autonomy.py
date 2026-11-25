"""KEEP Phase 4.9 — Autonomous Workflow Engine SQLAlchemy ORM Models.

Persists autonomous workflow state, step execution attempts, controller
decisions, audit events, and resource budgets.

Specification: devdocs/p4/p4.9.txt (Section 7) & docs/Database/database-schema.md (Section 3.32)
Owner: Member 2 (Schemas, Persistence, Migrations & Adaptive Planning)
"""

from __future__ import annotations

import datetime
from typing import Any

from backend.app.db.base import Base, UUIDPrimaryKeyMixin
from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class AutonomousWorkflowModel(Base, UUIDPrimaryKeyMixin):
    """Master durable record for a Phase 4.9 autonomous workflow execution."""

    __tablename__ = "autonomous_workflows"
    __table_args__ = (
        Index("idx_auto_wf_tenant_status", "tenant_id", "status"),
        Index("idx_auto_wf_tenant_created", "tenant_id", "created_at"),
        Index("idx_auto_wf_idempotency", "tenant_id", "requested_by", "idempotency_key"),
    )

    execution_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    workflow_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="pending")
    policy_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    current_plan: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    current_step_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    replan_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    termination_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    final_result: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    checkpoint_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    idempotency_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    deadline_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=600),
        nullable=False,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class AutonomousWorkflowStepModel(Base, UUIDPrimaryKeyMixin):
    """Tracks planned steps, agent bindings, attempt counts, and outputs."""

    __tablename__ = "autonomous_workflow_steps"
    __table_args__ = (
        Index("idx_auto_steps_exec_order", "execution_id", "plan_version", "step_order"),
        Index("idx_auto_steps_tenant_status", "tenant_id", "status"),
    )

    step_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    execution_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    plan_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tool_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    required_capability: Mapped[str] = mapped_column(
        String(128), default="knowledge.research", nullable=False
    )
    is_side_effecting: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="pending")
    attempt: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    inputs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    outputs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class AutonomyDecisionModel(Base, UUIDPrimaryKeyMixin):
    """Audit trail of controller decisions (continue, replan, pause, stop)."""

    __tablename__ = "autonomy_decisions"
    __table_args__ = (Index("idx_auto_decisions_exec_created", "execution_id", "created_at"),)

    decision_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    execution_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evaluation_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    remaining_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )


class AutonomyEventModel(Base, UUIDPrimaryKeyMixin):
    """Append-only operational event log for autonomous workflows."""

    __tablename__ = "autonomy_events"
    __table_args__ = (Index("idx_auto_events_exec_created", "execution_id", "created_at"),)

    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    execution_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )


class AutonomyBudgetModel(Base, UUIDPrimaryKeyMixin):
    """Tracks resource limits and real-time budget consumption per autonomous workflow."""

    __tablename__ = "autonomy_budgets"

    execution_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    max_steps: Mapped[int] = mapped_column(Integer, nullable=False)
    steps_consumed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_replans: Mapped[int] = mapped_column(Integer, nullable=False)
    replans_consumed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_agent_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    total_agent_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deadline_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
