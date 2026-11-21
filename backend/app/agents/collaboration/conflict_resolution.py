"""KEEP Phase 4.8 — Conflict Resolution Engine.

Detects contradictions, applies evidence-weighted reconciliation, enforces
bounded revision loops, and manages escalation for human review.

Specification: devdocs/p4/p4.8.txt
Owner: Member 3 (Peer Review, Policies & Conflict Resolution)
"""

from __future__ import annotations

import datetime
import logging

from backend.app.agents.collaboration.contracts import (
    CollaborationConflict,
    CollaborationFinding,
    CollaborationSecurityContext,
    ConflictResolutionRequest,
    ConflictStatus,
    generate_collaboration_conflict_id,
)
from backend.app.agents.collaboration.repository import BaseCollaborationRepository
from backend.app.agents.errors import (
    CollaborationConflictUnresolvedError,
    CollaborationMaxRevisionsExceededError,
    CollaborationSessionNotFoundError,
)

logger = logging.getLogger(__name__)

# Heuristic negation indicators for claim contradiction detection
_CONTRADICTORY_PAIRS = (
    ("supported", "unsupported"),
    ("compatible", "incompatible"),
    ("increases", "decreases"),
    ("reduces", "improves"),
    ("true", "false"),
    ("passed", "failed"),
    ("safe", "unsafe"),
    ("vulnerable", "secure"),
)


def claims_contradict(claim_a: str, claim_b: str) -> bool:
    """Heuristic check for opposing assertions between two finding claims."""
    ca, cb = claim_a.lower(), claim_b.lower()
    for pos, neg in _CONTRADICTORY_PAIRS:
        if (pos in ca and neg in cb) or (neg in ca and pos in cb):
            return True
    return False


class ConflictResolutionEngine:
    """Detects, reconciles, and escalates disagreements across agent findings."""

    def __init__(self, repository: BaseCollaborationRepository) -> None:
        self.repository = repository
        self._revision_counts: dict[str, int] = {}  # session_id -> revision_count

    async def detect_contradictions(
        self,
        session_id: str,
        security_context: CollaborationSecurityContext,
    ) -> list[CollaborationConflict]:
        """Scans session findings for contradictory claims and registers detected conflicts."""
        session = await self.repository.get_session(session_id, security_context.tenant_id)
        if not session:
            raise CollaborationSessionNotFoundError(session_id)

        findings = await self.repository.list_findings(session_id, security_context.tenant_id)
        existing_conflicts = await self.repository.list_conflicts(session_id, security_context.tenant_id)
        existing_pairs = {frozenset(c.finding_ids) for c in existing_conflicts}

        detected: list[CollaborationConflict] = []

        for i, fa in enumerate(findings):
            for fb in findings[i + 1 :]:
                pair = frozenset([fa.finding_id, fb.finding_id])
                if pair in existing_pairs:
                    continue

                if claims_contradict(fa.claim, fb.claim):
                    cid = generate_collaboration_conflict_id()
                    conflict = CollaborationConflict(
                        conflict_id=cid,
                        session_id=session_id,
                        tenant_id=security_context.tenant_id,
                        finding_ids=[fa.finding_id, fb.finding_id],
                        status=ConflictStatus.DETECTED,
                        description=(
                            f"Contradiction detected between claim '{fa.claim}' "
                            f"and opposing claim '{fb.claim}'."
                        ),
                        created_at=datetime.datetime.now(datetime.UTC),
                    )
                    await self.repository.create_conflict(conflict)
                    detected.append(conflict)
                    logger.warning("Detected conflict %s between %s and %s.", cid, fa.finding_id, fb.finding_id)

        return detected

    async def reconcile_conflict(
        self,
        conflict_id: str,
        security_context: CollaborationSecurityContext,
    ) -> CollaborationConflict:
        """Attempts deterministic evidence-weighted reconciliation of a detected conflict."""
        conflict = await self.repository.get_conflict(conflict_id, security_context.tenant_id)
        if not conflict:
            raise CollaborationConflictUnresolvedError(f"Conflict '{conflict_id}' not found.")

        # Load involved findings
        findings: list[CollaborationFinding] = []
        for fid in conflict.finding_ids:
            f = await self.repository.get_finding(fid, security_context.tenant_id)
            if f:
                findings.append(f)

        if len(findings) == 2:
            fa, fb = findings[0], findings[1]
            # Compare evidence counts
            if len(fa.evidence_refs) > len(fb.evidence_refs):
                conflict.status = ConflictStatus.RESOLVED
                conflict.resolution = (
                    f"Resolved in favor of finding '{fa.finding_id}' "
                    f"({len(fa.evidence_refs)} evidence refs vs {len(fb.evidence_refs)})."
                )
                conflict.resolved_by = "system:evidence_weight_policy"
                conflict.resolved_at = datetime.datetime.now(datetime.UTC)
                await self.repository.update_conflict(conflict)
                return conflict

            if len(fb.evidence_refs) > len(fa.evidence_refs):
                conflict.status = ConflictStatus.RESOLVED
                conflict.resolution = (
                    f"Resolved in favor of finding '{fb.finding_id}' "
                    f"({len(fb.evidence_refs)} evidence refs vs {len(fa.evidence_refs)})."
                )
                conflict.resolved_by = "system:evidence_weight_policy"
                conflict.resolved_at = datetime.datetime.now(datetime.UTC)
                await self.repository.update_conflict(conflict)
                return conflict

        # Cannot resolve automatically — escalate
        conflict.status = ConflictStatus.ESCALATED
        conflict.resolution = "Evidence weight is equal or ambiguous; escalated for human resolution."
        conflict.resolved_at = datetime.datetime.now(datetime.UTC)
        await self.repository.update_conflict(conflict)
        return conflict

    async def record_revision_attempt(
        self,
        session_id: str,
        security_context: CollaborationSecurityContext,
    ) -> int:
        """Tracks review revision loop count and enforces configured max_revisions ceiling."""
        session = await self.repository.get_session(session_id, security_context.tenant_id)
        if not session:
            raise CollaborationSessionNotFoundError(session_id)

        current = self._revision_counts.get(session_id, 0)
        if current >= session.max_revisions:
            raise CollaborationMaxRevisionsExceededError(session_id, session.max_revisions)

        current += 1
        self._revision_counts[session_id] = current
        logger.info("Session %s revision count incremented to %d/%d.", session_id, current, session.max_revisions)
        return current

    def get_revision_count(self, session_id: str) -> int:
        """Returns the current revision count for a session."""
        return self._revision_counts.get(session_id, 0)

    async def resolve_escalated_conflict(
        self,
        request: ConflictResolutionRequest,
        security_context: CollaborationSecurityContext,
    ) -> CollaborationConflict:
        """Applies human intervention or policy resolution to an escalated conflict."""
        conflict = await self.repository.get_conflict(request.conflict_id, security_context.tenant_id)
        if not conflict:
            raise CollaborationConflictUnresolvedError(f"Conflict '{request.conflict_id}' not found.")

        conflict.status = ConflictStatus.RESOLVED
        conflict.resolution = request.resolution
        conflict.resolved_by = security_context.user_id
        conflict.resolved_at = datetime.datetime.now(datetime.UTC)
        await self.repository.update_conflict(conflict)
        logger.info("Conflict %s resolved by user %s.", request.conflict_id, security_context.user_id)
        return conflict
