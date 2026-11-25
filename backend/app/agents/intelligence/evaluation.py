"""Phase 4.11 — Labelled Detector Evaluation (Precision, Recall & Alert Volume)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.agents.intelligence_detectors.base import IntelligenceDetector


@dataclass(frozen=True)
class LabelledObservation:
    """A single labelled observation for detector quality evaluation."""

    case_id: str
    observation: dict[str, Any]
    expected_categories: set[str]


@dataclass(frozen=True)
class EvaluationResult:
    """Precision, recall, F1, and alert volume metrics across a labelled test set."""

    total_cases: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    total_candidates: int


async def evaluate_detector_set(
    detectors: list[IntelligenceDetector],
    dataset: list[LabelledObservation],
    tenant_id: str = "eval_tenant",
) -> EvaluationResult:
    """Evaluates precision, recall, F1, and alert volume on a labelled dataset."""
    tp = 0
    fp = 0
    fn = 0
    total_candidates = 0
    sec_ctx = {"tenant_id": tenant_id, "user_id": "eval_runner", "roles": ["admin"]}

    for case in dataset:
        predicted_cats: set[str] = set()
        for det in detectors:
            cands = await det.detect(case.observation, sec_ctx)
            total_candidates += len(cands)
            for c in cands:
                predicted_cats.add(str(c["category"]))

        tp += len(predicted_cats.intersection(case.expected_categories))
        fp += len(predicted_cats - case.expected_categories)
        fn += len(case.expected_categories - predicted_cats)

    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    f1 = round((2 * precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0

    return EvaluationResult(
        total_cases=len(dataset),
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        precision=precision,
        recall=recall,
        f1_score=f1,
        total_candidates=total_candidates,
    )
