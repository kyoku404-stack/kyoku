"""KEEP Phase 4.11 — Proactive Enterprise Intelligence SQLAlchemy ORM Models.

Persists detection runs (`intelligence_runs`), ranked insights (`intelligence_insights`),
evidence links (`intelligence_evidence`), user feedback (`intelligence_feedback`),
deduplication/dismissal suppressions (`intelligence_suppressions`), and append-only
audit trail (`intelligence_audit_events`).
"""

from __future__ import annotations

import datetime
from typing import Any

from backend.app.db.base import Base, UUIDPrimaryKeyMixin
from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


class IntelligenceRunModel(Base, UUIDPrimaryKeyMixin):
    """Durable proactive detection scan execution record."""

    __tablename__ = "intelligence_runs"
    __table_args__ = (Index("idx_intel_runs_tenant_status", "tenant_id", "status"),)

    run_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    trigger_source: Mapped[str] = mapped_column(String(64), default="manual", nullable=False)
    source_event_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    detector_versions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    candidates_generated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    insights_published: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    insights_suppressed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    detector_errors: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IntelligenceInsightModel(Base, UUIDPrimaryKeyMixin):
    """Durable tenant-scoped proactive intelligence insight."""

    __tablename__ = "intelligence_insights"
    __table_args__ = (
        Index("idx_intel_insights_tenant_status", "tenant_id", "status"),
        Index("idx_intel_insights_tenant_priority", "tenant_id", "priority_score"),
        Index("idx_intel_insights_tenant_dedup", "tenant_id", "dedup_key"),
    )

    insight_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    run_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    observed_facts: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    inferred_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    evidence_refs: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    affected_resource_refs: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    audience_roles: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    impact_score: Mapped[float] = mapped_column(Float, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    urgency_score: Mapped[float] = mapped_column(Float, nullable=False)
    novelty_score: Mapped[float] = mapped_column(Float, nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    dedup_key: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    detector_id: Mapped[str] = mapped_column(String(128), nullable=False)
    detector_version: Mapped[str] = mapped_column(String(32), nullable=False)
    ranking_version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False)
    workflow_execution_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    owner_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_freshness_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class IntelligenceEvidenceModel(Base, UUIDPrimaryKeyMixin):
    """Source provenance references linked to an intelligence insight."""

    __tablename__ = "intelligence_evidence"
    __table_args__ = (Index("idx_intel_evidence_tenant_insight", "tenant_id", "insight_id"),)

    evidence_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    insight_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    resource_ref: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), default="document", nullable=False)
    source_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_outcome: Mapped[str] = mapped_column(String(32), default="valid", nullable=False)
    verified_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )


class IntelligenceFeedbackModel(Base, UUIDPrimaryKeyMixin):
    """User feedback entries for proactive intelligence insights."""

    __tablename__ = "intelligence_feedback"
    __table_args__ = (Index("idx_intel_feedback_tenant_insight", "tenant_id", "insight_id"),)

    feedback_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    insight_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    feedback: Mapped[str] = mapped_column(String(32), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope: Mapped[str] = mapped_column(String(32), default="user", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )


class IntelligenceSuppressionModel(Base, UUIDPrimaryKeyMixin):
    """Active deduplication windows and per-user insight dismissals."""

    __tablename__ = "intelligence_suppressions"
    __table_args__ = (
        Index("idx_intel_suppress_tenant_dedup", "tenant_id", "dedup_key"),
        Index("idx_intel_suppress_until", "suppressed_until"),
    )

    suppression_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    dedup_key: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    scope: Mapped[str] = mapped_column(String(32), default="tenant", nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    suppressed_until: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )


class IntelligenceAuditEventModel(Base, UUIDPrimaryKeyMixin):
    """Append-only audit log for intelligence lifecycle events."""

    __tablename__ = "intelligence_audit_events"
    __table_args__ = (Index("idx_intel_audit_tenant_action", "tenant_id", "action"),)

    audit_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    insight_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    run_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
