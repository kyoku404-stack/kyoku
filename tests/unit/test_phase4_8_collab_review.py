"""Unit tests for Phase 4.8 Member 3 — Peer Review, Policies & Conflict Resolution.

Tests peer reviews, bias prevention, contradiction detection, deterministic
reconciliation, bounded revision loop limits, and zero-trust policies.
"""

from __future__ import annotations

import pytest

from backend.app.agents.collaboration.conflict_resolution import (
    ConflictResolutionEngine,
    claims_contradict,
)
from backend.app.agents.collaboration.contracts import (
    CollaborationFinding,
    CollaborationRequest,
    CollaborationSecurityContext,
    CollaborationTaskSpec,
    ConflictStatus,
    ReviewOutcome,
)
from backend.app.agents.collaboration.findings import FindingsCatalog
from backend.app.agents.collaboration.policies import CollaborationPolicyEngine
from backend.app.agents.collaboration.repository import InMemoryCollaborationRepository
from backend.app.agents.collaboration.review import PeerReviewService
from backend.app.agents.collaboration.session_manager import SessionManager
from backend.app.agents.errors import (
    CollaborationAccessDeniedError,
    CollaborationMaxRevisionsExceededError,
    CollaborationTenantIsolationViolationError,
)


@pytest.fixture
def repo() -> InMemoryCollaborationRepository:
    return InMemoryCollaborationRepository()


@pytest.fixture
def session_mgr(repo: InMemoryCollaborationRepository) -> SessionManager:
    return SessionManager(repository=repo)


@pytest.fixture
def review_service(repo: InMemoryCollaborationRepository) -> PeerReviewService:
    return PeerReviewService(repository=repo)


@pytest.fixture
def conflict_engine(repo: InMemoryCollaborationRepository) -> ConflictResolutionEngine:
    return ConflictResolutionEngine(repository=repo)


@pytest.fixture
def policy_engine() -> CollaborationPolicyEngine:
    return CollaborationPolicyEngine()


@pytest.fixture
def findings_catalog(repo: InMemoryCollaborationRepository) -> FindingsCatalog:
    return FindingsCatalog(repository=repo)


@pytest.fixture
def security_context() -> CollaborationSecurityContext:
    return CollaborationSecurityContext(
        tenant_id="tenant-corp",
        user_id="usr-lead-01",
        roles=["lead", "architect"],
        permissions=["agent.invoke", "agent.read"],
    )


def test_claims_contradiction_heuristics():
    """Verify contradiction detection identifies opposing polarity claims."""
    assert claims_contradict(
        "Redis cluster is supported in production.",
        "Redis cluster is unsupported in production.",
    )
    assert claims_contradict(
        "Architecture passed vulnerability scan.",
        "Architecture failed vulnerability scan.",
    )
    assert not claims_contradict(
        "PostgreSQL query performance is fast.",
        "PostgreSQL query performance is stable.",
    )


@pytest.mark.asyncio
async def test_peer_review_supported_and_unsupported_findings(
    session_mgr: SessionManager,
    findings_catalog: FindingsCatalog,
    review_service: PeerReviewService,
    security_context: CollaborationSecurityContext,
):
    """Verify peer review accepts evidence-backed findings and requests revision for unsupported claims."""
    request = CollaborationRequest(
        objective="Review evaluation",
        agent_ids=["agent:researcher", "agent:reviewer"],
        tasks=[CollaborationTaskSpec(task_id="t-1", agent_id="agent:researcher", title="Task 1")],
    )
    session = await session_mgr.create_session(request, security_context)

    # Finding 1: Well-supported
    f1 = await findings_catalog.register_finding(
        session_id=session.session_id,
        task_id="t-1",
        claim="Latency p99 is under 15ms.",
        evidence_refs=["keep://evidence/doc-101", "keep://evidence/doc-102"],
        security_context=security_context,
    )

    # Finding 2: Unsupported claim
    f2 = await findings_catalog.register_finding(
        session_id=session.session_id,
        task_id="t-1",
        claim="Throughput will scale infinitely.",
        evidence_refs=[],
        security_context=security_context,
    )

    # Reviewing f1 only -> ACCEPTED
    res1 = await review_service.review_findings(
        session_id=session.session_id,
        reviewer_id="agent:reviewer",
        finding_ids=[f1.finding_id],
        security_context=security_context,
    )
    assert res1.outcome == ReviewOutcome.ACCEPTED
    assert len(res1.unsupported_claims) == 0

    # Reviewing f2 -> NEEDS_REVISION
    res2 = await review_service.review_findings(
        session_id=session.session_id,
        reviewer_id="agent:reviewer",
        finding_ids=[f2.finding_id],
        security_context=security_context,
    )
    assert res2.outcome == ReviewOutcome.NEEDS_REVISION
    assert len(res2.unsupported_claims) == 1
    assert "Throughput will scale infinitely." in res2.unsupported_claims[0]


@pytest.mark.asyncio
async def test_peer_review_self_review_prevention(
    session_mgr: SessionManager,
    findings_catalog: FindingsCatalog,
    review_service: PeerReviewService,
    security_context: CollaborationSecurityContext,
):
    """Verify that an agent cannot conduct peer review on its own findings."""
    request = CollaborationRequest(
        objective="Self review prevention",
        agent_ids=["agent:researcher"],
        tasks=[CollaborationTaskSpec(task_id="t-own", agent_id="agent:researcher", title="Task Own")],
    )
    session = await session_mgr.create_session(request, security_context)

    f = await findings_catalog.register_finding(
        session_id=session.session_id,
        task_id="t-own",
        claim="Self-evident finding",
        evidence_refs=["doc-1"],
        security_context=security_context,
    )

    with pytest.raises(ValueError, match="Self-review rejected"):
        await review_service.review_findings(
            session_id=session.session_id,
            reviewer_id="agent:researcher",
            finding_ids=[f.finding_id],
            security_context=security_context,
        )


@pytest.mark.asyncio
async def test_conflict_detection_and_evidence_weighted_resolution(
    session_mgr: SessionManager,
    repo: InMemoryCollaborationRepository,
    conflict_engine: ConflictResolutionEngine,
    security_context: CollaborationSecurityContext,
):
    """Verify contradiction detection and automatic reconciliation favoring superior evidence."""
    request = CollaborationRequest(
        objective="Conflict scenario",
        agent_ids=["agent:agent1", "agent:agent2"],
        tasks=[
            CollaborationTaskSpec(task_id="t-1", agent_id="agent:agent1", title="Task 1"),
            CollaborationTaskSpec(task_id="t-2", agent_id="agent:agent2", title="Task 2"),
        ],
    )
    session = await session_mgr.create_session(request, security_context)

    # Contradicting findings: one with 2 evidence refs, one with 0
    f1 = CollaborationFinding(
        finding_id="fnd-pos",
        session_id=session.session_id,
        tenant_id="tenant-corp",
        task_id="t-1",
        claim="System throughput increases by 50%.",
        evidence_refs=["ev-bench-1", "ev-bench-2"],
    )
    f2 = CollaborationFinding(
        finding_id="fnd-neg",
        session_id=session.session_id,
        tenant_id="tenant-corp",
        task_id="t-2",
        claim="System throughput decreases by 50%.",
        evidence_refs=[],
    )
    await repo.create_finding(f1)
    await repo.create_finding(f2)

    detected = await conflict_engine.detect_contradictions(session.session_id, security_context)
    assert len(detected) == 1
    assert detected[0].status == ConflictStatus.DETECTED

    # Reconcile -> resolves in favor of fnd-pos
    reconciled = await conflict_engine.reconcile_conflict(detected[0].conflict_id, security_context)
    assert reconciled.status == ConflictStatus.RESOLVED
    assert "fnd-pos" in (reconciled.resolution or "")


@pytest.mark.asyncio
async def test_bounded_revision_loop_enforcement(
    session_mgr: SessionManager,
    conflict_engine: ConflictResolutionEngine,
    security_context: CollaborationSecurityContext,
):
    """Verify exceeding configured max_revisions raises CollaborationMaxRevisionsExceededError."""
    request = CollaborationRequest(
        objective="Revision loop test",
        agent_ids=["agent:worker"],
        max_revisions=2,
    )
    session = await session_mgr.create_session(request, security_context)

    # Revision 1: Allowed
    c1 = await conflict_engine.record_revision_attempt(session.session_id, security_context)
    assert c1 == 1

    # Revision 2: Allowed
    c2 = await conflict_engine.record_revision_attempt(session.session_id, security_context)
    assert c2 == 2

    # Revision 3: Exceeds limit -> error
    with pytest.raises(CollaborationMaxRevisionsExceededError):
        await conflict_engine.record_revision_attempt(session.session_id, security_context)


@pytest.mark.asyncio
async def test_policy_engine_authorization(
    session_mgr: SessionManager,
    policy_engine: CollaborationPolicyEngine,
    security_context: CollaborationSecurityContext,
):
    """Verify policy engine blocks cross-tenant access and unauthorized conflict resolution."""
    request = CollaborationRequest(objective="Policy test", agent_ids=["agent:worker"])
    session = await session_mgr.create_session(request, security_context)

    # Cross-tenant access blocked
    foreign_ctx = CollaborationSecurityContext(tenant_id="tenant-other", user_id="usr-guest")
    with pytest.raises(CollaborationTenantIsolationViolationError):
        policy_engine.authorize_session_access(session, foreign_ctx)

    # Supervisory role required for conflict resolution
    guest_ctx = CollaborationSecurityContext(
        tenant_id="tenant-corp",
        user_id="usr-guest",
        roles=["viewer"],
        permissions=["agent.read"],
    )
    with pytest.raises(CollaborationAccessDeniedError, match="Conflict resolution requires supervisory role"):
        policy_engine.authorize_conflict_resolution(guest_ctx)

    # Lead role permitted
    policy_engine.authorize_conflict_resolution(security_context)
