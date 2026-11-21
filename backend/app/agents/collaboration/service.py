"""KEEP Phase 4.8 — Multi-Agent Collaboration Service.

Unified service interface providing session management, task coordination,
messaging, peer reviews, and conflict handling.

Specification: devdocs/p4/p4.8.txt
Owner: Member 1 (Contracts & Session Management)
"""

from __future__ import annotations

import datetime
import logging

from backend.app.agents.collaboration.contracts import (
    CancelSessionRequest,
    CollaborationConflict,
    CollaborationFinding,
    CollaborationMessage,
    CollaborationReport,
    CollaborationRequest,
    CollaborationSecurityContext,
    CollaborationSession,
    CollaborationTask,
    ConflictResolutionRequest,
    ConflictStatus,
    ReviewResult,
)
from backend.app.agents.collaboration.repository import (
    BaseCollaborationRepository,
    InMemoryCollaborationRepository,
)
from backend.app.agents.collaboration.session_manager import SessionManager
from backend.app.agents.errors import (
    CollaborationConflictUnresolvedError,
)
from backend.app.agents.registry import AgentRegistry

logger = logging.getLogger(__name__)


class CollaborationService:
    """Core domain service orchestrating multi-agent collaboration sessions."""

    def __init__(
        self,
        repository: BaseCollaborationRepository | None = None,
        registry: AgentRegistry | None = None,
        session_manager: SessionManager | None = None,
    ) -> None:
        self.repository = repository or InMemoryCollaborationRepository()
        self.registry = registry
        self.session_manager = session_manager or SessionManager(
            repository=self.repository,
            registry=self.registry,
        )

    async def start_session(
        self,
        request: CollaborationRequest,
        security_context: CollaborationSecurityContext,
    ) -> CollaborationSession:
        """Starts a new multi-agent collaboration session."""
        return await self.session_manager.create_session(request, security_context)

    async def get_session(
        self,
        session_id: str,
        security_context: CollaborationSecurityContext,
    ) -> CollaborationSession:
        """Retrieves an existing collaboration session."""
        return await self.session_manager.get_session(session_id, security_context)

    async def cancel_session(
        self,
        session_id: str,
        request: CancelSessionRequest,
        security_context: CollaborationSecurityContext,
    ) -> CollaborationSession:
        """Cancels an ongoing collaboration session."""
        return await self.session_manager.cancel_session(session_id, request, security_context)

    async def list_tasks(
        self,
        session_id: str,
        security_context: CollaborationSecurityContext,
    ) -> list[CollaborationTask]:
        """Lists all tasks registered for a session under tenant isolation."""
        # Ensure session exists and caller belongs to same tenant
        await self.get_session(session_id, security_context)
        return await self.repository.list_tasks(session_id, security_context.tenant_id)

    async def list_messages(
        self,
        session_id: str,
        security_context: CollaborationSecurityContext,
        task_id: str | None = None,
        limit: int = 50,
    ) -> list[CollaborationMessage]:
        """Lists messages for a session under tenant isolation."""
        await self.get_session(session_id, security_context)
        return await self.repository.list_messages(
            session_id=session_id,
            tenant_id=security_context.tenant_id,
            task_id=task_id,
            limit=limit,
        )

    async def list_findings(
        self,
        session_id: str,
        security_context: CollaborationSecurityContext,
        task_id: str | None = None,
    ) -> list[CollaborationFinding]:
        """Lists findings produced within a session under tenant isolation."""
        await self.get_session(session_id, security_context)
        return await self.repository.list_findings(
            session_id=session_id,
            tenant_id=security_context.tenant_id,
            task_id=task_id,
        )

    async def list_reviews(
        self,
        session_id: str,
        security_context: CollaborationSecurityContext,
    ) -> list[ReviewResult]:
        """Lists peer review outcomes for a session under tenant isolation."""
        await self.get_session(session_id, security_context)
        return await self.repository.list_reviews(session_id, security_context.tenant_id)

    async def get_report(
        self,
        session_id: str,
        security_context: CollaborationSecurityContext,
    ) -> CollaborationReport:
        """Synthesizes and retrieves the complete collaboration report."""
        return await self.session_manager.compile_report(session_id, security_context)

    async def resolve_conflict(
        self,
        session_id: str,
        request: ConflictResolutionRequest,
        security_context: CollaborationSecurityContext,
    ) -> CollaborationConflict:
        """Applies human intervention or policy resolution to an escalated conflict."""
        await self.get_session(session_id, security_context)
        conflict = await self.repository.get_conflict(
            conflict_id=request.conflict_id,
            tenant_id=security_context.tenant_id,
        )
        if not conflict:
            raise CollaborationConflictUnresolvedError(
                f"Conflict '{request.conflict_id}' not found in session '{session_id}'."
            )

        conflict.status = ConflictStatus.RESOLVED
        conflict.resolution = request.resolution
        conflict.resolved_by = security_context.user_id
        conflict.resolved_at = datetime.datetime.now(datetime.UTC)
        return await self.repository.update_conflict(conflict)
