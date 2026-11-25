"""Phase 4.11 — Proactive Enterprise Intelligence Contracts.

Defines structured Pydantic v2 contracts for intelligence candidates,
insights, evidence references, detection runs, feedback, suppressions,
operational metrics, and security context.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

InsightCategory = Literal[
    "knowledge_gap",
    "contradiction",
    "stale_knowledge",
    "significant_change",
    "emerging_trend",
]

InsightStatus = Literal[
    "candidate",
    "validated",
    "published",
    "suppressed",
    "withheld",
    "investigating",
    "dismissed",
    "resolved",
]

EvidenceStatus = Literal["valid", "missing", "unauthorized", "stale"]

FeedbackType = Literal[
    "useful",
    "irrelevant",
    "already_known",
    "incorrect",
    "needs_more_evidence",
]

SuppressionScope = Literal["tenant", "audience", "user"]

RunStatus = Literal["running", "completed", "completed_with_errors", "failed"]

TriggerSource = Literal["manual", "event", "schedule"]


def _utcnow() -> datetime:
    return datetime.now(UTC)


def new_insight_id() -> str:
    return f"ins_{uuid4().hex[:16]}"


def new_run_id() -> str:
    return f"intel_run_{uuid4().hex[:16]}"


def new_evidence_id() -> str:
    return f"evd_{uuid4().hex[:16]}"


def new_feedback_id() -> str:
    return f"ifb_{uuid4().hex[:16]}"


def new_suppression_id() -> str:
    return f"isup_{uuid4().hex[:16]}"


def new_audit_id() -> str:
    return f"iaud_{uuid4().hex[:16]}"


class IntelligenceSecurityContext(BaseModel):
    """Zero-trust security context derived exclusively from KEEP auth."""

    tenant_id: str = Field(..., min_length=1, max_length=128)
    user_id: str = Field(..., min_length=1, max_length=128)
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    accessible_resource_refs: list[str] | None = Field(
        default=None,
        description="Optional explicit resource allowlist; None permits tenant-scoped resources.",
    )


class EvidenceReference(BaseModel):
    """Traceable reference to a KEEP source record (no restricted full-text copy)."""

    evidence_id: str = Field(default_factory=new_evidence_id)
    resource_ref: str = Field(..., min_length=1, max_length=255)
    source_type: str = Field(default="document", max_length=64)
    source_version: str | None = Field(default=None, max_length=64)
    snippet: str | None = Field(default=None, max_length=500)
    validation_outcome: EvidenceStatus = "valid"
    verified_at: datetime = Field(default_factory=_utcnow)


class IntelligenceCandidate(BaseModel):
    """Structured candidate emitted by an IntelligenceDetector before validation & ranking."""

    category: InsightCategory
    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., min_length=1, max_length=4000)
    observed_facts: list[str] = Field(default_factory=list)
    inferred_explanation: str | None = Field(default=None, max_length=2000)
    evidence_refs: list[str] = Field(default_factory=list)
    evidence_details: list[EvidenceReference] = Field(default_factory=list)
    affected_resource_refs: list[str] = Field(default_factory=list)
    impact_score: float = Field(..., ge=0.0, le=1.0)
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    evidence_quality_score: float = Field(default=0.7, ge=0.0, le=1.0)
    urgency_score: float = Field(default=0.5, ge=0.0, le=1.0)
    novelty_score: float = Field(default=0.8, ge=0.0, le=1.0)
    confidence_score: float = Field(default=0.7, ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    detector_id: str = Field(default="unknown", max_length=128)
    detector_version: str = Field(default="1.0.0", max_length=32)
    audience_roles: list[str] = Field(default_factory=list)
    allow_evidence_free: bool = False
    dedup_hint: str | None = Field(default=None, max_length=255)
    source_freshness_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntelligenceInsight(BaseModel):
    """Published or tracked proactive intelligence insight with audit and ranking metadata."""

    insight_id: str = Field(default_factory=new_insight_id)
    tenant_id: str = Field(..., min_length=1, max_length=128)
    run_id: str = Field(..., min_length=1, max_length=128)
    category: InsightCategory
    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., min_length=1, max_length=4000)
    observed_facts: list[str] = Field(default_factory=list)
    inferred_explanation: str | None = None
    limitations: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    evidence_records: list[EvidenceReference] = Field(default_factory=list)
    affected_resource_refs: list[str] = Field(default_factory=list)
    audience_roles: list[str] = Field(default_factory=list)
    impact_score: float = Field(..., ge=0.0, le=1.0)
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    evidence_quality_score: float = Field(..., ge=0.0, le=1.0)
    urgency_score: float = Field(..., ge=0.0, le=1.0)
    novelty_score: float = Field(..., ge=0.0, le=1.0)
    priority_score: float = Field(..., ge=0.0, le=100.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    status: InsightStatus = "published"
    dedup_key: str = Field(..., min_length=1, max_length=255)
    detector_id: str = Field(..., min_length=1, max_length=128)
    detector_version: str = Field(default="1.0.0", max_length=32)
    ranking_version: str = Field(default="v1", max_length=32)
    workflow_execution_id: str | None = None
    owner_id: str | None = None
    source_freshness_at: datetime | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class DetectionRunRecord(BaseModel):
    """Execution record for a proactive intelligence detection scan."""

    run_id: str = Field(default_factory=new_run_id)
    tenant_id: str
    trigger_source: TriggerSource = "manual"
    source_event_id: str | None = None
    detector_versions: dict[str, str] = Field(default_factory=dict)
    status: RunStatus = "running"
    candidates_generated: int = 0
    insights_published: int = 0
    insights_suppressed: int = 0
    detector_errors: list[dict[str, Any]] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=_utcnow)
    completed_at: datetime | None = None


class InsightFeedbackRequest(BaseModel):
    """User feedback payload on an intelligence insight."""

    feedback: FeedbackType
    comment: str | None = Field(default=None, max_length=1000)


class InsightFeedbackRecord(BaseModel):
    """Persisted feedback entry."""

    feedback_id: str = Field(default_factory=new_feedback_id)
    insight_id: str
    tenant_id: str
    user_id: str
    feedback: FeedbackType
    comment: str | None = None
    scope: Literal["user", "organization"] = "user"
    created_at: datetime = Field(default_factory=_utcnow)


class InsightDismissRequest(BaseModel):
    """Dismiss an insight either for the user's own feed or organization-wide."""

    scope: Literal["user", "organization"] = "user"
    reason: str | None = Field(default="Dismissed by user", max_length=500)


class InsightResolveRequest(BaseModel):
    """Resolve an insight with an optional resolution note."""

    resolution_note: str | None = Field(default="Resolved", max_length=1000)


class InsightInvestigateRequest(BaseModel):
    """Request further workflow investigation of a published insight."""

    workflow_id: str = Field(default="knowledge_analysis", min_length=1, max_length=128)
    notes: str | None = Field(default=None, max_length=1000)


class ScanRequest(BaseModel):
    """Authorized scan request payload."""

    observations: list[dict[str, Any]] = Field(default_factory=list)
    detector_ids: list[str] | None = None
    trigger_source: TriggerSource = "manual"
    source_event_id: str | None = None
    suppress_window_seconds: int = Field(default=3600, ge=0, le=86400 * 30)


class SuppressionRecord(BaseModel):
    """Active deduplication suppression or per-user dismissal record."""

    suppression_id: str = Field(default_factory=new_suppression_id)
    tenant_id: str
    dedup_key: str
    scope: SuppressionScope = "tenant"
    user_id: str | None = None
    reason: str
    suppressed_until: datetime
    created_at: datetime = Field(default_factory=_utcnow)


class IntelligenceAuditEvent(BaseModel):
    """Append-only audit trail entry."""

    audit_id: str = Field(default_factory=new_audit_id)
    tenant_id: str
    insight_id: str | None = None
    run_id: str | None = None
    action: str
    actor_id: str
    reason: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)


class OperationalMetrics(BaseModel):
    """Operational metrics for proactive intelligence monitoring."""

    tenant_id: str
    total_runs: int = 0
    total_candidates: int = 0
    published_insights: int = 0
    suppressed_insights: int = 0
    withheld_insights: int = 0
    dismissed_insights: int = 0
    resolved_insights: int = 0
    duplicate_suppression_rate: float = 0.0
    feedback_counts: dict[str, int] = Field(default_factory=dict)
    category_counts: dict[str, int] = Field(default_factory=dict)
