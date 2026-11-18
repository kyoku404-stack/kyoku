"""KEEP Phase 4.4 — Multi-Agent Planning & Reasoning SQLAlchemy ORM Models.

Stores plans (`agent_plans`), immutable plan revisions (`agent_plan_revisions`),
planned tasks with resolved agent versions (`agent_plan_tasks`), and plan lifecycle
audit events (`agent_plan_events`) separately from Phase 4.2 and Phase 4.3 execution rows.

Specification Reference: devdocs/p4/p4.4.txt (Section 10) & docs/Database/database-schema.md (Section 3.27)
Owner: Member 4 (FastAPI, Persistence & Integration Testing)
"""

from __future__ import annotations

from typing import Any

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class AgentPlan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Top-level durable multi-agent execution plan record scoped strictly by tenant."""

    __tablename__ = "agent_plans"
    __table_args__ = (
        Index("idx_agent_plans_tenant_status", "tenant_id", "status"),
        Index("idx_agent_plans_tenant_created", "tenant_id", "created_at"),
    )

    plan_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True, nullable=False)
    goal_text: Mapped[str] = mapped_column(Text, nullable=False)
    goal_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    input_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    execution_layers_json: Mapped[list[list[str]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    validation_findings_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    approval_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approval_reasons_json: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    clarification_questions_json: Mapped[list[str]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    policy_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    max_steps: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    max_replans: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    replan_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revision_reason: Mapped[str] = mapped_column(
        String(512), default="Initial plan generation", nullable=False
    )
    correlation_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    source_request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    workflow_execution_id: Mapped[str | None] = mapped_column(
        String(128), index=True, nullable=True
    )


class AgentPlanRevision(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Immutable historical snapshot of a plan version and its validation findings."""

    __tablename__ = "agent_plan_revisions"
    __table_args__ = (Index("idx_agent_plan_rev_plan_ver", "plan_id", "version"),)

    revision_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    plan_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    revision_reason: Mapped[str] = mapped_column(String(512), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    validation_findings_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )


class AgentPlanTask(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Persisted task node inside a specific plan version with resolved agent metadata."""

    __tablename__ = "agent_plan_tasks"
    __table_args__ = (Index("idx_agent_plan_tasks_plan_ver", "plan_id", "plan_version"),)

    plan_task_pk: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    plan_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    plan_version: Mapped[int] = mapped_column(Integer, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    required_capabilities_json: Mapped[list[str]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    depends_on_json: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    input_refs_json: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    output_key: Mapped[str] = mapped_column(String(128), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_evidence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_side_effecting: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    estimated_tokens: Mapped[int] = mapped_column(Integer, default=1500, nullable=False)
    parallel_group: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    resolved_agent_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resolved_agent_version: Mapped[str | None] = mapped_column(String(32), nullable=True)


class AgentPlanEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Append-only audit trail for plan creation, revision, validation, and submission."""

    __tablename__ = "agent_plan_events"
    __table_args__ = (Index("idx_agent_plan_events_plan_tenant", "plan_id", "tenant_id"),)

    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    plan_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
