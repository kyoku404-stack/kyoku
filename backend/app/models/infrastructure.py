"""KEEP Enterprise Platform — Production Infrastructure, Scalability & Observability ORM Models.

Specification: devdocs/p3/p3.6.txt Section 3.23 & docs/database/database-schema.md
Author: Member 2 (Backend & Database Lead)
"""

from __future__ import annotations

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
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class SystemDeployment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tracks automated and manual system deployments, strategies, and rollbacks."""

    __tablename__ = "system_deployments"

    deployment_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    service_name: Mapped[str] = mapped_column(String(100), default="all", nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    strategy: Mapped[str] = mapped_column(String(50), default="ROLLING", nullable=False)
    environment: Mapped[str] = mapped_column(String(50), default="production", index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True, nullable=False)
    rollback_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    auto_rollback_on_failure: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deployed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class SystemBackup(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Disaster recovery snapshot catalog, storage paths, RPO tracking, and checksum verification."""

    __tablename__ = "system_backups"

    backup_name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    backup_type: Mapped[str] = mapped_column(String(50), default="DATABASE", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    storage_location: Mapped[str] = mapped_column(String(255), nullable=False)
    rpo_drift_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SystemHealthSnapshot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Periodic high-water mark telemetry and composite subsystem health records."""

    __tablename__ = "system_health_snapshots"

    status: Mapped[str] = mapped_column(String(50), default="HEALTHY", nullable=False)
    cpu_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    memory_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    disk_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    active_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    subsystems: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class SystemAuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Centralized operational diagnostic and system event log store."""

    __tablename__ = "system_audit_logs"

    service_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(30), default="INFO", index=True, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
