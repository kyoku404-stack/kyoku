"""KEEP Phase 4.8 — Collaboration Repository Interfaces & Implementations.

Provides repository interfaces and an in-memory implementation for persisting
collaboration sessions, tasks, messages, findings, reviews, and conflicts.

Specification: devdocs/p4/p4.8.txt
Owner: Member 1 (Contracts & Session Management)
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.app.agents.collaboration.contracts import (
    CollaborationConflict,
    CollaborationFinding,
    CollaborationMessage,
    CollaborationSession,
    CollaborationTask,
    ConflictStatus,
    ReviewOutcome,
    ReviewResult,
    SessionStatus,
    TaskStatus,
)
from backend.app.models.agent_collaboration import (
    CollaborationConflictModel,
    CollaborationFindingModel,
    CollaborationMessageModel,
    CollaborationReviewModel,
    CollaborationSessionModel,
    CollaborationTaskModel,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseCollaborationRepository(ABC):
    """Abstract interface for multi-tenant collaboration persistence."""

    # Session operations
    @abstractmethod
    async def create_session(self, session: CollaborationSession) -> CollaborationSession:
        """Persists a new collaboration session."""
        ...

    @abstractmethod
    async def get_session(self, session_id: str, tenant_id: str) -> CollaborationSession | None:
        """Retrieves a session ensuring tenant isolation."""
        ...

    @abstractmethod
    async def update_session(self, session: CollaborationSession) -> CollaborationSession:
        """Updates an existing collaboration session."""
        ...

    @abstractmethod
    async def list_sessions(
        self, tenant_id: str, status: SessionStatus | None = None, limit: int = 50
    ) -> list[CollaborationSession]:
        """Lists sessions for a tenant, optionally filtered by status."""
        ...

    # Task operations
    @abstractmethod
    async def create_task(self, task: CollaborationTask) -> CollaborationTask:
        """Persists a new collaboration task."""
        ...

    @abstractmethod
    async def get_task(self, task_id: str, tenant_id: str) -> CollaborationTask | None:
        """Retrieves a task ensuring tenant isolation."""
        ...

    @abstractmethod
    async def update_task(self, task: CollaborationTask) -> CollaborationTask:
        """Updates an existing collaboration task."""
        ...

    @abstractmethod
    async def list_tasks(self, session_id: str, tenant_id: str) -> list[CollaborationTask]:
        """Lists all tasks for a session under tenant isolation."""
        ...

    # Message operations
    @abstractmethod
    async def create_message(self, message: CollaborationMessage) -> CollaborationMessage:
        """Appends a new validated inter-agent message."""
        ...

    @abstractmethod
    async def list_messages(
        self, session_id: str, tenant_id: str, task_id: str | None = None, limit: int = 50
    ) -> list[CollaborationMessage]:
        """Lists messages for a session/task under tenant isolation."""
        ...

    # Finding operations
    @abstractmethod
    async def create_finding(self, finding: CollaborationFinding) -> CollaborationFinding:
        """Persists a new evidence-backed finding."""
        ...

    @abstractmethod
    async def get_finding(self, finding_id: str, tenant_id: str) -> CollaborationFinding | None:
        """Retrieves a finding ensuring tenant isolation."""
        ...

    @abstractmethod
    async def list_findings(
        self, session_id: str, tenant_id: str, task_id: str | None = None
    ) -> list[CollaborationFinding]:
        """Lists findings for a session/task under tenant isolation."""
        ...

    # Review operations
    @abstractmethod
    async def create_review(self, review: ReviewResult) -> ReviewResult:
        """Persists a new peer review outcome."""
        ...

    @abstractmethod
    async def list_reviews(self, session_id: str, tenant_id: str) -> list[ReviewResult]:
        """Lists peer reviews for a session under tenant isolation."""
        ...

    # Conflict operations
    @abstractmethod
    async def create_conflict(self, conflict: CollaborationConflict) -> CollaborationConflict:
        """Persists a new conflict record."""
        ...

    @abstractmethod
    async def get_conflict(self, conflict_id: str, tenant_id: str) -> CollaborationConflict | None:
        """Retrieves a conflict ensuring tenant isolation."""
        ...

    @abstractmethod
    async def update_conflict(self, conflict: CollaborationConflict) -> CollaborationConflict:
        """Updates an existing conflict."""
        ...

    @abstractmethod
    async def list_conflicts(
        self, session_id: str, tenant_id: str, status: ConflictStatus | None = None
    ) -> list[CollaborationConflict]:
        """Lists conflicts for a session under tenant isolation."""
        ...


class InMemoryCollaborationRepository(BaseCollaborationRepository):
    """In-memory multi-tenant implementation for unit testing and local simulation."""

    def __init__(self) -> None:
        self.sessions: dict[tuple[str, str], CollaborationSession] = {}  # (tenant_id, session_id)
        self.tasks: dict[tuple[str, str], CollaborationTask] = {}  # (tenant_id, task_id)
        self.messages: list[CollaborationMessage] = []
        self.findings: dict[tuple[str, str], CollaborationFinding] = {}  # (tenant_id, finding_id)
        self.reviews: list[ReviewResult] = []
        self.conflicts: dict[tuple[str, str], CollaborationConflict] = {}  # (tenant_id, conflict_id)

    async def create_session(self, session: CollaborationSession) -> CollaborationSession:
        self.sessions[(session.tenant_id, session.session_id)] = session
        return session

    async def get_session(self, session_id: str, tenant_id: str) -> CollaborationSession | None:
        return self.sessions.get((tenant_id, session_id))

    async def update_session(self, session: CollaborationSession) -> CollaborationSession:
        self.sessions[(session.tenant_id, session.session_id)] = session
        return session

    async def list_sessions(
        self, tenant_id: str, status: SessionStatus | None = None, limit: int = 50
    ) -> list[CollaborationSession]:
        results = [
            s for (t, _), s in self.sessions.items()
            if t == tenant_id and (status is None or s.status == status)
        ]
        results.sort(key=lambda s: s.created_at, reverse=True)
        return results[:limit]

    async def create_task(self, task: CollaborationTask) -> CollaborationTask:
        self.tasks[(task.tenant_id, task.task_id)] = task
        return task

    async def get_task(self, task_id: str, tenant_id: str) -> CollaborationTask | None:
        return self.tasks.get((tenant_id, task_id))

    async def update_task(self, task: CollaborationTask) -> CollaborationTask:
        self.tasks[(task.tenant_id, task.task_id)] = task
        return task

    async def list_tasks(self, session_id: str, tenant_id: str) -> list[CollaborationTask]:
        return [
            t for (ten, _), t in self.tasks.items()
            if ten == tenant_id and t.session_id == session_id
        ]

    async def create_message(self, message: CollaborationMessage) -> CollaborationMessage:
        self.messages.append(message)
        return message

    async def list_messages(
        self, session_id: str, tenant_id: str, task_id: str | None = None, limit: int = 50
    ) -> list[CollaborationMessage]:
        results = [
            m for m in self.messages
            if m.tenant_id == tenant_id and m.session_id == session_id and (task_id is None or m.task_id == task_id)
        ]
        results.sort(key=lambda m: m.created_at)
        return results[:limit]

    async def create_finding(self, finding: CollaborationFinding) -> CollaborationFinding:
        self.findings[(finding.tenant_id, finding.finding_id)] = finding
        return finding

    async def get_finding(self, finding_id: str, tenant_id: str) -> CollaborationFinding | None:
        return self.findings.get((tenant_id, finding_id))

    async def list_findings(
        self, session_id: str, tenant_id: str, task_id: str | None = None
    ) -> list[CollaborationFinding]:
        results = [
            f for (ten, _), f in self.findings.items()
            if ten == tenant_id and f.session_id == session_id and (task_id is None or f.task_id == task_id)
        ]
        results.sort(key=lambda f: f.created_at)
        return results

    async def create_review(self, review: ReviewResult) -> ReviewResult:
        self.reviews.append(review)
        return review

    async def list_reviews(self, session_id: str, tenant_id: str) -> list[ReviewResult]:
        results = [
            r for r in self.reviews
            if r.tenant_id == tenant_id and r.session_id == session_id
        ]
        results.sort(key=lambda r: r.created_at)
        return results

    async def create_conflict(self, conflict: CollaborationConflict) -> CollaborationConflict:
        self.conflicts[(conflict.tenant_id, conflict.conflict_id)] = conflict
        return conflict

    async def get_conflict(self, conflict_id: str, tenant_id: str) -> CollaborationConflict | None:
        return self.conflicts.get((tenant_id, conflict_id))

    async def update_conflict(self, conflict: CollaborationConflict) -> CollaborationConflict:
        self.conflicts[(conflict.tenant_id, conflict.conflict_id)] = conflict
        return conflict

    async def list_conflicts(
        self, session_id: str, tenant_id: str, status: ConflictStatus | None = None
    ) -> list[CollaborationConflict]:
        results = [
            c for (ten, _), c in self.conflicts.items()
            if ten == tenant_id and c.session_id == session_id and (status is None or c.status == status)
        ]
        results.sort(key=lambda c: c.created_at)
        return results


class SqlAlchemyCollaborationRepository(BaseCollaborationRepository):
    """Database repository implementing BaseCollaborationRepository using SQLAlchemy ORM."""

    def __init__(self, session: AsyncSession | None = None) -> None:
        self._session = session
        self._fallback = InMemoryCollaborationRepository()

    @staticmethod
    def _model_to_session(model: CollaborationSessionModel) -> CollaborationSession:
        return CollaborationSession(
            session_id=model.session_id,
            tenant_id=model.tenant_id,
            requested_by=model.requested_by,
            objective=model.objective,
            status=SessionStatus(model.status),
            workflow_id=model.workflow_id,
            max_agents=model.max_agents,
            require_review=model.require_review,
            max_revisions=model.max_revisions,
            summary=model.summary,
            report=model.report or {},
            created_at=model.created_at,
            completed_at=model.completed_at,
        )

    @staticmethod
    def _model_to_task(model: CollaborationTaskModel) -> CollaborationTask:
        return CollaborationTask(
            task_id=model.task_id,
            session_id=model.session_id,
            tenant_id=model.tenant_id,
            agent_id=model.agent_id,
            title=model.title,
            status=TaskStatus(model.status),
            attempt=model.attempt,
            max_attempts=model.max_attempts,
            dependencies=model.dependencies or [],
            inputs=model.inputs or {},
            outputs=model.outputs or {},
            error_code=model.error_code,
            created_at=model.created_at,
            completed_at=model.completed_at,
        )

    @staticmethod
    def _model_to_message(model: CollaborationMessageModel) -> CollaborationMessage:
        return CollaborationMessage(
            message_id=model.message_id,
            session_id=model.session_id,
            tenant_id=model.tenant_id,
            sender_id=model.sender_id,
            recipient_id=model.recipient_id,
            task_id=model.task_id,
            message_type=model.message_type,  # type: ignore[arg-type]
            payload=model.payload or {},
            correlation_id=model.correlation_id,
            created_at=model.created_at,
        )

    @staticmethod
    def _model_to_finding(model: CollaborationFindingModel) -> CollaborationFinding:
        return CollaborationFinding(
            finding_id=model.finding_id,
            session_id=model.session_id,
            tenant_id=model.tenant_id,
            task_id=model.task_id,
            claim=model.claim,
            evidence_refs=model.evidence_refs or [],
            provenance=model.provenance or {},
            limitations=model.limitations,
            created_at=model.created_at,
        )

    @staticmethod
    def _model_to_review(model: CollaborationReviewModel) -> ReviewResult:
        return ReviewResult(
            review_id=model.review_id,
            session_id=model.session_id,
            tenant_id=model.tenant_id,
            reviewer_id=model.reviewer_id,
            finding_ids=model.finding_ids or [],
            outcome=ReviewOutcome(model.outcome),
            reasons=model.reasons or [],
            unsupported_claims=model.unsupported_claims or [],
            missing_evidence=model.missing_evidence or [],
            created_at=model.created_at,
        )

    @staticmethod
    def _model_to_conflict(model: CollaborationConflictModel) -> CollaborationConflict:
        return CollaborationConflict(
            conflict_id=model.conflict_id,
            session_id=model.session_id,
            tenant_id=model.tenant_id,
            finding_ids=model.finding_ids or [],
            status=ConflictStatus(model.status),
            description=model.description,
            resolution=model.resolution,
            resolved_by=model.resolved_by,
            resolved_at=model.resolved_at,
            created_at=model.created_at,
        )

    async def create_session(self, session: CollaborationSession) -> CollaborationSession:
        if self._session is None:
            return await self._fallback.create_session(session)
        model = CollaborationSessionModel(
            session_id=session.session_id,
            tenant_id=session.tenant_id,
            requested_by=session.requested_by,
            objective=session.objective,
            status=session.status.value,
            workflow_id=session.workflow_id,
            max_agents=session.max_agents,
            require_review=session.require_review,
            max_revisions=session.max_revisions,
            summary=session.summary,
            report=session.report,
            created_at=session.created_at,
            completed_at=session.completed_at,
        )
        self._session.add(model)
        await self._session.flush()
        return session

    async def get_session(self, session_id: str, tenant_id: str) -> CollaborationSession | None:
        if self._session is None:
            return await self._fallback.get_session(session_id, tenant_id)
        stmt = select(CollaborationSessionModel).where(
            CollaborationSessionModel.session_id == session_id,
            CollaborationSessionModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_session(model) if model else None

    async def update_session(self, session: CollaborationSession) -> CollaborationSession:
        if self._session is None:
            return await self._fallback.update_session(session)
        stmt = select(CollaborationSessionModel).where(
            CollaborationSessionModel.session_id == session.session_id,
            CollaborationSessionModel.tenant_id == session.tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.status = session.status.value
            model.summary = session.summary
            model.report = session.report
            model.completed_at = session.completed_at
            await self._session.flush()
        return session

    async def list_sessions(
        self, tenant_id: str, status: SessionStatus | None = None, limit: int = 50
    ) -> list[CollaborationSession]:
        if self._session is None:
            return await self._fallback.list_sessions(tenant_id, status, limit)
        stmt = select(CollaborationSessionModel).where(CollaborationSessionModel.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(CollaborationSessionModel.status == status.value)
        stmt = stmt.order_by(CollaborationSessionModel.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return [self._model_to_session(m) for m in result.scalars().all()]

    async def create_task(self, task: CollaborationTask) -> CollaborationTask:
        if self._session is None:
            return await self._fallback.create_task(task)
        model = CollaborationTaskModel(
            task_id=task.task_id,
            session_id=task.session_id,
            tenant_id=task.tenant_id,
            agent_id=task.agent_id,
            title=task.title,
            status=task.status.value,
            attempt=task.attempt,
            max_attempts=task.max_attempts,
            dependencies=task.dependencies,
            inputs=task.inputs,
            outputs=task.outputs,
            error_code=task.error_code,
            created_at=task.created_at,
            completed_at=task.completed_at,
        )
        self._session.add(model)
        await self._session.flush()
        return task

    async def get_task(self, task_id: str, tenant_id: str) -> CollaborationTask | None:
        if self._session is None:
            return await self._fallback.get_task(task_id, tenant_id)
        stmt = select(CollaborationTaskModel).where(
            CollaborationTaskModel.task_id == task_id,
            CollaborationTaskModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_task(model) if model else None

    async def update_task(self, task: CollaborationTask) -> CollaborationTask:
        if self._session is None:
            return await self._fallback.update_task(task)
        stmt = select(CollaborationTaskModel).where(
            CollaborationTaskModel.task_id == task.task_id,
            CollaborationTaskModel.tenant_id == task.tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.agent_id = task.agent_id
            model.status = task.status.value
            model.attempt = task.attempt
            model.outputs = task.outputs
            model.error_code = task.error_code
            model.completed_at = task.completed_at
            await self._session.flush()
        return task

    async def list_tasks(self, session_id: str, tenant_id: str) -> list[CollaborationTask]:
        if self._session is None:
            return await self._fallback.list_tasks(session_id, tenant_id)
        stmt = select(CollaborationTaskModel).where(
            CollaborationTaskModel.session_id == session_id,
            CollaborationTaskModel.tenant_id == tenant_id,
        ).order_by(CollaborationTaskModel.created_at.asc())
        result = await self._session.execute(stmt)
        return [self._model_to_task(m) for m in result.scalars().all()]

    async def create_message(self, message: CollaborationMessage) -> CollaborationMessage:
        if self._session is None:
            return await self._fallback.create_message(message)
        model = CollaborationMessageModel(
            message_id=message.message_id,
            session_id=message.session_id,
            tenant_id=message.tenant_id,
            sender_id=message.sender_id,
            recipient_id=message.recipient_id,
            task_id=message.task_id,
            message_type=message.message_type.value if hasattr(message.message_type, "value") else str(message.message_type),
            payload=message.payload,
            correlation_id=message.correlation_id,
            created_at=message.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return message

    async def list_messages(
        self, session_id: str, tenant_id: str, task_id: str | None = None, limit: int = 50
    ) -> list[CollaborationMessage]:
        if self._session is None:
            return await self._fallback.list_messages(session_id, tenant_id, task_id, limit)
        stmt = select(CollaborationMessageModel).where(
            CollaborationMessageModel.session_id == session_id,
            CollaborationMessageModel.tenant_id == tenant_id,
        )
        if task_id:
            stmt = stmt.where(CollaborationMessageModel.task_id == task_id)
        stmt = stmt.order_by(CollaborationMessageModel.created_at.asc()).limit(limit)
        result = await self._session.execute(stmt)
        return [self._model_to_message(m) for m in result.scalars().all()]

    async def create_finding(self, finding: CollaborationFinding) -> CollaborationFinding:
        if self._session is None:
            return await self._fallback.create_finding(finding)
        model = CollaborationFindingModel(
            finding_id=finding.finding_id,
            session_id=finding.session_id,
            tenant_id=finding.tenant_id,
            task_id=finding.task_id,
            claim=finding.claim,
            evidence_refs=finding.evidence_refs,
            provenance=finding.provenance,
            limitations=finding.limitations,
            created_at=finding.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return finding

    async def get_finding(self, finding_id: str, tenant_id: str) -> CollaborationFinding | None:
        if self._session is None:
            return await self._fallback.get_finding(finding_id, tenant_id)
        stmt = select(CollaborationFindingModel).where(
            CollaborationFindingModel.finding_id == finding_id,
            CollaborationFindingModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_finding(model) if model else None

    async def list_findings(
        self, session_id: str, tenant_id: str, task_id: str | None = None
    ) -> list[CollaborationFinding]:
        if self._session is None:
            return await self._fallback.list_findings(session_id, tenant_id, task_id)
        stmt = select(CollaborationFindingModel).where(
            CollaborationFindingModel.session_id == session_id,
            CollaborationFindingModel.tenant_id == tenant_id,
        )
        if task_id:
            stmt = stmt.where(CollaborationFindingModel.task_id == task_id)
        stmt = stmt.order_by(CollaborationFindingModel.created_at.asc())
        result = await self._session.execute(stmt)
        return [self._model_to_finding(m) for m in result.scalars().all()]

    async def create_review(self, review: ReviewResult) -> ReviewResult:
        if self._session is None:
            return await self._fallback.create_review(review)
        model = CollaborationReviewModel(
            review_id=review.review_id,
            session_id=review.session_id,
            tenant_id=review.tenant_id,
            reviewer_id=review.reviewer_id,
            finding_ids=review.finding_ids,
            outcome=review.outcome.value if hasattr(review.outcome, "value") else str(review.outcome),
            reasons=review.reasons,
            unsupported_claims=review.unsupported_claims,
            missing_evidence=review.missing_evidence,
            created_at=review.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return review

    async def list_reviews(self, session_id: str, tenant_id: str) -> list[ReviewResult]:
        if self._session is None:
            return await self._fallback.list_reviews(session_id, tenant_id)
        stmt = select(CollaborationReviewModel).where(
            CollaborationReviewModel.session_id == session_id,
            CollaborationReviewModel.tenant_id == tenant_id,
        ).order_by(CollaborationReviewModel.created_at.asc())
        result = await self._session.execute(stmt)
        return [self._model_to_review(m) for m in result.scalars().all()]

    async def create_conflict(self, conflict: CollaborationConflict) -> CollaborationConflict:
        if self._session is None:
            return await self._fallback.create_conflict(conflict)
        model = CollaborationConflictModel(
            conflict_id=conflict.conflict_id,
            session_id=conflict.session_id,
            tenant_id=conflict.tenant_id,
            finding_ids=conflict.finding_ids,
            status=conflict.status.value if hasattr(conflict.status, "value") else str(conflict.status),
            description=conflict.description,
            resolution=conflict.resolution,
            resolved_by=conflict.resolved_by,
            resolved_at=conflict.resolved_at,
            created_at=conflict.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return conflict

    async def get_conflict(self, conflict_id: str, tenant_id: str) -> CollaborationConflict | None:
        if self._session is None:
            return await self._fallback.get_conflict(conflict_id, tenant_id)
        stmt = select(CollaborationConflictModel).where(
            CollaborationConflictModel.conflict_id == conflict_id,
            CollaborationConflictModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_conflict(model) if model else None

    async def update_conflict(self, conflict: CollaborationConflict) -> CollaborationConflict:
        if self._session is None:
            return await self._fallback.update_conflict(conflict)
        stmt = select(CollaborationConflictModel).where(
            CollaborationConflictModel.conflict_id == conflict.conflict_id,
            CollaborationConflictModel.tenant_id == conflict.tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.status = conflict.status.value if hasattr(conflict.status, "value") else str(conflict.status)
            model.resolution = conflict.resolution
            model.resolved_by = conflict.resolved_by
            model.resolved_at = conflict.resolved_at
            await self._session.flush()
        return conflict

    async def list_conflicts(
        self, session_id: str, tenant_id: str, status: ConflictStatus | None = None
    ) -> list[CollaborationConflict]:
        if self._session is None:
            return await self._fallback.list_conflicts(session_id, tenant_id, status)
        stmt = select(CollaborationConflictModel).where(
            CollaborationConflictModel.session_id == session_id,
            CollaborationConflictModel.tenant_id == tenant_id,
        )
        if status:
            stmt = stmt.where(CollaborationConflictModel.status == status.value)
        stmt = stmt.order_by(CollaborationConflictModel.created_at.asc())
        result = await self._session.execute(stmt)
        return [self._model_to_conflict(m) for m in result.scalars().all()]

