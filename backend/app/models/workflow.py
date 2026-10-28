"""KEEP Enterprise Platform — Workflow Automation & Event-Driven Intelligence ORM Models.

Specification: devdocs/p3/p3.4.txt Section 3.21 & docs/database/database-schema.md
Author: Member 2 (Backend & Database Lead)
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from backend.app.db.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Workflow(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Core workflow definition governing trigger conditions and ordered DAG steps."""

    __tablename__ = "workflows"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(50), default="EVENT", nullable=False)
    event_pattern: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cron_expression: Mapped[str | None] = mapped_column(String(60), nullable=True)
    condition_rules: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    def __init__(self, **kwargs: Any) -> None:
        if "created_by_id" in kwargs:
            kwargs["created_by"] = kwargs.pop("created_by_id")
        super().__init__(**kwargs)

    @property
    def created_by_id(self) -> uuid.UUID | None:
        return self.created_by

    @created_by_id.setter
    def created_by_id(self, val: uuid.UUID | None) -> None:
        self.created_by = val

    steps = relationship(
        "WorkflowStep",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowStep.step_order",
    )
    executions = relationship(
        "WorkflowExecution",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )


class WorkflowStep(Base, UUIDPrimaryKeyMixin):
    """Ordered executable DAG action step comprising a workflow."""

    __tablename__ = "workflow_steps"
    __table_args__ = (
        UniqueConstraint("workflow_id", "step_order", name="uq_workflow_step_order"),
    )

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"), index=True, nullable=False
    )
    step_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    action_type: Mapped[str] = mapped_column(String(60), nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)

    def __init__(self, **kwargs: Any) -> None:
        if "action_config" in kwargs:
            kwargs["configuration"] = kwargs.pop("action_config")
        name_val = kwargs.pop("name", None)
        if name_val and "configuration" in kwargs and isinstance(kwargs["configuration"], dict):
            kwargs["configuration"].setdefault("name", name_val)
        super().__init__(**kwargs)

    @property
    def action_config(self) -> dict[str, Any]:
        return self.configuration

    @action_config.setter
    def action_config(self, val: dict[str, Any]) -> None:
        self.configuration = val
    depends_on_step_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workflow_steps.id", ondelete="SET NULL"), nullable=True
    )
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    workflow = relationship("Workflow", back_populates="steps")


class WorkflowExecution(Base, UUIDPrimaryKeyMixin):
    """Historical execution run of a workflow triggered by event, schedule, or manual run."""

    __tablename__ = "workflow_executions"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"), index=True, nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    triggered_by_event_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="RUNNING", index=True, nullable=False)
    current_step_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    input_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)
    output_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workflow = relationship("Workflow", back_populates="executions")
    step_runs = relationship(
        "WorkflowExecutionStep",
        back_populates="execution",
        cascade="all, delete-orphan",
    )


class WorkflowExecutionStep(Base, UUIDPrimaryKeyMixin):
    """Detailed telemetry and I/O payload per step execution in a run."""

    __tablename__ = "workflow_execution_steps"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_executions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    step_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_steps.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(40), default="PENDING", nullable=False)
    input_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)
    output_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    execution = relationship("WorkflowExecution", back_populates="step_runs")
    step = relationship("WorkflowStep")


class WorkflowApproval(Base, UUIDPrimaryKeyMixin):
    """Human-in-the-loop review tickets gating sensitive workflow operations."""

    __tablename__ = "workflow_approvals"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_executions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    step_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workflow_steps.id", ondelete="SET NULL"), nullable=True
    )
    requester_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approver_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    approver_role: Mapped[str] = mapped_column(String(50), default="OrgAdmin", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True, nullable=False)
    decision_comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    execution = relationship("WorkflowExecution")


from backend.app.models.notification import Notification  # noqa: F401


class NotificationPreference(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Granular user opt-in/opt-out preferences per delivery channel and category."""

    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "channel", "category", name="uq_user_channel_category"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WorkflowTemplate(Base):
    """Pre-configured reusable enterprise automation patterns."""

    __tablename__ = "workflow_templates"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), default="EVENT", nullable=False)
    event_pattern: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cron_expression: Mapped[str | None] = mapped_column(String(60), nullable=True)
    steps_definition: Mapped[list[Any]] = mapped_column(JSONB, default=list, server_default="[]", nullable=False)
    is_system_template: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
