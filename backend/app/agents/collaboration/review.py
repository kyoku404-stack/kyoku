"""KEEP Phase 4.8 — Peer Review Service.

Validates claims, verifies evidence citations, prevents self-review bias,
and produces structured review evaluations.

Specification: devdocs/p4/p4.8.txt
Owner: Member 3 (Peer Review, Policies & Conflict Resolution)
"""

from __future__ import annotations

import datetime
import logging

from backend.app.agents.collaboration.contracts import (
    CollaborationFinding,
    CollaborationSecurityContext,
    ReviewOutcome,
    ReviewResult,
    generate_collaboration_review_id,
)
from backend.app.agents.collaboration.repository import BaseCollaborationRepository
from backend.app.agents.errors import (
    CollaborationSessionNotFoundError,
    CollaborationTenantIsolationViolationError,
)

logger = logging.getLogger(__name__)


class PeerReviewService:
    """Evaluates agent findings for evidence rigor, claim consistency, and completeness."""

    def __init__(self, repository: BaseCollaborationRepository) -> None:
        self.repository = repository

    async def review_findings(
        self,
        session_id: str,
        reviewer_id: str,
        finding_ids: list[str],
        security_context: CollaborationSecurityContext,
        force_outcome: ReviewOutcome | None = None,
        critique: str | None = None,
    ) -> ReviewResult:
        """Conducts structured peer evaluation of target findings."""
        session = await self.repository.get_session(session_id, security_context.tenant_id)
        if not session:
            raise CollaborationSessionNotFoundError(session_id)

        if session.tenant_id != security_context.tenant_id:
            raise CollaborationTenantIsolationViolationError(
                security_context.tenant_id, session.tenant_id
            )

        # Retrieve target findings
        session_findings = await self.repository.list_findings(session_id, security_context.tenant_id)
        finding_map = {f.finding_id: f for f in session_findings}

        evaluated: list[CollaborationFinding] = []
        for fid in finding_ids:
            if fid in finding_map:
                evaluated.append(finding_map[fid])

        if not evaluated:
            raise ValueError(f"No valid findings found in session '{session_id}' for IDs: {finding_ids}")

        # Self-review check: reviewer cannot be the sole author of all findings
        authors = {f.provenance.get("agent_id") for f in evaluated}
        if len(authors) == 1 and reviewer_id in authors:
            logger.warning("Agent %s attempted self-review on own findings %s.", reviewer_id, finding_ids)
            raise ValueError(f"Self-review rejected: reviewer '{reviewer_id}' authored all target findings.")

        # Evaluate evidence backing
        unsupported: list[str] = []
        missing_refs: list[str] = []
        for f in evaluated:
            if not f.evidence_refs:
                unsupported.append(f.claim)
                missing_refs.append(f"finding:{f.finding_id}:missing_evidence")

        # Determine outcome
        if force_outcome:
            outcome = force_outcome
        elif unsupported:
            outcome = ReviewOutcome.NEEDS_REVISION
        else:
            outcome = ReviewOutcome.ACCEPTED

        reasons: list[str] = []
        if critique:
            reasons.append(critique)
        if unsupported:
            reasons.append(f"{len(unsupported)} claims lack verified evidence references.")

        review_id = generate_collaboration_review_id()
        review = ReviewResult(
            review_id=review_id,
            session_id=session_id,
            tenant_id=security_context.tenant_id,
            reviewer_id=reviewer_id,
            finding_ids=finding_ids,
            outcome=outcome,
            reasons=reasons,
            unsupported_claims=unsupported,
            missing_evidence=missing_refs,
            created_at=datetime.datetime.now(datetime.UTC),
        )

        saved = await self.repository.create_review(review)
        logger.info(
            "Peer review %s completed by %s on findings %s (outcome=%s).",
            review_id,
            reviewer_id,
            finding_ids,
            outcome.value,
        )
        return saved

    async def list_reviews(
        self,
        session_id: str,
        security_context: CollaborationSecurityContext,
    ) -> list[ReviewResult]:
        """Lists all peer reviews for a collaboration session."""
        session = await self.repository.get_session(session_id, security_context.tenant_id)
        if not session:
            raise CollaborationSessionNotFoundError(session_id)

        return await self.repository.list_reviews(session_id, security_context.tenant_id)
