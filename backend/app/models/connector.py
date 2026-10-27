"""KEEP Enterprise Platform — Connector Framework & Enterprise Integrations ORM Models.

Specification: devdocs/p3/p3.1.txt Section 3.18 & docs/database/database-schema.md
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
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Connector(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stores enterprise SaaS connector instances, auth methods, and sync status."""

    __tablename__ = "connectors"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    platform_category: Mapped[str] = mapped_column(String(50), nullable=False)
    auth_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="CONFIGURED", nullable=False, index=True)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    encrypted_credentials: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    total_documents_synced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization = relationship("Organization")
    sync_jobs = relationship("ConnectorSyncJob", back_populates="connector", cascade="all, delete-orphan")
    sync_logs = relationship("ConnectorSyncLog", back_populates="connector", cascade="all, delete-orphan")


class ConnectorSyncJob(Base, UUIDPrimaryKeyMixin):
    """Tracks asynchronous full and incremental synchronization batches."""

    __tablename__ = "connector_sync_jobs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    connector_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("connectors.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sync_mode: Mapped[str] = mapped_column(String(30), default="INCREMENTAL", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False, index=True)
    trigger_type: Mapped[str] = mapped_column(String(30), default="MANUAL", nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    documents_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    documents_added: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    documents_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    documents_deleted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    documents_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    documents_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    organization = relationship("Organization")
    connector = relationship("Connector", back_populates="sync_jobs")
    logs = relationship("ConnectorSyncLog", back_populates="sync_job", cascade="all, delete-orphan")


class ConnectorSyncLog(Base, UUIDPrimaryKeyMixin):
    """Maintains detailed, immutable resource-level synchronization audit logs."""

    __tablename__ = "connector_sync_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    connector_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("connectors.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sync_job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("connector_sync_jobs.id", ondelete="CASCADE"), nullable=True, index=True
    )
    external_document_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    document_title: Mapped[str] = mapped_column(String(512), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_taken: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="SUCCESS", nullable=False)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    organization = relationship("Organization")
    connector = relationship("Connector", back_populates="sync_logs")
    sync_job = relationship("ConnectorSyncJob", back_populates="logs")
