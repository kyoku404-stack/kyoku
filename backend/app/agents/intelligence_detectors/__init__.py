"""Phase 4.11 — Intelligence Detectors Package."""

from backend.app.agents.intelligence_detectors.base import (
    DetectorRegistry,
    IntelligenceDetector,
)
from backend.app.agents.intelligence_detectors.change_detector import (
    SignificantChangeDetector,
)
from backend.app.agents.intelligence_detectors.contradiction_detector import (
    ContradictionDetector,
)
from backend.app.agents.intelligence_detectors.knowledge_gap_detector import (
    KnowledgeGapDetector,
)
from backend.app.agents.intelligence_detectors.staleness_detector import (
    StalenessDetector,
    detect_stale_document,
)
from backend.app.agents.intelligence_detectors.trend_detector import (
    EmergingTrendDetector,
)


def build_default_detectors() -> list[IntelligenceDetector]:
    return [
        SignificantChangeDetector(),
        KnowledgeGapDetector(),
        ContradictionDetector(),
        StalenessDetector(),
        EmergingTrendDetector(),
    ]


__all__ = [
    "ContradictionDetector",
    "DetectorRegistry",
    "EmergingTrendDetector",
    "IntelligenceDetector",
    "KnowledgeGapDetector",
    "SignificantChangeDetector",
    "StalenessDetector",
    "build_default_detectors",
    "detect_stale_document",
]
