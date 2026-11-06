"""KEEP Enterprise Platform — Phase 3.7 Production Release & Security Audit ORM Models.

Specification Reference: devdocs/p3/p3.7.txt Section 3.24 & docs/database/database-schema.md
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
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class ProductionRelease(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Immutable production release catalog and deployment manifest record."""

    __tablename__ = "production_releases"

    release_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    version: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    release_tag: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    git_commit: Mapped[str] = mapped_column(String(50), nullable=False)
    changelog: Mapped[str] = mapped_column(Text, nullable=False)
    environment: Mapped[str] = mapped_column(String(50), default="production", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False)
    preflight_score: Mapped[float] = mapped_column(Numeric(4, 2), default=1.0, nullable=False)
    artifacts_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    deployed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReleaseChecklist(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Granular pre-flight verification items evaluated prior to release deployment."""

    __tablename__ = "release_checklists"

    release_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("production_releases.release_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    check_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PASSED", nullable=False)
    score: Mapped[float] = mapped_column(Numeric(4, 2), default=1.0, nullable=False)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class SecurityAuditRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Point-in-time enterprise security compliance benchmark ratings and findings."""

    __tablename__ = "security_audit_records"

    audit_type: Mapped[str] = mapped_column(String(80), default="OWASP_TOP_10", nullable=False)
    compliance_standard: Mapped[str] = mapped_column(
        String(100),
        default="OWASP_TOP_10_AND_LLM_TOP_10",
        nullable=False,
    )
    total_controls: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    passed_controls: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    failed_controls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overall_score: Mapped[float] = mapped_column(Numeric(5, 2), default=100.0, index=True, nullable=False)
    controls_json: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    findings_json: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    auditor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
