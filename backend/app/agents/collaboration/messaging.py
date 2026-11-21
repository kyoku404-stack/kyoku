"""KEEP Phase 4.8 — Collaboration Messaging Service.

Validates and routes structured inter-agent messages with secret scrubbing
and correlation tracking.

Specification: devdocs/p4/p4.8.txt
Owner: Member 2 (Communication & Task Dispatching)
"""

from __future__ import annotations

import datetime
import logging
import re
from typing import Any
from uuid import uuid4

from backend.app.agents.collaboration.contracts import (
    CollaborationMessage,
    CollaborationMessageType,
    CollaborationSecurityContext,
    generate_collaboration_message_id,
)
from backend.app.agents.collaboration.repository import BaseCollaborationRepository
from backend.app.agents.errors import (
    CollaborationMessageInvalidError,
    CollaborationSessionNotFoundError,
    CollaborationTenantIsolationViolationError,
)

logger = logging.getLogger(__name__)

# Secret and credential scrubbing patterns
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    re.compile(r"(?i)(password|secret|api[_-]?key|token)\s*[:=]\s*['\"]?[^\s'\";,]+['\"]?"),
)


def scrub_secrets_from_text(text: str) -> str:
    """Masks secrets, tokens, and API keys from a text string."""
    sanitized = text
    for pattern in _SECRET_PATTERNS:
        sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)
    return sanitized


def scrub_secrets_recursively(data: Any) -> Any:
    """Recursively walks nested structures and redacts credential patterns."""
    if isinstance(data, str):
        return scrub_secrets_from_text(data)
    if isinstance(data, dict):
        return {k: scrub_secrets_recursively(v) for k, v in data.items()}
    if isinstance(data, list):
        return [scrub_secrets_recursively(item) for item in data]
    return data


class CollaborationMessageService:
    """Validates and persists structured communication between collaborating agents."""

    def __init__(self, repository: BaseCollaborationRepository) -> None:
        self.repository = repository

    async def send_message(
        self,
        session_id: str,
        sender_id: str,
        recipient_id: str,
        message_type: CollaborationMessageType,
        payload: dict[str, Any],
        security_context: CollaborationSecurityContext,
        task_id: str | None = None,
        correlation_id: str | None = None,
    ) -> CollaborationMessage:
        """Validates, sanitizes, and records an inter-agent message."""
        if not sender_id or not sender_id.strip():
            raise CollaborationMessageInvalidError("Message sender_id cannot be empty.")
        if not recipient_id or not recipient_id.strip():
            raise CollaborationMessageInvalidError("Message recipient_id cannot be empty.")

        # Validate session ownership and isolation
        session = await self.repository.get_session(session_id, security_context.tenant_id)
        if not session:
            raise CollaborationSessionNotFoundError(session_id)

        if session.tenant_id != security_context.tenant_id:
            raise CollaborationTenantIsolationViolationError(
                security_context.tenant_id, session.tenant_id
            )

        sanitized_payload = scrub_secrets_recursively(payload)
        msg_id = generate_collaboration_message_id()
        trace_id = correlation_id or f"corr_{uuid4().hex[:16]}"

        message = CollaborationMessage(
            message_id=msg_id,
            session_id=session_id,
            tenant_id=security_context.tenant_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            task_id=task_id,
            message_type=message_type,
            payload=sanitized_payload,
            correlation_id=trace_id,
            created_at=datetime.datetime.now(datetime.UTC),
        )

        saved = await self.repository.create_message(message)
        logger.info(
            "Message %s routed from %s to %s (type=%s) in session %s.",
            msg_id,
            sender_id,
            recipient_id,
            message_type.value,
            session_id,
        )
        return saved

    async def list_messages(
        self,
        session_id: str,
        security_context: CollaborationSecurityContext,
        task_id: str | None = None,
        limit: int = 50,
    ) -> list[CollaborationMessage]:
        """Lists messages for a session ensuring tenant isolation."""
        session = await self.repository.get_session(session_id, security_context.tenant_id)
        if not session:
            raise CollaborationSessionNotFoundError(session_id)

        return await self.repository.list_messages(
            session_id=session_id,
            tenant_id=security_context.tenant_id,
            task_id=task_id,
            limit=limit,
        )
