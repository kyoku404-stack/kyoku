"""KEEP Phase 4.8 — Collaboration Session Manager.

Manages session lifecycle, task initializations, state transitions, security
validation, and final report compilation.

Specification: devdocs/p4/p4.8.txt
Owner: Member 1 (Contracts & Session Management)
"""

from __future__ import annotations

import datetime
import logging
from typing import Any

from backend.app.agents.collaboration.contracts import (
    CancelSessionRequest,
    CollaborationReport,
    CollaborationRequest,
    CollaborationSecurityContext,
    CollaborationSession,
    CollaborationTask,
    ConflictStatus,
    SessionStatus,
    TaskStatus,
    generate_collaboration_session_id,
    generate_collaboration_task_id,
)
from backend.app.agents.collaboration.repository import BaseCollaborationRepository
from backend.app.agents.errors import (
    CollaborationAccessDeniedError,
    CollaborationSessionCancelledError,
    CollaborationSessionCompletedError,
    CollaborationSessionNotFoundError,
)
from backend.app.agents.registry import AgentRegistry

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages the creation, transitions, and reporting of multi-agent collaboration sessions."""

    def __init__(
        self,
        repository: BaseCollaborationRepository,
        registry: AgentRegistry | None = None,
    ) -> None:
        self.repository = repository
        self.registry = registry

    async def create_session(
        self,
        request: CollaborationRequest,
        security_context: CollaborationSecurityContext,
    ) -> CollaborationSession:
        """Initializes a new collaboration session and registers initial tasks."""
        if not security_context.tenant_id:
            raise CollaborationAccessDeniedError("Missing tenant context.")

        session_id = generate_collaboration_session_id()

        # Validate agent count ceiling
        if len(request.agent_ids) > request.max_agents:
            raise ValueError(
                f"Agent count ({len(request.agent_ids)}) exceeds maximum allowed ({request.max_agents})."
            )

        # Validate agent registry presence if registry provided
        if self.registry:
            for agent_id in request.agent_ids:
                if not self.registry.is_registered(agent_id) and agent_id not in (
                    "coordinator", "reviewer", "critic", "synthesizer"
                ):
                    logger.warning("Agent '%s' not registered in agent registry.", agent_id)

        session = CollaborationSession(
            session_id=session_id,
            tenant_id=security_context.tenant_id,
            requested_by=security_context.user_id,
            objective=request.objective,
            status=SessionStatus.PLANNING,
            workflow_id=request.workflow_id,
            max_agents=request.max_agents,
            require_review=request.require_review,
            max_revisions=request.max_revisions,
            summary=None,
            report={},
        )
        await self.repository.create_session(session)

        # Initialize tasks
        for spec in request.tasks:
            task_id = spec.task_id or generate_collaboration_task_id()
            task = CollaborationTask(
                task_id=task_id,
                session_id=session_id,
                tenant_id=security_context.tenant_id,
                agent_id=spec.agent_id,
                title=spec.title,
                status=TaskStatus.PENDING,
                attempt=0,
                max_attempts=spec.max_attempts,
                dependencies=list(spec.dependencies),
                inputs=dict(spec.inputs),
                outputs={},
            )
            await self.repository.create_task(task)

        logger.info(
            "Created collaboration session %s for tenant %s with %d tasks.",
            session_id,
            security_context.tenant_id,
            len(request.tasks),
        )
        return session

    async def get_session(
        self,
        session_id: str,
        security_context: CollaborationSecurityContext,
    ) -> CollaborationSession:
        """Retrieves a collaboration session with tenant isolation enforcement."""
        session = await self.repository.get_session(session_id, security_context.tenant_id)
        if not session:
            # Check if session exists in another tenant for isolation error
            # or treat as not found
            raise CollaborationSessionNotFoundError(session_id)
        return session

    async def transition_status(
        self,
        session_id: str,
        new_status: SessionStatus,
        security_context: CollaborationSecurityContext,
        summary: str | None = None,
        report_data: dict[str, Any] | None = None,
    ) -> CollaborationSession:
        """Transitions session to a new lifecycle status with validation."""
        session = await self.get_session(session_id, security_context)

        if session.status in (SessionStatus.COMPLETED, SessionStatus.CANCELLED, SessionStatus.FAILED):
            if session.status == SessionStatus.COMPLETED:
                raise CollaborationSessionCompletedError(session_id)
            if session.status == SessionStatus.CANCELLED:
                raise CollaborationSessionCancelledError(session_id)
            raise ValueError(f"Cannot transition terminal session '{session_id}' from {session.status}.")

        session.status = new_status
        if summary is not None:
            session.summary = summary
        if report_data is not None:
            session.report = report_data
        if new_status in (SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.CANCELLED):
            session.completed_at = datetime.datetime.now(datetime.UTC)

        await self.repository.update_session(session)
        logger.info("Session %s transitioned to %s.", session_id, new_status.value)
        return session

    async def cancel_session(
        self,
        session_id: str,
        request: CancelSessionRequest,
        security_context: CollaborationSecurityContext,
    ) -> CollaborationSession:
        """Aborts an active collaboration session."""
        session = await self.get_session(session_id, security_context)

        if session.status == SessionStatus.COMPLETED:
            raise CollaborationSessionCompletedError(session_id)
        if session.status == SessionStatus.CANCELLED:
            return session

        session.status = SessionStatus.CANCELLED
        session.completed_at = datetime.datetime.now(datetime.UTC)
        session.summary = f"Cancelled: {request.reason}"

        await self.repository.update_session(session)

        # Cancel all pending/assigned/running tasks
        tasks = await self.repository.list_tasks(session_id, security_context.tenant_id)
        for task in tasks:
            if task.status in (TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.RUNNING):
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.datetime.now(datetime.UTC)
                await self.repository.update_task(task)

        logger.info("Session %s cancelled by user %s: %s", session_id, security_context.user_id, request.reason)
        return session

    async def compile_report(
        self,
        session_id: str,
        security_context: CollaborationSecurityContext,
    ) -> CollaborationReport:
        """Synthesizes the complete collaboration report including findings, reviews, and conflicts."""
        session = await self.get_session(session_id, security_context)
        findings = await self.repository.list_findings(session_id, security_context.tenant_id)
        reviews = await self.repository.list_reviews(session_id, security_context.tenant_id)
        conflicts = await self.repository.list_conflicts(session_id, security_context.tenant_id)

        unresolved = [
            c for c in conflicts
            if c.status in (ConflictStatus.DETECTED, ConflictStatus.ESCALATED)
        ]

        tasks = await self.repository.list_tasks(session_id, security_context.tenant_id)
        succeeded_tasks = sum(1 for t in tasks if t.status == TaskStatus.SUCCEEDED)
        failed_tasks = sum(1 for t in tasks if t.status == TaskStatus.FAILED)

        metrics = {
            "total_tasks": len(tasks),
            "succeeded_tasks": succeeded_tasks,
            "failed_tasks": failed_tasks,
            "total_findings": len(findings),
            "total_reviews": len(reviews),
            "total_conflicts": len(conflicts),
            "unresolved_conflicts": len(unresolved),
        }

        report = CollaborationReport(
            session_id=session.session_id,
            objective=session.objective,
            status=session.status,
            summary=session.summary,
            findings=findings,
            reviews=reviews,
            conflicts=conflicts,
            unresolved_conflicts=unresolved,
            metrics=metrics,
            completed_at=session.completed_at,
        )
        return report
