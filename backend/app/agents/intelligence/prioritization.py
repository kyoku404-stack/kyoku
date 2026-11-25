"""Phase 4.11 — Deterministic Insight Prioritization & Ranking."""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.agents.intelligence.contracts import (
    IntelligenceCandidate,
    IntelligenceInsight,
)

RANKING_VERSION = "v1"


@dataclass(frozen=True)
class RankingWeights:
    impact: float = 0.30
    relevance: float = 0.25
    evidence_quality: float = 0.25
    urgency: float = 0.10
    novelty: float = 0.10


DEFAULT_WEIGHTS = RankingWeights()


def calculate_priority_score(
    impact: float,
    relevance: float,
    evidence_quality: float,
    urgency: float,
    novelty: float,
    weights: RankingWeights = DEFAULT_WEIGHTS,
) -> float:
    """Calculates deterministic priority score S in [0, 100].

    Formula: S = 100 * (0.30*I + 0.25*R + 0.25*E + 0.10*U + 0.10*N)
    """
    values = [impact, relevance, evidence_quality, urgency, novelty]
    if any(not 0.0 <= value <= 1.0 for value in values):
        raise ValueError("All scores must be between 0 and 1")

    score = 100.0 * (
        weights.impact * impact
        + weights.relevance * relevance
        + weights.evidence_quality * evidence_quality
        + weights.urgency * urgency
        + weights.novelty * novelty
    )
    return round(min(100.0, max(0.0, score)), 4)


def score_candidate(
    candidate: IntelligenceCandidate,
    weights: RankingWeights = DEFAULT_WEIGHTS,
) -> float:
    """Computes the priority score for an IntelligenceCandidate."""
    return calculate_priority_score(
        impact=candidate.impact_score,
        relevance=candidate.relevance_score,
        evidence_quality=candidate.evidence_quality_score,
        urgency=candidate.urgency_score,
        novelty=candidate.novelty_score,
        weights=weights,
    )


def rank_insights(insights: list[IntelligenceInsight]) -> list[IntelligenceInsight]:
    """Deterministically sorts insights by priority_score DESC, confidence DESC, insight_id ASC."""
    return sorted(
        insights,
        key=lambda ins: (-ins.priority_score, -ins.confidence_score, ins.category, ins.insight_id),
    )
