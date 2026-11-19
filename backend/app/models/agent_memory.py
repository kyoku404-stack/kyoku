"""KEEP Phase 4.7 — Agent Memory System SQLAlchemy ORM Models.

Persists canonical active memories (`memories`), candidate proposals (`memory_proposals`),
historical version snapshots (`memory_versions`), and audit events (`memory_access_events`).

Specification Reference: devdocs/p4/p4.7.txt (Sections 4, 11) & docs/Database/database-schema.md (Section 3.30)
Owner: Member 4 (LangGraph Integration, API, Persistence & QA)
"""

from __future__ import annotations

import datetime
from typing import Any

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class MemoryModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Canonical active or historical agent memory record."""

    __tablename__ = "memories"
    __table_args__ = (
        Index("idx_memories_tenant_scope", "tenant_id", "scope"),
        Index("idx_memories_tenant_owner", "tenant_id", "owner_id"),
        Index("idx_memories_tenant_status", "tenant_id", "status"),
        Index("idx_memories_content_hash", "tenant_id", "content_hash"),
        Index("idx_memories_expires_at", "expires_at"),
    )

    memory_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    scope: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    owner_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    memory_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False, default="preference")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), default="user_input", nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    superseded_by: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    meta_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    expires_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MemoryProposalModel(Base, UUIDPrimaryKeyMixin):
    """Candidate memory proposal submitted by an agent or user awaiting review."""

    __tablename__ = "memory_proposals"
    __table_args__ = (
        Index("idx_memory_proposals_tenant_status", "tenant_id", "status"),
        Index("idx_memory_proposals_tenant_owner", "tenant_id", "owner_id"),
    )

    proposal_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    scope: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    owner_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    proposer_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    proposer_type: Mapped[str] = mapped_column(String(32), default="agent", nullable=False)
    memory_type: Mapped[str] = mapped_column(String(64), default="preference", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True, nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)
    approved_memory_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    meta_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
    reviewed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MemoryVersionModel(Base, UUIDPrimaryKeyMixin):
    """Historical snapshot preserving version lineage and superseding reason."""

    __tablename__ = "memory_versions"
    __table_args__ = (
        Index("idx_memory_versions_memory_version", "memory_id", "version"),
        Index("idx_memory_versions_tenant_memory", "tenant_id", "memory_id"),
    )

    memory_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )


class MemoryAccessEventModel(Base, UUIDPrimaryKeyMixin):
    """Append-only audit trail capturing retrieval, proposal, approval, and deletion events."""

    __tablename__ = "memory_access_events"
    __table_args__ = (
        Index("idx_memory_access_events_tenant_time", "tenant_id", "created_at"),
        Index("idx_memory_access_events_tenant_memory", "tenant_id", "memory_id"),
        Index("idx_memory_access_events_tenant_action", "tenant_id", "action"),
    )

    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    memory_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    scope: Mapped[str | None] = mapped_column(String(32), nullable=True)
    allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    denial_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    query_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
