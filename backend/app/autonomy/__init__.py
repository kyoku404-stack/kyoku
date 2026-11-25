"""Compatibility alias package for Phase 4.9 `app.autonomy.*` spec references."""

from backend.app.agents.autonomy import (
    AutonomousWorkflowController,
    AutonomousWorkflowRecord,
    AutonomousWorkflowRequest,
    AutonomyPolicy,
    AutonomySecurityContext,
    AutonomyState,
    AutonomyStatus,
    EvaluationResult,
)

__all__ = [
    "AutonomousWorkflowController",
    "AutonomousWorkflowRecord",
    "AutonomousWorkflowRequest",
    "AutonomyPolicy",
    "AutonomySecurityContext",
    "AutonomyState",
    "AutonomyStatus",
    "EvaluationResult",
]
