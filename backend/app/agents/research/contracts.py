"""KEEP Phase 4.5 — Research Agent Contracts, Schemas & Interfaces.

Defines canonical Pydantic v2 models for research requests, provenance-tracked
evidence passages, claim-level findings, contradiction records, quality reports,
and Protocol interfaces for retrieval, synthesis, quality validation, and persistence.

Owner: Member 1 (Research Agent Core)
Specification: devdocs/p4/p4.5.txt (Sections 3, 4.2, 5, 6, 7)
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal, Protocol, runtime_checkable
from uuid import uuid4

from backend.app.agents.contracts import AgentContext, EvidenceReference
from backend.app.agents.metadata import CapabilityAccess
from pydantic import BaseModel, Field, field_validator

RESEARCH_SCHEMA_VERSION = "1.0"

RequiredOutputType = Literal["summary", "comparison", "detailed_report"]
ConfidenceLevel = Literal["low", "medium", "high"]
ClaimType = Literal["factual", "hypothesis", "recommendation"]


class ResearchStatus(str, Enum):
    """Canonical lifecycle statuses for a KEEP research investigation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_RESEARCH_STATUSES: frozenset[ResearchStatus] = frozenset(
    {
        ResearchStatus.COMPLETED,
        ResearchStatus.PARTIAL,
        ResearchStatus.INSUFFICIENT_EVIDENCE,
        ResearchStatus.FAILED,
        ResearchStatus.CANCELLED,
    }
)

REPORT_READY_STATUSES: frozenset[ResearchStatus] = frozenset(
    {
        ResearchStatus.COMPLETED,
        ResearchStatus.PARTIAL,
        ResearchStatus.INSUFFICIENT_EVIDENCE,
    }
)


def generate_research_id() -> str:
    """Generates a unique external research investigation identifier."""
    return f"res_{uuid4().hex[:16]}"


def generate_research_event_id() -> str:
    """Generates a unique audit event identifier for a research run."""
    return f"resevt_{uuid4().hex[:16]}"


def compute_research_fingerprint(request: ResearchRequest) -> str:
    """Produces a deterministic SHA-256 fingerprint for scoped idempotency checks."""
    canonical = {
        "question": request.question.strip(),
        "scope": (request.scope or "").strip(),
        "max_sources": request.max_sources,
        "required_output": request.required_output,
        "filters": request.filters,
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class ResearchRequest(BaseModel):
    """Validated investigation request submitted to KEEP's Research Agent."""

    research_id: str = Field(default_factory=generate_research_id, min_length=1, max_length=128)
    question: str = Field(..., min_length=3, max_length=2000)
    scope: str | None = Field(default=None, max_length=1000)
    max_sources: int = Field(default=12, ge=1, le=30)
    required_output: RequiredOutputType = Field(default="detailed_report")
    filters: dict[str, Any] = Field(default_factory=dict)
    plan_id: str | None = Field(default=None, max_length=128)
    workflow_execution_id: str | None = Field(default=None, max_length=128)
    agent_execution_id: str | None = Field(default=None, max_length=128)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("Research question must contain at least 3 non-whitespace characters.")
        return cleaned

    @field_validator("scope")
    @classmethod
    def strip_scope(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class EvidenceItem(BaseModel):
    """Provenance-tracked, sanitized evidence passage collected from authorized KEEP sources."""

    evidence_id: str = Field(..., min_length=2, max_length=64)
    source_id: str = Field(..., min_length=1, max_length=128)
    source_title: str = Field(..., min_length=1, max_length=256)
    passage: str = Field(..., min_length=1, max_length=4000)
    retrieval_reference: str = Field(..., min_length=1, max_length=256)
    relevance_score: float | None = Field(default=None, ge=0.0, le=1.0)
    document_date: str | None = Field(default=None, max_length=64)
    access_tier: CapabilityAccess = Field(default="read")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("evidence_id", "source_id", "source_title", "passage", "retrieval_reference")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("EvidenceItem field cannot be blank.")
        return cleaned

    def to_agent_evidence_reference(self, *, tenant_id: str | None = None) -> EvidenceReference:
        """Converts this research EvidenceItem into a Phase 4.1 AgentResult EvidenceReference."""
        return EvidenceReference(
            source_id=self.source_id,
            source_type="document",
            title=self.source_title,
            excerpt=self.passage[:2000],
            uri=self.retrieval_reference,
            score=self.relevance_score,
            tenant_id=tenant_id,
        )


class ContradictionRecord(BaseModel):
    """Explicitly surfaces conflicting claims across retrieved evidence sources."""

    topic: str = Field(..., min_length=1, max_length=256)
    description: str = Field(..., min_length=1, max_length=1000)
    evidence_ids: list[str] = Field(default_factory=list)
    source_dates: list[str] = Field(default_factory=list)


class ResearchFinding(BaseModel):
    """Structured claim-level finding backed by verifiable evidence_ids."""

    finding_id: str = Field(..., min_length=2, max_length=64)
    claim: str = Field(..., min_length=3, max_length=2000)
    claim_type: ClaimType = Field(default="factual")
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = Field(default="low")
    limitations: list[str] = Field(default_factory=list)
    has_contradiction: bool = Field(default=False)

    @field_validator("finding_id", "claim")
    @classmethod
    def strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("ResearchFinding text fields cannot be blank.")
        return cleaned


class RetrievalOutcome(BaseModel):
    """Structured output returned by ResearchRetrievalInterface."""

    evidence: list[EvidenceItem] = Field(default_factory=list)
    sources_retrieved: int = Field(default=0, ge=0)
    sources_retained: int = Field(default=0, ge=0)
    retrieval_latency_ms: int = Field(default=0, ge=0)
    sanitized_passages_count: int = Field(default=0, ge=0)
    filtered_restricted_count: int = Field(default=0, ge=0)
    warnings: list[str] = Field(default_factory=list)


class SynthesisDraft(BaseModel):
    """Structured synthesis output before or after quality validation."""

    summary: str = Field(..., min_length=1, max_length=4000)
    findings: list[ResearchFinding] = Field(default_factory=list)
    contradictions: list[ContradictionRecord] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)
    synthesis_latency_ms: int = Field(default=0, ge=0)


class QualityCheckResult(BaseModel):
    """Outcome of citation integrity, grounding, contradiction, and coverage validation."""

    is_valid: bool
    invalid_citations: list[str] = Field(default_factory=list)
    unsupported_findings: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    recommended_unresolved_questions: list[str] = Field(default_factory=list)


class ResearchReport(BaseModel):
    """Canonical structured output produced by KEEP's Research Agent."""

    research_id: str
    question: str
    scope: str | None = None
    required_output: RequiredOutputType = "detailed_report"
    status: ResearchStatus
    summary: str
    findings: list[ResearchFinding] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    contradictions: list[ContradictionRecord] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    correction_attempts: int = Field(default=0, ge=0)
    sources_retrieved: int = Field(default=0, ge=0)
    sources_retained: int = Field(default=0, ge=0)
    retrieval_latency_ms: int | None = None
    synthesis_latency_ms: int | None = None
    correlation_id: str | None = None
    completed_at: datetime | None = None
    schema_version: str = Field(default=RESEARCH_SCHEMA_VERSION)


class ResearchEventRecord(BaseModel):
    """Immutable audit trail entry for a research investigation."""

    event_id: str = Field(default_factory=generate_research_event_id)
    research_id: str
    tenant_id: str
    event_type: str
    correlation_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ResearchRunRecord(BaseModel):
    """Persisted metadata and lifecycle record for a research investigation."""

    research_id: str
    tenant_id: str
    requested_by: str
    question: str
    scope: str | None = None
    required_output: RequiredOutputType = "detailed_report"
    max_sources: int = 12
    status: ResearchStatus = ResearchStatus.PENDING
    summary: str | None = None
    contradictions: list[ContradictionRecord] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    correction_attempts: int = 0
    sources_retrieved: int = 0
    sources_retained: int = 0
    retrieval_latency_ms: int | None = None
    synthesis_latency_ms: int | None = None
    correlation_id: str
    plan_id: str | None = None
    workflow_execution_id: str | None = None
    agent_execution_id: str | None = None
    idempotency_key: str | None = None
    request_fingerprint: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


@runtime_checkable
class ResearchRetrievalInterface(Protocol):
    """Protocol for tenant-scoped authorized research evidence retrieval."""

    async def retrieve_evidence(
        self,
        request: ResearchRequest,
        context: AgentContext,
    ) -> RetrievalOutcome:
        ...


@runtime_checkable
class ResearchSynthesisInterface(Protocol):
    """Protocol for cross-source evidence synthesis and bounded citation correction."""

    async def synthesize(
        self,
        request: ResearchRequest,
        evidence: list[EvidenceItem],
        context: AgentContext,
    ) -> SynthesisDraft:
        ...

    async def correct_findings(
        self,
        request: ResearchRequest,
        draft: SynthesisDraft,
        evidence: list[EvidenceItem],
        quality_issues: list[str],
        context: AgentContext,
    ) -> SynthesisDraft:
        ...


@runtime_checkable
class ResearchQualityInterface(Protocol):
    """Protocol for validating citation integrity, claim grounding, and evidence quality."""

    def validate(
        self,
        request: ResearchRequest,
        draft: SynthesisDraft,
        evidence: list[EvidenceItem],
    ) -> QualityCheckResult:
        ...


@runtime_checkable
class ResearchRepositoryInterface(Protocol):
    """Protocol for tenant-scoped research persistence."""

    async def create_run(self, run: ResearchRunRecord) -> ResearchRunRecord:
        ...

    async def update_run(self, run: ResearchRunRecord) -> ResearchRunRecord:
        ...

    async def get_run(self, research_id: str, tenant_id: str) -> ResearchRunRecord | None:
        ...

    async def list_runs(
        self,
        tenant_id: str,
        *,
        status: ResearchStatus | None = None,
        limit: int = 50,
    ) -> list[ResearchRunRecord]:
        ...

    async def find_by_idempotency_key(
        self,
        tenant_id: str,
        requested_by: str,
        idempotency_key: str,
    ) -> ResearchRunRecord | None:
        ...

    async def save_evidence(
        self,
        research_id: str,
        tenant_id: str,
        evidence: list[EvidenceItem],
    ) -> None:
        ...

    async def get_evidence(self, research_id: str, tenant_id: str) -> list[EvidenceItem]:
        ...

    async def save_findings(
        self,
        research_id: str,
        tenant_id: str,
        findings: list[ResearchFinding],
    ) -> None:
        ...

    async def get_findings(self, research_id: str, tenant_id: str) -> list[ResearchFinding]:
        ...

    async def append_event(self, event: ResearchEventRecord) -> ResearchEventRecord:
        ...

    async def list_events(self, research_id: str, tenant_id: str) -> list[ResearchEventRecord]:
        ...
