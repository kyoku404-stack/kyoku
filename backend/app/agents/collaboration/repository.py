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
    ReviewResult,
    SessionStatus,
)


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
