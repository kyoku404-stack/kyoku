"""KEEP Phase 4.5 — Research Persistence Repositories (InMemory & SQLAlchemy).

Provides tenant-scoped CRUD for `research_runs`, `research_evidence`,
`research_findings`, and `research_events` with SQLite/PostgreSQL UTC datetime
normalization and scoped idempotency lookups.

Owner: Member 4 (Research Graph, Persistence, API & QA)
Specification: devdocs/p4/p4.5.txt (Section 8)
"""

from __future__ import annotations

from datetime import UTC, datetime

from backend.app.agents.research.contracts import (
    ContradictionRecord,
    EvidenceItem,
    ResearchEventRecord,
    ResearchFinding,
    ResearchRunRecord,
    ResearchStatus,
)
from backend.app.models.agent_research import (
    ResearchEvent,
    ResearchEvidence,
    ResearchFindingModel,
    ResearchRun,
)
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


class InMemoryResearchRepository:
    """Thread-safe in-memory research repository for fast unit testing."""

    def __init__(self) -> None:
        self._runs: dict[str, ResearchRunRecord] = {}
        self._evidence: dict[str, list[EvidenceItem]] = {}
        self._findings: dict[str, list[ResearchFinding]] = {}
        self._events: dict[str, list[ResearchEventRecord]] = {}

    async def create_run(self, run: ResearchRunRecord) -> ResearchRunRecord:
        stored = run.model_copy(deep=True)
        self._runs[run.research_id] = stored
        return stored.model_copy(deep=True)

    async def update_run(self, run: ResearchRunRecord) -> ResearchRunRecord:
        stored = run.model_copy(deep=True)
        self._runs[run.research_id] = stored
        return stored.model_copy(deep=True)

    async def get_run(self, research_id: str, tenant_id: str) -> ResearchRunRecord | None:
        run = self._runs.get(research_id)
        if run is None or run.tenant_id != tenant_id:
            return None
        return run.model_copy(deep=True)

    async def list_runs(
        self,
        tenant_id: str,
        *,
        status: ResearchStatus | None = None,
        limit: int = 50,
    ) -> list[ResearchRunRecord]:
        items = [r.model_copy(deep=True) for r in self._runs.values() if r.tenant_id == tenant_id]
        if status is not None:
            items = [r for r in items if r.status == status]
        items.sort(key=lambda r: r.created_at, reverse=True)
        return items[:limit]

    async def find_by_idempotency_key(
        self,
        tenant_id: str,
        requested_by: str,
        idempotency_key: str,
    ) -> ResearchRunRecord | None:
        for run in self._runs.values():
            if (
                run.tenant_id == tenant_id
                and run.requested_by == requested_by
                and run.idempotency_key == idempotency_key
            ):
                return run.model_copy(deep=True)
        return None

    async def save_evidence(
        self,
        research_id: str,
        tenant_id: str,
        evidence: list[EvidenceItem],
    ) -> None:
        self._evidence[research_id] = [e.model_copy(deep=True) for e in evidence]

    async def get_evidence(self, research_id: str, tenant_id: str) -> list[EvidenceItem]:
        run = self._runs.get(research_id)
        if run is None or run.tenant_id != tenant_id:
            return []
        return [e.model_copy(deep=True) for e in self._evidence.get(research_id, [])]

    async def save_findings(
        self,
        research_id: str,
        tenant_id: str,
        findings: list[ResearchFinding],
    ) -> None:
        self._findings[research_id] = [f.model_copy(deep=True) for f in findings]

    async def get_findings(self, research_id: str, tenant_id: str) -> list[ResearchFinding]:
        run = self._runs.get(research_id)
        if run is None or run.tenant_id != tenant_id:
            return []
        return [f.model_copy(deep=True) for f in self._findings.get(research_id, [])]

    async def append_event(self, event: ResearchEventRecord) -> ResearchEventRecord:
        stored = event.model_copy(deep=True)
        self._events.setdefault(event.research_id, []).append(stored)
        return stored.model_copy(deep=True)

    async def list_events(self, research_id: str, tenant_id: str) -> list[ResearchEventRecord]:
        run = self._runs.get(research_id)
        if run is None or run.tenant_id != tenant_id:
            return []
        return [e.model_copy(deep=True) for e in self._events.get(research_id, [])]


class SQLAlchemyResearchRepository:
    """Async SQLAlchemy repository persisting Phase 4.5 research investigations."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _row_to_run(row: ResearchRun) -> ResearchRunRecord:
        return ResearchRunRecord(
            research_id=row.research_id,
            tenant_id=row.tenant_id,
            requested_by=row.requested_by,
            question=row.question,
            scope=row.scope,
            required_output=row.required_output,  # type: ignore[arg-type]
            max_sources=row.max_sources,
            status=ResearchStatus(row.status),
            summary=row.summary,
            contradictions=[
                ContradictionRecord.model_validate(c) for c in (row.contradictions_json or [])
            ],
            unresolved_questions=list(row.unresolved_questions_json or []),
            follow_up_suggestions=list(row.follow_up_suggestions_json or []),
            warnings=list(row.warnings_json or []),
            correction_attempts=row.correction_attempts,
            sources_retrieved=row.sources_retrieved,
            sources_retained=row.sources_retained,
            retrieval_latency_ms=row.retrieval_latency_ms,
            synthesis_latency_ms=row.synthesis_latency_ms,
            correlation_id=row.correlation_id,
            plan_id=row.plan_id,
            workflow_execution_id=row.workflow_execution_id,
            agent_execution_id=row.agent_execution_id,
            idempotency_key=row.idempotency_key,
            request_fingerprint=row.request_fingerprint,
            error_code=row.error_code,
            error_message=row.error_message,
            completed_at=_ensure_utc(row.completed_at),
            created_at=_ensure_utc(row.created_at) or datetime.now(UTC),
            updated_at=_ensure_utc(row.updated_at) or datetime.now(UTC),
        )

    async def create_run(self, run: ResearchRunRecord) -> ResearchRunRecord:
        async with self._session_factory() as session:
            row = ResearchRun(
                research_id=run.research_id,
                tenant_id=run.tenant_id,
                requested_by=run.requested_by,
                question=run.question,
                scope=run.scope,
                required_output=run.required_output,
                max_sources=run.max_sources,
                status=run.status.value,
                summary=run.summary,
                contradictions_json=[c.model_dump(mode="json") for c in run.contradictions],
                unresolved_questions_json=list(run.unresolved_questions),
                follow_up_suggestions_json=list(run.follow_up_suggestions),
                warnings_json=list(run.warnings),
                correction_attempts=run.correction_attempts,
                sources_retrieved=run.sources_retrieved,
                sources_retained=run.sources_retained,
                retrieval_latency_ms=run.retrieval_latency_ms,
                synthesis_latency_ms=run.synthesis_latency_ms,
                correlation_id=run.correlation_id,
                plan_id=run.plan_id,
                workflow_execution_id=run.workflow_execution_id,
                agent_execution_id=run.agent_execution_id,
                idempotency_key=run.idempotency_key,
                request_fingerprint=run.request_fingerprint,
                error_code=run.error_code,
                error_message=run.error_message,
                completed_at=run.completed_at,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return self._row_to_run(row)

    async def update_run(self, run: ResearchRunRecord) -> ResearchRunRecord:
        async with self._session_factory() as session:
            stmt = select(ResearchRun).where(
                ResearchRun.research_id == run.research_id,
                ResearchRun.tenant_id == run.tenant_id,
            )
            res = await session.execute(stmt)
            row = res.scalar_one_or_none()
            if row is None:
                return await self.create_run(run)
            row.status = run.status.value
            row.summary = run.summary
            row.contradictions_json = [c.model_dump(mode="json") for c in run.contradictions]
            row.unresolved_questions_json = list(run.unresolved_questions)
            row.follow_up_suggestions_json = list(run.follow_up_suggestions)
            row.warnings_json = list(run.warnings)
            row.correction_attempts = run.correction_attempts
            row.sources_retrieved = run.sources_retrieved
            row.sources_retained = run.sources_retained
            row.retrieval_latency_ms = run.retrieval_latency_ms
            row.synthesis_latency_ms = run.synthesis_latency_ms
            row.agent_execution_id = run.agent_execution_id
            row.error_code = run.error_code
            row.error_message = run.error_message
            row.completed_at = run.completed_at
            await session.commit()
            await session.refresh(row)
            return self._row_to_run(row)

    async def get_run(self, research_id: str, tenant_id: str) -> ResearchRunRecord | None:
        async with self._session_factory() as session:
            stmt = select(ResearchRun).where(
                ResearchRun.research_id == research_id,
                ResearchRun.tenant_id == tenant_id,
            )
            res = await session.execute(stmt)
            row = res.scalar_one_or_none()
            return self._row_to_run(row) if row is not None else None

    async def list_runs(
        self,
        tenant_id: str,
        *,
        status: ResearchStatus | None = None,
        limit: int = 50,
    ) -> list[ResearchRunRecord]:
        async with self._session_factory() as session:
            stmt = select(ResearchRun).where(ResearchRun.tenant_id == tenant_id)
            if status is not None:
                stmt = stmt.where(ResearchRun.status == status.value)
            stmt = stmt.order_by(ResearchRun.created_at.desc()).limit(limit)
            res = await session.execute(stmt)
            return [self._row_to_run(r) for r in res.scalars().all()]

    async def find_by_idempotency_key(
        self,
        tenant_id: str,
        requested_by: str,
        idempotency_key: str,
    ) -> ResearchRunRecord | None:
        async with self._session_factory() as session:
            stmt = (
                select(ResearchRun)
                .where(
                    ResearchRun.tenant_id == tenant_id,
                    ResearchRun.requested_by == requested_by,
                    ResearchRun.idempotency_key == idempotency_key,
                )
                .order_by(ResearchRun.created_at.desc())
                .limit(1)
            )
            res = await session.execute(stmt)
            row = res.scalar_one_or_none()
            return self._row_to_run(row) if row is not None else None

    async def save_evidence(
        self,
        research_id: str,
        tenant_id: str,
        evidence: list[EvidenceItem],
    ) -> None:
        async with self._session_factory() as session:
            await session.execute(
                delete(ResearchEvidence).where(
                    ResearchEvidence.research_id == research_id,
                    ResearchEvidence.tenant_id == tenant_id,
                )
            )
            for idx, item in enumerate(evidence):
                session.add(
                    ResearchEvidence(
                        record_pk=f"{research_id}:{item.evidence_id}:{idx}",
                        research_id=research_id,
                        tenant_id=tenant_id,
                        evidence_id=item.evidence_id,
                        source_id=item.source_id,
                        source_title=item.source_title,
                        passage=item.passage,
                        retrieval_reference=item.retrieval_reference,
                        relevance_score=item.relevance_score,
                        document_date=item.document_date,
                        access_tier=item.access_tier,
                        metadata_json=dict(item.metadata),
                    )
                )
            await session.commit()

    async def get_evidence(self, research_id: str, tenant_id: str) -> list[EvidenceItem]:
        async with self._session_factory() as session:
            stmt = (
                select(ResearchEvidence)
                .where(
                    ResearchEvidence.research_id == research_id,
                    ResearchEvidence.tenant_id == tenant_id,
                )
                .order_by(ResearchEvidence.evidence_id.asc())
            )
            res = await session.execute(stmt)
            items: list[EvidenceItem] = []
            for row in res.scalars().all():
                items.append(
                    EvidenceItem(
                        evidence_id=row.evidence_id,
                        source_id=row.source_id,
                        source_title=row.source_title,
                        passage=row.passage,
                        retrieval_reference=row.retrieval_reference,
                        relevance_score=row.relevance_score,
                        document_date=row.document_date,
                        access_tier=row.access_tier,  # type: ignore[arg-type]
                        metadata=dict(row.metadata_json or {}),
                    )
                )
            return items

    async def save_findings(
        self,
        research_id: str,
        tenant_id: str,
        findings: list[ResearchFinding],
    ) -> None:
        async with self._session_factory() as session:
            await session.execute(
                delete(ResearchFindingModel).where(
                    ResearchFindingModel.research_id == research_id,
                    ResearchFindingModel.tenant_id == tenant_id,
                )
            )
            for idx, finding in enumerate(findings):
                session.add(
                    ResearchFindingModel(
                        finding_pk=f"{research_id}:{finding.finding_id}:{idx}",
                        research_id=research_id,
                        tenant_id=tenant_id,
                        finding_id=finding.finding_id,
                        claim=finding.claim,
                        claim_type=finding.claim_type,
                        evidence_ids_json=list(finding.evidence_ids),
                        confidence=finding.confidence,
                        limitations_json=list(finding.limitations),
                        has_contradiction=finding.has_contradiction,
                    )
                )
            await session.commit()

    async def get_findings(self, research_id: str, tenant_id: str) -> list[ResearchFinding]:
        async with self._session_factory() as session:
            stmt = (
                select(ResearchFindingModel)
                .where(
                    ResearchFindingModel.research_id == research_id,
                    ResearchFindingModel.tenant_id == tenant_id,
                )
                .order_by(ResearchFindingModel.finding_id.asc())
            )
            res = await session.execute(stmt)
            items: list[ResearchFinding] = []
            for row in res.scalars().all():
                items.append(
                    ResearchFinding(
                        finding_id=row.finding_id,
                        claim=row.claim,
                        claim_type=row.claim_type,  # type: ignore[arg-type]
                        evidence_ids=list(row.evidence_ids_json or []),
                        confidence=row.confidence,  # type: ignore[arg-type]
                        limitations=list(row.limitations_json or []),
                        has_contradiction=bool(row.has_contradiction),
                    )
                )
            return items

    async def append_event(self, event: ResearchEventRecord) -> ResearchEventRecord:
        async with self._session_factory() as session:
            row = ResearchEvent(
                event_id=event.event_id,
                research_id=event.research_id,
                tenant_id=event.tenant_id,
                event_type=event.event_type,
                correlation_id=event.correlation_id,
                details_json=dict(event.details),
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return ResearchEventRecord(
                event_id=row.event_id,
                research_id=row.research_id,
                tenant_id=row.tenant_id,
                event_type=row.event_type,
                correlation_id=row.correlation_id,
                details=dict(row.details_json or {}),
                created_at=_ensure_utc(row.created_at) or datetime.now(UTC),
            )

    async def list_events(self, research_id: str, tenant_id: str) -> list[ResearchEventRecord]:
        async with self._session_factory() as session:
            stmt = (
                select(ResearchEvent)
                .where(
                    ResearchEvent.research_id == research_id,
                    ResearchEvent.tenant_id == tenant_id,
                )
                .order_by(ResearchEvent.created_at.asc())
            )
            res = await session.execute(stmt)
            return [
                ResearchEventRecord(
                    event_id=r.event_id,
                    research_id=r.research_id,
                    tenant_id=r.tenant_id,
                    event_type=r.event_type,
                    correlation_id=r.correlation_id,
                    details=dict(r.details_json or {}),
                    created_at=_ensure_utc(r.created_at) or datetime.now(UTC),
                )
                for r in res.scalars().all()
            ]
