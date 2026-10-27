import uuid
from datetime import datetime
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
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class AssistantWorkflow(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tracks multi-step agentic workflow execution states, DAG progress, and context."""

    __tablename__ = "assistant_workflows"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="SET NULL"), index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), default="CHAT", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True, nullable=False)
    current_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    context_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, server_default="{}", nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization")
    user = relationship("User", foreign_keys=[user_id])
    session = relationship("ChatSession")
    tasks = relationship(
        "AssistantTask",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="AssistantTask.step_number",
    )
    approvals = relationship(
        "AssistantApproval",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )


class AssistantTask(Base, UUIDPrimaryKeyMixin):
    """Tracks atomic DAG step nodes within an assistant workflow."""

    __tablename__ = "assistant_tasks"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assistant_workflows.id", ondelete="CASCADE"), index=True, nullable=False
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    input_parameters_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, server_default="{}", nullable=True
    )
    output_result_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, server_default="{}", nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approval_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    execution_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    organization = relationship("Organization")
    workflow = relationship("AssistantWorkflow", back_populates="tasks")


class AssistantApproval(Base, UUIDPrimaryKeyMixin):
    """Captures human-in-the-loop review requests for sensitive or destructive operations."""

    __tablename__ = "assistant_approvals"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assistant_workflows.id", ondelete="CASCADE"), index=True, nullable=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assistant_tasks.id", ondelete="CASCADE"), index=True, nullable=True
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, server_default="{}", nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True, nullable=False)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    organization = relationship("Organization")
    user = relationship("User", foreign_keys=[user_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    workflow = relationship("AssistantWorkflow", back_populates="approvals")
    task = relationship("AssistantTask")


class AssistantReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stores generated structured multi-format reports and executive briefings."""

    __tablename__ = "assistant_reports"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    report_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str] = mapped_column(String(50), default="MARKDOWN", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, server_default="{}", nullable=True
    )

    organization = relationship("Organization")
    user = relationship("User")
