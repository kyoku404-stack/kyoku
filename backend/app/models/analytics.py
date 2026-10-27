"""KEEP Enterprise Platform — Analytics, Predictive Intelligence & Recommendations ORM Models.

Specification: devdocs/p2/p2.5.txt Section 3.17 & docs/database/database-schema.md
Author: Member 2 (Backend & Database Lead)
"""

import uuid
from datetime import UTC, date, datetime
from typing import Any

from backend.app.db.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class AnalyticsSnapshot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stores point-in-time analytical aggregations and Knowledge Health Score metrics."""

    __tablename__ = "analytics_snapshots"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    snapshot_date: Mapped[date] = mapped_column(
        Date, default=date.today, nullable=False, index=True
    )
    metric_category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    health_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default="{}", nullable=False
    )

    organization = relationship("Organization")


class AIRecommendation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stores actionable, prioritized AI strategic recommendations."""

    __tablename__ = "ai_recommendations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    impact_score: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    effort_score: Mapped[float] = mapped_column(Float, default=3.0, nullable=False)
    priority_index: Mapped[float] = mapped_column(Float, default=2.5, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False, index=True)
    action_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default="{}", nullable=False
    )

    organization = relationship("Organization")


class DetectedAnomaly(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stores operational anomaly detection events."""

    __tablename__ = "detected_anomalies"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    anomaly_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    deviation_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    organization = relationship("Organization")
