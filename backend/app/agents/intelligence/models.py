"""Phase 4.11 — Intelligence Lifecycle State & Validation Helpers."""

from __future__ import annotations

from backend.app.agents.errors import IntelligenceInvalidStateError
from backend.app.agents.intelligence.contracts import InsightStatus

ALLOWED_INSIGHT_TRANSITIONS: dict[InsightStatus, set[InsightStatus]] = {
    "candidate": {"validated", "suppressed", "withheld"},
    "validated": {"published", "suppressed", "withheld"},
    "published": {"investigating", "dismissed", "resolved"},
    "investigating": {"published", "dismissed", "resolved"},
    "dismissed": {"published", "resolved"},
    "resolved": set(),
    "suppressed": {"published"},
    "withheld": set(),
}


def validate_insight_transition(
    insight_id: str,
    current_status: InsightStatus,
    target_status: InsightStatus,
) -> InsightStatus:
    """Validates and returns `target_status` or raises IntelligenceInvalidStateError."""
    if current_status == target_status:
        return target_status
    allowed = ALLOWED_INSIGHT_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        raise IntelligenceInvalidStateError(
            insight_id=insight_id,
            current_status=current_status,
            action=f"transition_to_{target_status}",
        )
    return target_status
