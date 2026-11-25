"""Phase 4.11 — Insight Category & Detector Registry."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.app.agents.intelligence.contracts import InsightCategory


@dataclass(frozen=True)
class InsightCategorySpec:
    category: InsightCategory
    description: str
    default_suppression_seconds: int = 3600
    requires_evidence: bool = True


class InsightRegistry:
    """Registry of supported insight categories and metadata."""

    def __init__(self) -> None:
        self._specs: dict[InsightCategory, InsightCategorySpec] = {
            "significant_change": InsightCategorySpec(
                category="significant_change",
                description="Material changes detected between document versions or policies.",
                default_suppression_seconds=3600,
                requires_evidence=True,
            ),
            "knowledge_gap": InsightCategorySpec(
                category="knowledge_gap",
                description="Recurring unanswered questions or insufficient authorized documentation.",
                default_suppression_seconds=7200,
                requires_evidence=False,
            ),
            "contradiction": InsightCategorySpec(
                category="contradiction",
                description="Incompatible or conflicting statements across documents or versions.",
                default_suppression_seconds=3600,
                requires_evidence=True,
            ),
            "stale_knowledge": InsightCategorySpec(
                category="stale_knowledge",
                description="Knowledge exceeding its configured review interval or referencing superseded info.",
                default_suppression_seconds=86400,
                requires_evidence=True,
            ),
            "emerging_trend": InsightCategorySpec(
                category="emerging_trend",
                description="Repeated patterns over a defined time window relative to baseline.",
                default_suppression_seconds=14400,
                requires_evidence=True,
            ),
        }
        self._detector_versions: dict[str, str] = field(default_factory=dict) if False else {}

    def get_category(self, category: InsightCategory) -> InsightCategorySpec:
        return self._specs[category]

    def list_categories(self) -> list[InsightCategorySpec]:
        return list(self._specs.values())

    def register_detector_version(self, detector_id: str, version: str) -> None:
        self._detector_versions[detector_id] = version

    def get_detector_versions(self) -> dict[str, str]:
        return dict(self._detector_versions)
