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


class SqlAlchemyIntelligenceRepository(BaseIntelligenceRepository):
    """Durable SQLAlchemy async repository for Phase 4.11 tables."""

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _to_run(row) -> DetectionRunRecord:
        return DetectionRunRecord(
            run_id=row.run_id,
            tenant_id=row.tenant_id,
            trigger_source=row.trigger_source,
            source_event_id=row.source_event_id,
            detector_versions=dict(row.detector_versions or {}),
            status=row.status,
            candidates_generated=row.candidates_generated,
            insights_published=row.insights_published,
            insights_suppressed=row.insights_suppressed,
            detector_errors=list(row.detector_errors or []),
            started_at=row.started_at,
            completed_at=row.completed_at,
        )

    @staticmethod
    def _to_insight(row) -> IntelligenceInsight:
        return IntelligenceInsight(
            insight_id=row.insight_id,
            tenant_id=row.tenant_id,
            run_id=row.run_id,
            category=row.category,
            title=row.title,
            summary=row.summary,
            observed_facts=list(row.observed_facts or []),
            inferred_explanation=row.inferred_explanation,
            limitations=list(row.limitations or []),
            evidence_refs=list(row.evidence_refs or []),
            affected_resource_refs=list(row.affected_resource_refs or []),
            audience_roles=list(row.audience_roles or []),
            impact_score=row.impact_score,
            relevance_score=row.relevance_score,
            evidence_quality_score=row.evidence_quality_score,
            urgency_score=row.urgency_score,
            novelty_score=row.novelty_score,
            priority_score=row.priority_score,
            confidence_score=row.confidence_score,
            status=row.status,
            dedup_key=row.dedup_key,
            detector_id=row.detector_id,
            detector_version=row.detector_version,
            ranking_version=row.ranking_version,
            workflow_execution_id=row.workflow_execution_id,
            owner_id=row.owner_id,
            source_freshness_at=row.source_freshness_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def create_run(self, run: DetectionRunRecord) -> DetectionRunRecord:
        from backend.app.models.agent_intelligence import IntelligenceRunModel

        async with self._session_factory() as db:
            db.add(
                IntelligenceRunModel(
                    run_id=run.run_id,
                    tenant_id=run.tenant_id,
                    trigger_source=run.trigger_source,
                    source_event_id=run.source_event_id,
                    detector_versions=run.detector_versions,
                    status=run.status,
                    candidates_generated=run.candidates_generated,
                    insights_published=run.insights_published,
                    insights_suppressed=run.insights_suppressed,
                    detector_errors=run.detector_errors,
                    started_at=run.started_at,
                    completed_at=run.completed_at,
                )
            )
            await db.commit()
        return run

    async def update_run(self, run: DetectionRunRecord) -> DetectionRunRecord:
        from backend.app.models.agent_intelligence import IntelligenceRunModel
        from sqlalchemy import select

        async with self._session_factory() as db:
            row = await db.scalar(
                select(IntelligenceRunModel).where(
                    IntelligenceRunModel.tenant_id == run.tenant_id,
                    IntelligenceRunModel.run_id == run.run_id,
                )
            )
            if row is not None:
                row.status = run.status
                row.candidates_generated = run.candidates_generated
                row.insights_published = run.insights_published
                row.insights_suppressed = run.insights_suppressed
                row.detector_errors = run.detector_errors
                row.completed_at = run.completed_at
                await db.commit()
        return run

    async def get_run(self, tenant_id: str, run_id: str) -> DetectionRunRecord | None:
        from backend.app.models.agent_intelligence import IntelligenceRunModel
        from sqlalchemy import select

        async with self._session_factory() as db:
            row = await db.scalar(
                select(IntelligenceRunModel).where(
                    IntelligenceRunModel.tenant_id == tenant_id,
                    IntelligenceRunModel.run_id == run_id,
                )
            )
            return self._to_run(row) if row is not None else None

    async def list_runs(self, tenant_id: str, limit: int = 50) -> list[DetectionRunRecord]:
        from backend.app.models.agent_intelligence import IntelligenceRunModel
        from sqlalchemy import select

        async with self._session_factory() as db:
            rows = (
                await db.scalars(
                    select(IntelligenceRunModel)
                    .where(IntelligenceRunModel.tenant_id == tenant_id)
                    .order_by(IntelligenceRunModel.started_at.desc())
                    .limit(limit)
                )
            ).all()
            return [self._to_run(r) for r in rows]

    async def save_insight(self, insight: IntelligenceInsight) -> IntelligenceInsight:
        from backend.app.models.agent_intelligence import IntelligenceInsightModel

        async with self._session_factory() as db:
            db.add(
                IntelligenceInsightModel(
                    insight_id=insight.insight_id,
                    tenant_id=insight.tenant_id,
                    run_id=insight.run_id,
                    category=insight.category,
                    title=insight.title,
                    summary=insight.summary,
                    observed_facts=insight.observed_facts,
                    inferred_explanation=insight.inferred_explanation,
                    limitations=insight.limitations,
                    evidence_refs=insight.evidence_refs,
                    affected_resource_refs=insight.affected_resource_refs,
                    audience_roles=insight.audience_roles,
                    impact_score=insight.impact_score,
                    relevance_score=insight.relevance_score,
                    evidence_quality_score=insight.evidence_quality_score,
                    urgency_score=insight.urgency_score,
                    novelty_score=insight.novelty_score,
                    priority_score=insight.priority_score,
                    confidence_score=insight.confidence_score,
                    status=insight.status,
                    dedup_key=insight.dedup_key,
                    detector_id=insight.detector_id,
                    detector_version=insight.detector_version,
                    ranking_version=insight.ranking_version,
                    workflow_execution_id=insight.workflow_execution_id,
                    owner_id=insight.owner_id,
                    source_freshness_at=insight.source_freshness_at,
                    created_at=insight.created_at,
                    updated_at=insight.updated_at,
                )
            )
            await db.commit()
        return insight

    async def update_insight(self, insight: IntelligenceInsight) -> IntelligenceInsight:
        from backend.app.models.agent_intelligence import IntelligenceInsightModel
        from sqlalchemy import select

        async with self._session_factory() as db:
            row = await db.scalar(
                select(IntelligenceInsightModel).where(
                    IntelligenceInsightModel.tenant_id == insight.tenant_id,
                    IntelligenceInsightModel.insight_id == insight.insight_id,
                )
            )
            if row is not None:
                row.status = insight.status
                row.workflow_execution_id = insight.workflow_execution_id
                row.updated_at = insight.updated_at
                await db.commit()
        return insight

    async def get_insight(self, tenant_id: str, insight_id: str) -> IntelligenceInsight | None:
        from backend.app.models.agent_intelligence import IntelligenceInsightModel
        from sqlalchemy import select

        async with self._session_factory() as db:
            row = await db.scalar(
                select(IntelligenceInsightModel).where(
                    IntelligenceInsightModel.tenant_id == tenant_id,
                    IntelligenceInsightModel.insight_id == insight_id,
                )
            )
            return self._to_insight(row) if row is not None else None

    async def list_insights(
        self,
        tenant_id: str,
        *,
        category: InsightCategory | None = None,
        status: InsightStatus | None = None,
        min_priority: float | None = None,
        limit: int = 100,
    ) -> list[IntelligenceInsight]:
        from backend.app.models.agent_intelligence import IntelligenceInsightModel
        from sqlalchemy import select

        stmt = select(IntelligenceInsightModel).where(IntelligenceInsightModel.tenant_id == tenant_id)
        if category is not None:
            stmt = stmt.where(IntelligenceInsightModel.category == category)
        if status is not None:
            stmt = stmt.where(IntelligenceInsightModel.status == status)
        if min_priority is not None:
            stmt = stmt.where(IntelligenceInsightModel.priority_score >= min_priority)
        stmt = stmt.order_by(IntelligenceInsightModel.priority_score.desc()).limit(limit)

        async with self._session_factory() as db:
            rows = (await db.scalars(stmt)).all()
            return [self._to_insight(r) for r in rows]

    async def save_evidence(
        self,
        tenant_id: str,
        insight_id: str,
        records: list[EvidenceReference],
    ) -> list[EvidenceReference]:
        from backend.app.models.agent_intelligence import IntelligenceEvidenceModel

        async with self._session_factory() as db:
            for rec in records:
                db.add(
                    IntelligenceEvidenceModel(
                        evidence_id=rec.evidence_id,
                        insight_id=insight_id,
                        tenant_id=tenant_id,
                        resource_ref=rec.resource_ref,
                        source_type=rec.source_type,
                        source_version=rec.source_version,
                        snippet=rec.snippet,
                        validation_outcome=rec.validation_outcome,
                        verified_at=rec.verified_at,
                    )
                )
            await db.commit()
        return records

    async def get_evidence(self, tenant_id: str, insight_id: str) -> list[EvidenceReference]:
        from backend.app.models.agent_intelligence import IntelligenceEvidenceModel
        from sqlalchemy import select

        async with self._session_factory() as db:
            rows = (
                await db.scalars(
                    select(IntelligenceEvidenceModel).where(
                        IntelligenceEvidenceModel.tenant_id == tenant_id,
                        IntelligenceEvidenceModel.insight_id == insight_id,
                    )
                )
            ).all()
            return [
                EvidenceReference(
                    evidence_id=r.evidence_id,
                    resource_ref=r.resource_ref,
                    source_type=r.source_type,
                    source_version=r.source_version,
                    snippet=r.snippet,
                    validation_outcome=r.validation_outcome,  # type: ignore[arg-type]
                    verified_at=r.verified_at,
                )
                for r in rows
            ]

    async def add_feedback(self, record: InsightFeedbackRecord) -> InsightFeedbackRecord:
        from backend.app.models.agent_intelligence import IntelligenceFeedbackModel

        async with self._session_factory() as db:
            db.add(
                IntelligenceFeedbackModel(
                    feedback_id=record.feedback_id,
                    insight_id=record.insight_id,
                    tenant_id=record.tenant_id,
                    user_id=record.user_id,
                    feedback=record.feedback,
                    comment=record.comment,
                    scope=record.scope,
                    created_at=record.created_at,
                )
            )
            await db.commit()
        return record

    async def list_feedback(self, tenant_id: str, insight_id: str | None = None) -> list[InsightFeedbackRecord]:
        from backend.app.models.agent_intelligence import IntelligenceFeedbackModel
        from sqlalchemy import select

        stmt = select(IntelligenceFeedbackModel).where(IntelligenceFeedbackModel.tenant_id == tenant_id)
        if insight_id is not None:
            stmt = stmt.where(IntelligenceFeedbackModel.insight_id == insight_id)
        async with self._session_factory() as db:
            rows = (await db.scalars(stmt)).all()
            return [
                InsightFeedbackRecord(
                    feedback_id=r.feedback_id,
                    insight_id=r.insight_id,
                    tenant_id=r.tenant_id,
                    user_id=r.user_id,
                    feedback=r.feedback,  # type: ignore[arg-type]
                    comment=r.comment,
                    scope=r.scope,  # type: ignore[arg-type]
                    created_at=r.created_at,
                )
                for r in rows
            ]

    async def add_suppression(self, suppression: SuppressionRecord) -> SuppressionRecord:
        from backend.app.models.agent_intelligence import IntelligenceSuppressionModel

        async with self._session_factory() as db:
            db.add(
                IntelligenceSuppressionModel(
                    suppression_id=suppression.suppression_id,
                    tenant_id=suppression.tenant_id,
                    dedup_key=suppression.dedup_key,
                    scope=suppression.scope,
                    user_id=suppression.user_id,
                    reason=suppression.reason,
                    suppressed_until=suppression.suppressed_until,
                    created_at=suppression.created_at,
                )
            )
            await db.commit()
        return suppression

    async def list_active_suppressions(
        self,
        tenant_id: str,
        now: datetime | None = None,
    ) -> list[SuppressionRecord]:
        from backend.app.models.agent_intelligence import IntelligenceSuppressionModel
        from sqlalchemy import select

        current = now or datetime.now(UTC)
        async with self._session_factory() as db:
            rows = (
                await db.scalars(
                    select(IntelligenceSuppressionModel).where(
                        IntelligenceSuppressionModel.tenant_id == tenant_id,
                        IntelligenceSuppressionModel.suppressed_until > current,
                    )
                )
            ).all()
            return [
                SuppressionRecord(
                    suppression_id=r.suppression_id,
                    tenant_id=r.tenant_id,
                    dedup_key=r.dedup_key,
                    scope=r.scope,  # type: ignore[arg-type]
                    user_id=r.user_id,
                    reason=r.reason,
                    suppressed_until=r.suppressed_until,
                    created_at=r.created_at,
                )
                for r in rows
            ]

    async def add_audit_event(self, event: IntelligenceAuditEvent) -> IntelligenceAuditEvent:
        from backend.app.models.agent_intelligence import IntelligenceAuditEventModel

        async with self._session_factory() as db:
            db.add(
                IntelligenceAuditEventModel(
                    audit_id=event.audit_id,
                    tenant_id=event.tenant_id,
                    insight_id=event.insight_id,
                    run_id=event.run_id,
                    action=event.action,
                    actor_id=event.actor_id,
                    reason=event.reason,
                    details=event.details,
                    created_at=event.created_at,
                )
            )
            await db.commit()
        return event

    async def list_audit_events(
        self,
        tenant_id: str,
        insight_id: str | None = None,
        run_id: str | None = None,
        limit: int = 200,
    ) -> list[IntelligenceAuditEvent]:
        from backend.app.models.agent_intelligence import IntelligenceAuditEventModel
        from sqlalchemy import select

        stmt = select(IntelligenceAuditEventModel).where(IntelligenceAuditEventModel.tenant_id == tenant_id)
        if insight_id is not None:
            stmt = stmt.where(IntelligenceAuditEventModel.insight_id == insight_id)
        if run_id is not None:
            stmt = stmt.where(IntelligenceAuditEventModel.run_id == run_id)
        stmt = stmt.order_by(IntelligenceAuditEventModel.created_at.desc()).limit(limit)

        async with self._session_factory() as db:
            rows = (await db.scalars(stmt)).all()
            return [
                IntelligenceAuditEvent(
                    audit_id=r.audit_id,
                    tenant_id=r.tenant_id,
                    insight_id=r.insight_id,
                    run_id=r.run_id,
                    action=r.action,
                    actor_id=r.actor_id,
                    reason=r.reason,
                    details=dict(r.details or {}),
                    created_at=r.created_at,
                )
                for r in rows
            ]
