"""Phase 4.11 — Intelligence Repository Interface & In-Memory Implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime

from backend.app.agents.intelligence.contracts import (
    DetectionRunRecord,
    EvidenceReference,
    InsightCategory,
    InsightFeedbackRecord,
    InsightStatus,
    IntelligenceAuditEvent,
    IntelligenceInsight,
    SuppressionRecord,
)


class BaseIntelligenceRepository(ABC):
    """Abstract tenant-scoped persistence interface for Phase 4.11."""

    @abstractmethod
    async def create_run(self, run: DetectionRunRecord) -> DetectionRunRecord: ...

    @abstractmethod
    async def update_run(self, run: DetectionRunRecord) -> DetectionRunRecord: ...

    @abstractmethod
    async def get_run(self, tenant_id: str, run_id: str) -> DetectionRunRecord | None: ...

    @abstractmethod
    async def list_runs(self, tenant_id: str, limit: int = 50) -> list[DetectionRunRecord]: ...

    @abstractmethod
    async def save_insight(self, insight: IntelligenceInsight) -> IntelligenceInsight: ...

    @abstractmethod
    async def update_insight(self, insight: IntelligenceInsight) -> IntelligenceInsight: ...

    @abstractmethod
    async def get_insight(self, tenant_id: str, insight_id: str) -> IntelligenceInsight | None: ...

    @abstractmethod
    async def list_insights(
        self,
        tenant_id: str,
        *,
        category: InsightCategory | None = None,
        status: InsightStatus | None = None,
        min_priority: float | None = None,
        limit: int = 100,
    ) -> list[IntelligenceInsight]: ...

    @abstractmethod
    async def save_evidence(
        self,
        tenant_id: str,
        insight_id: str,
        records: list[EvidenceReference],
    ) -> list[EvidenceReference]: ...

    @abstractmethod
    async def get_evidence(self, tenant_id: str, insight_id: str) -> list[EvidenceReference]: ...

    @abstractmethod
    async def add_feedback(self, record: InsightFeedbackRecord) -> InsightFeedbackRecord: ...

    @abstractmethod
    async def list_feedback(self, tenant_id: str, insight_id: str | None = None) -> list[InsightFeedbackRecord]: ...

    @abstractmethod
    async def add_suppression(self, suppression: SuppressionRecord) -> SuppressionRecord: ...

    @abstractmethod
    async def list_active_suppressions(
        self,
        tenant_id: str,
        now: datetime | None = None,
    ) -> list[SuppressionRecord]: ...

    @abstractmethod
    async def add_audit_event(self, event: IntelligenceAuditEvent) -> IntelligenceAuditEvent: ...

    @abstractmethod
    async def list_audit_events(
        self,
        tenant_id: str,
        insight_id: str | None = None,
        run_id: str | None = None,
        limit: int = 200,
    ) -> list[IntelligenceAuditEvent]: ...


class InMemoryIntelligenceRepository(BaseIntelligenceRepository):
    """Thread-safe in-memory repository for deterministic unit testing and fallback."""

    def __init__(self) -> None:
        self._runs: dict[str, DetectionRunRecord] = {}
        self._insights: dict[str, IntelligenceInsight] = {}
        self._evidence: dict[str, list[EvidenceReference]] = {}
        self._feedback: list[InsightFeedbackRecord] = []
        self._suppressions: list[SuppressionRecord] = []
        self._audit_events: list[IntelligenceAuditEvent] = []

    async def create_run(self, run: DetectionRunRecord) -> DetectionRunRecord:
        self._runs[run.run_id] = run.model_copy(deep=True)
        return run

    async def update_run(self, run: DetectionRunRecord) -> DetectionRunRecord:
        self._runs[run.run_id] = run.model_copy(deep=True)
        return run

    async def get_run(self, tenant_id: str, run_id: str) -> DetectionRunRecord | None:
        rec = self._runs.get(run_id)
        if rec is None or rec.tenant_id != tenant_id:
            return None
        return rec.model_copy(deep=True)

    async def list_runs(self, tenant_id: str, limit: int = 50) -> list[DetectionRunRecord]:
        items = [r.model_copy(deep=True) for r in self._runs.values() if r.tenant_id == tenant_id]
        items.sort(key=lambda r: r.started_at, reverse=True)
        return items[:limit]

    async def save_insight(self, insight: IntelligenceInsight) -> IntelligenceInsight:
        self._insights[insight.insight_id] = insight.model_copy(deep=True)
        if insight.evidence_records:
            self._evidence[insight.insight_id] = [e.model_copy(deep=True) for e in insight.evidence_records]
        return insight

    async def update_insight(self, insight: IntelligenceInsight) -> IntelligenceInsight:
        self._insights[insight.insight_id] = insight.model_copy(deep=True)
        return insight

    async def get_insight(self, tenant_id: str, insight_id: str) -> IntelligenceInsight | None:
        item = self._insights.get(insight_id)
        if item is None or item.tenant_id != tenant_id:
            return None
        return item.model_copy(deep=True)

    async def list_insights(
        self,
        tenant_id: str,
        *,
        category: InsightCategory | None = None,
        status: InsightStatus | None = None,
        min_priority: float | None = None,
        limit: int = 100,
    ) -> list[IntelligenceInsight]:
        results: list[IntelligenceInsight] = []
        for ins in self._insights.values():
            if ins.tenant_id != tenant_id:
                continue
            if category is not None and ins.category != category:
                continue
            if status is not None and ins.status != status:
                continue
            if min_priority is not None and ins.priority_score < min_priority:
                continue
            results.append(ins.model_copy(deep=True))
        results.sort(key=lambda i: (-i.priority_score, -i.confidence_score, i.insight_id))
        return results[:limit]

    async def save_evidence(
        self,
        tenant_id: str,
        insight_id: str,
        records: list[EvidenceReference],
    ) -> list[EvidenceReference]:
        self._evidence[insight_id] = [r.model_copy(deep=True) for r in records]
        return records

    async def get_evidence(self, tenant_id: str, insight_id: str) -> list[EvidenceReference]:
        ins = self._insights.get(insight_id)
        if ins is None or ins.tenant_id != tenant_id:
            return []
        return [r.model_copy(deep=True) for r in self._evidence.get(insight_id, [])]

    async def add_feedback(self, record: InsightFeedbackRecord) -> InsightFeedbackRecord:
        self._feedback.append(record.model_copy(deep=True))
        return record

    async def list_feedback(self, tenant_id: str, insight_id: str | None = None) -> list[InsightFeedbackRecord]:
        return [
            f.model_copy(deep=True)
            for f in self._feedback
            if f.tenant_id == tenant_id and (insight_id is None or f.insight_id == insight_id)
        ]

    async def add_suppression(self, suppression: SuppressionRecord) -> SuppressionRecord:
        self._suppressions.append(suppression.model_copy(deep=True))
        return suppression

    async def list_active_suppressions(
        self,
        tenant_id: str,
        now: datetime | None = None,
    ) -> list[SuppressionRecord]:
        current = now or datetime.now(UTC)
        out: list[SuppressionRecord] = []
        for s in self._suppressions:
            if s.tenant_id != tenant_id:
                continue
            until = s.suppressed_until if s.suppressed_until.tzinfo else s.suppressed_until.replace(tzinfo=UTC)
            if until > current:
                out.append(s.model_copy(deep=True))
        return out

    async def add_audit_event(self, event: IntelligenceAuditEvent) -> IntelligenceAuditEvent:
        self._audit_events.append(event.model_copy(deep=True))
        return event

    async def list_audit_events(
        self,
        tenant_id: str,
        insight_id: str | None = None,
        run_id: str | None = None,
        limit: int = 200,
    ) -> list[IntelligenceAuditEvent]:
        events = [
            e.model_copy(deep=True)
            for e in self._audit_events
            if e.tenant_id == tenant_id
            and (insight_id is None or e.insight_id == insight_id)
            and (run_id is None or e.run_id == run_id)
        ]
        events.sort(key=lambda e: e.created_at, reverse=True)
        return events[:limit]
