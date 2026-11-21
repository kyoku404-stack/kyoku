"""KEEP Phase 4.8 — Collaboration Findings Catalog.

Maintains verifiable claims produced by agents with evidence references,
provenance metadata, and documented limitations.

Specification: devdocs/p4/p4.8.txt
Owner: Member 2 (Communication & Task Dispatching)
"""

from __future__ import annotations

import datetime
import logging
from typing import Any

from backend.app.agents.collaboration.contracts import (
    CollaborationFinding,
    CollaborationSecurityContext,
    generate_collaboration_finding_id,
)
from backend.app.agents.collaboration.repository import BaseCollaborationRepository
from backend.app.agents.errors import (
    CollaborationSessionNotFoundError,
    CollaborationTaskNotFoundError,
    CollaborationTenantIsolationViolationError,
)

logger = logging.getLogger(__name__)


class FindingsCatalog:
    """Stores and retrieves verifiable findings linked to authorized KEEP evidence."""

    def __init__(self, repository: BaseCollaborationRepository) -> None:
        self.repository = repository

    async def register_finding(
        self,
        session_id: str,
        task_id: str,
        claim: str,
        security_context: CollaborationSecurityContext,
        evidence_refs: list[str] | None = None,
        provenance: dict[str, Any] | None = None,
        limitations: str | None = None,
    ) -> CollaborationFinding:
        """Registers a new evidence-backed finding under tenant boundary isolation."""
        if not claim or not claim.strip():
            raise ValueError("Finding claim cannot be empty.")

        # Validate session ownership
        session = await self.repository.get_session(session_id, security_context.tenant_id)
        if not session:
            raise CollaborationSessionNotFoundError(session_id)

        if session.tenant_id != security_context.tenant_id:
            raise CollaborationTenantIsolationViolationError(
                security_context.tenant_id, session.tenant_id
            )

        # Validate task ownership
        task = await self.repository.get_task(task_id, security_context.tenant_id)
        if not task:
            raise CollaborationTaskNotFoundError(task_id)

        finding_id = generate_collaboration_finding_id()
        provenance_payload = dict(provenance or {})
        provenance_payload.setdefault("agent_id", task.agent_id)
        provenance_payload.setdefault("registered_by", security_context.user_id)

        finding = CollaborationFinding(
            finding_id=finding_id,
            session_id=session_id,
            tenant_id=security_context.tenant_id,
            task_id=task_id,
            claim=claim.strip(),
            evidence_refs=list(evidence_refs or []),
            provenance=provenance_payload,
            limitations=limitations,
            created_at=datetime.datetime.now(datetime.UTC),
        )

        saved = await self.repository.create_finding(finding)
        logger.info(
            "Registered finding %s for task %s (session %s) with %d evidence refs.",
            finding_id,
            task_id,
            session_id,
            len(finding.evidence_refs),
        )
        return saved

    async def list_findings(
        self,
        session_id: str,
        security_context: CollaborationSecurityContext,
        task_id: str | None = None,
    ) -> list[CollaborationFinding]:
        """Lists findings for a session or task under tenant isolation."""
        session = await self.repository.get_session(session_id, security_context.tenant_id)
        if not session:
            raise CollaborationSessionNotFoundError(session_id)

        return await self.repository.list_findings(
            session_id=session_id,
            tenant_id=security_context.tenant_id,
            task_id=task_id,
        )

    async def get_finding(
        self,
        finding_id: str,
        security_context: CollaborationSecurityContext,
    ) -> CollaborationFinding | None:
        """Retrieves a single finding ensuring tenant isolation."""
        return await self.repository.get_finding(finding_id, security_context.tenant_id)
