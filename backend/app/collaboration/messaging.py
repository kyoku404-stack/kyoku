"""Re-export of messaging service for backwards compatibility."""

from backend.app.agents.collaboration.messaging import (  # noqa: F401
    CollaborationMessageService,
    scrub_secrets_from_text,
    scrub_secrets_recursively,
)
