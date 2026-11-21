"""KEEP Phase 4.8 — Agent Collaboration SQLAlchemy ORM Models.

Persists multi-agent collaboration sessions, tasks, messages, findings,
peer review results, and conflict resolutions.

Specification: devdocs/p4/p4.8.txt & docs/Database/database-schema.md (Section 3.31)
Owner: Member 4 (Persistence, LangGraph Integration, FastAPI Endpoints & Full QA)
"""

from __future__ import annotations

import datetime
from typing import Any

from backend.app.db.base import Base, UUIDPrimaryKeyMixin
from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class CollaborationSessionModel(Base, UUIDPrimaryKeyMixin):
    """Master collaboration session record."""

    __tablename__ = "collaboration_sessions"
    __table_args__ = (
        Index("idx_collab_sessions_tenant_status", "tenant_id", "status"),
        Index("idx_collab_sessions_workflow", "tenant_id", "workflow_id"),
        Index("idx_collab_sessions_created_at", "tenant_id", "created_at"),
    )

    session_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(128), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="planning")
    workflow_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    max_agents: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    require_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_revisions: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    report: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class CollaborationTaskModel(Base, UUIDPrimaryKeyMixin):
    """Subtasks assigned to specific agents in a collaboration session."""

    __tablename__ = "collaboration_tasks"
    __table_args__ = (
        Index("idx_collab_tasks_session_status", "session_id", "status"),
        Index("idx_collab_tasks_tenant_agent", "tenant_id", "agent_id"),
    )

    task_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="pending")
    attempt: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    dependencies: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
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


class CollaborationMessageModel(Base, UUIDPrimaryKeyMixin):
    """Append-only inter-agent communication records."""

    __tablename__ = "collaboration_messages"
    __table_args__ = (
        Index("idx_collab_messages_session_created", "session_id", "created_at"),
        Index("idx_collab_messages_routing", "tenant_id", "sender_id", "recipient_id"),
    )

    message_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    sender_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    recipient_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    task_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    message_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )


class CollaborationFindingModel(Base, UUIDPrimaryKeyMixin):
    """Verifiable knowledge claims produced by agents."""

    __tablename__ = "collaboration_findings"
    __table_args__ = (
        Index("idx_collab_findings_session_task", "session_id", "task_id"),
        Index("idx_collab_findings_tenant_created", "tenant_id", "created_at"),
    )

    finding_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    task_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_refs: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )


class CollaborationReviewModel(Base, UUIDPrimaryKeyMixin):
    """Peer review evaluation records."""

    __tablename__ = "collaboration_reviews"
    __table_args__ = (
        Index("idx_collab_reviews_session_reviewer", "session_id", "reviewer_id"),
        Index("idx_collab_reviews_tenant_created", "tenant_id", "created_at"),
    )

    review_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    reviewer_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    finding_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    unsupported_claims: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    missing_evidence: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )


class CollaborationConflictModel(Base, UUIDPrimaryKeyMixin):
    """Contradiction and resolution records across findings."""

    __tablename__ = "collaboration_conflicts"
    __table_args__ = (
        Index("idx_collab_conflicts_session_status", "session_id", "status"),
        Index("idx_collab_conflicts_tenant_created", "tenant_id", "created_at"),
    )

    conflict_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    finding_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="detected")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    resolved_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
