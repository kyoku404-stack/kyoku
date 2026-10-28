"""KEEP Enterprise Platform — Real-Time Collaboration & Team Workspaces ORM Models.

Specification: devdocs/p3/p3.2.txt Section 3.19 & docs/database/database-schema.md
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
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Workspace(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Team workspace scoping departmental projects, documents, and discussions."""

    __tablename__ = "workspaces"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_workspace_org_slug"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_color: Mapped[str] = mapped_column(String(30), default="#4F46E5", nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    organization = relationship("Organization")
    created_by = relationship("User", foreign_keys=[created_by_id])
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    comments = relationship("DocumentComment", back_populates="workspace", cascade="all, delete-orphan")
    activities = relationship("CollaborationActivity", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMember(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Membership association and role for a user within a team workspace."""

    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(30), default="MEMBER", nullable=False)

    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User")


class DocumentComment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Threaded comments and replies anchored to enterprise knowledge documents."""

    __tablename__ = "document_comments"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    parent_comment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_comments.id", ondelete="CASCADE"), index=True, nullable=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    highlight_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="OPEN", nullable=False, index=True)
    resolved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mentions_json: Mapped[list[Any]] = mapped_column(JSONB, server_default="[]", nullable=False)

    workspace = relationship("Workspace", back_populates="comments")
    author = relationship("User", foreign_keys=[author_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    replies = relationship("DocumentComment", cascade="all, delete-orphan", foreign_keys=[parent_comment_id])


class DocumentVersionHistory(Base, UUIDPrimaryKeyMixin):
    """Immutable version checkpoint records maintaining complete document change logs."""

    __tablename__ = "document_version_history"
    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_doc_version"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    editor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    approval_status: Mapped[str] = mapped_column(String(30), default="APPROVED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    document = relationship("Document")
    editor = relationship("User")


class CollaborationActivity(Base, UUIDPrimaryKeyMixin):
    """Unified workspace activity feed timeline event record."""

    __tablename__ = "collaboration_activities"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=True
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    activity_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    entity_type: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    workspace = relationship("Workspace", back_populates="activities")
    actor = relationship("User")
