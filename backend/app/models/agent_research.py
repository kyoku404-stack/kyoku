"""KEEP Phase 4.5 — Research Agents SQLAlchemy ORM Models.

Stores research investigations (`research_runs`), provenance-tracked authorized
evidence passages (`research_evidence`), claim-level cited findings
(`research_findings`), and append-only audit events (`research_events`).

Specification Reference: devdocs/p4/p4.5.txt (Section 8) & docs/Database/database-schema.md (Section 3.28)
Owner: Member 4 (Research Graph, Persistence, API & QA)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class ResearchRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Top-level durable multi-source research investigation scoped strictly by tenant."""

    __tablename__ = "research_runs"
    __table_args__ = (
        Index("idx_research_runs_tenant_status", "tenant_id", "status"),
        Index("idx_research_runs_tenant_created", "tenant_id", "created_at"),
        Index(
            "idx_research_runs_idempotency",
            "tenant_id",
            "requested_by",
            "idempotency_key",
        ),
    )

    research_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_output: Mapped[str] = mapped_column(String(32), default="detailed_report", nullable=False)
    max_sources: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    contradictions_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    unresolved_questions_json: Mapped[list[str]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    follow_up_suggestions_json: Mapped[list[str]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    warnings_json: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    correction_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sources_retrieved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sources_retained: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retrieval_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    synthesis_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    plan_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    workflow_execution_id: Mapped[str | None] = mapped_column(
        String(128), index=True, nullable=True
    )
    agent_execution_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ResearchEvidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Persisted provenance-tracked evidence passage collected for a research run."""

    __tablename__ = "research_evidence"
    __table_args__ = (Index("idx_research_evidence_run_tenant", "research_id", "tenant_id"),)

    record_pk: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    research_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    evidence_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_title: Mapped[str] = mapped_column(String(256), nullable=False)
    passage: Mapped[str] = mapped_column(Text, nullable=False)
    retrieval_reference: Mapped[str] = mapped_column(String(256), nullable=False)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    document_date: Mapped[str | None] = mapped_column(String(64), nullable=True)
    access_tier: Mapped[str] = mapped_column(String(32), default="read", nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class ResearchFindingModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Persisted claim-level finding bound to valid evidence_ids."""

    __tablename__ = "research_findings"
    __table_args__ = (Index("idx_research_findings_run_tenant", "research_id", "tenant_id"),)

    finding_pk: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    research_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    finding_id: Mapped[str] = mapped_column(String(64), nullable=False)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(32), default="factual", nullable=False)
    evidence_ids_json: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    confidence: Mapped[str] = mapped_column(String(16), default="low", nullable=False)
    limitations_json: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    has_contradiction: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ResearchEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Append-only audit trail for research lifecycle, validation, and error events."""

    __tablename__ = "research_events"
    __table_args__ = (Index("idx_research_events_run_tenant", "research_id", "tenant_id"),)

    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    research_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
