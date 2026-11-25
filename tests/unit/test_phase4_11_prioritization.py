"""Unit tests for Phase 4.11 Member 1: Intelligence Contracts, Prioritization, Deduplication & Service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.app.agents.intelligence import (
    IntelligenceCandidate,
    IntelligenceSecurityContext,
    IntelligenceService,
    ScanRequest,
    calculate_priority_score,
    compute_dedup_key,
    is_suppressed,
)


class _StubDetector:
    detector_id = "stub_change"
    version = "1.0.0"

    def __init__(self, fail: bool = False) -> None:
        self._fail = fail

    async def detect(self, observation: dict, security_context: dict) -> list[dict]:
        if self._fail:
            raise RuntimeError("detector crashed safely")
        return [
            IntelligenceCandidate(
                category="significant_change",
                title="Policy retention updated from 90 to 30 days",
                summary="Retention window shortened in Security Policy v2.",
                observed_facts=["v1 retention=90d", "v2 retention=30d"],
                inferred_explanation="Shorter retention may require archive verification.",
                evidence_refs=["doc:pol-1:v1", "doc:pol-1:v2"],
                affected_resource_refs=["doc:pol-1"],
                impact_score=0.9,
                relevance_score=0.8,
                evidence_quality_score=0.95,
                urgency_score=0.7,
                novelty_score=0.9,
                confidence_score=0.92,
            ).model_dump()
        ]


def test_priority_score_formula_and_bounds() -> None:
    score = calculate_priority_score(1.0, 1.0, 1.0, 1.0, 1.0)
    assert score == 100.0

    # 100*(0.30*0.8 + 0.25*0.6 + 0.25*0.9 + 0.10*0.5 + 0.10*0.4)
    # = 100*(0.24 + 0.15 + 0.225 + 0.05 + 0.04) = 70.5
    score2 = calculate_priority_score(0.8, 0.6, 0.9, 0.5, 0.4)
    assert score2 == 70.5

    with pytest.raises(ValueError):
        calculate_priority_score(1.2, 0.5, 0.5, 0.5, 0.5)


@pytest.mark.asyncio
async def test_service_deduplicates_across_runs_and_records_detector_errors() -> None:
    ctx = IntelligenceSecurityContext(
        tenant_id="org_1",
        user_id="usr_1",
        roles=["admin"],
        permissions=["agent.invoke", "agent.read"],
    )
    svc = IntelligenceService(detectors=[_StubDetector()])
    # Register second failing detector under distinct id
    failing = _StubDetector(fail=True)
    failing.detector_id = "stub_failing"  # type: ignore[misc]
    svc.register_detector(failing)

    run1 = await svc.run_scan(
        ScanRequest(observations=[{"doc_id": "pol-1"}], suppress_window_seconds=3600),
        ctx,
    )
    assert run1.status == "completed_with_errors"
    assert len(run1.detector_errors) >= 1
    assert run1.insights_published == 1
    assert run1.insights_suppressed == 0

    run2 = await svc.run_scan(
        ScanRequest(observations=[{"doc_id": "pol-1"}], suppress_window_seconds=3600),
        ctx,
    )
    assert run2.insights_published == 0
    assert run2.insights_suppressed == 1

    feed = await svc.list_insights(ctx)
    assert len(feed) == 1
    assert feed[0].priority_score > 80.0


def test_dedup_key_determinism_and_suppression_expiry() -> None:
    cand = IntelligenceCandidate(
        category="knowledge_gap",
        title="Missing Disaster Recovery Runbook",
        summary="Repeated questions without documentation.",
        evidence_refs=["run:r1"],
        affected_resource_refs=["topic:dr"],
        impact_score=0.7,
        relevance_score=0.7,
    )
    k1 = compute_dedup_key("org_a", cand)
    k2 = compute_dedup_key("org_a", cand)
    k3 = compute_dedup_key("org_b", cand)
    assert k1 == k2
    assert k1 != k3

    from backend.app.agents.intelligence.contracts import SuppressionRecord

    expired = SuppressionRecord(
        tenant_id="org_a",
        dedup_key=k1,
        scope="tenant",
        reason="old",
        suppressed_until=datetime.now(UTC) - timedelta(seconds=10),
    )
    suppressed, _ = is_suppressed([expired], k1)
    assert not suppressed
