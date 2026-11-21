"""Re-export of conflict resolution engine for backwards compatibility."""

from backend.app.agents.collaboration.conflict_resolution import (  # noqa: F401
    ConflictResolutionEngine,
    claims_contradict,
)
