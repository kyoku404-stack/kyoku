"""Re-export of collaboration repository for backwards compatibility."""

from backend.app.agents.collaboration.repository import (  # noqa: F401
    BaseCollaborationRepository,
    InMemoryCollaborationRepository,
)
