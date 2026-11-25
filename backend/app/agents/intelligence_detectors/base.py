"""Phase 4.11 — Intelligence Detector Protocol & Registry."""

from __future__ import annotations

from typing import Any, Protocol


class IntelligenceDetector(Protocol):
    """Protocol implemented by all deterministic/hybrid Phase 4.11 detectors."""

    @property
    def detector_id(self) -> str: ...

    @property
    def version(self) -> str: ...

    async def detect(
        self,
        observation: dict[str, Any],
        security_context: dict[str, Any],
    ) -> list[dict[str, Any]]: ...


class DetectorRegistry:
    """Registry of active Phase 4.11 detectors."""

    def __init__(self) -> None:
        self._detectors: dict[str, IntelligenceDetector] = {}

    def register(self, detector: IntelligenceDetector) -> None:
        self._detectors[detector.detector_id] = detector

    def get(self, detector_id: str) -> IntelligenceDetector | None:
        return self._detectors.get(detector_id)

    def list_all(self) -> list[IntelligenceDetector]:
        return list(self._detectors.values())
