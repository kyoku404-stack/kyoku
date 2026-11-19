"""KEEP Phase 4.6 — Tool Audit & Security Logging Service.

Records all tool invocation attempts, authorization decisions, denials,
and outputs with strict secret redaction and fail-closed security.
"""

from __future__ import annotations

import collections
import datetime
import logging
import uuid
from typing import Any

from backend.app.agents.errors import sanitize_error_message
from backend.app.agents.tools.contracts import (
    ToolCallRequest,
    ToolCallResult,
    ToolContext,
)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ToolAuditEvent(BaseModel):
    """Immutable audit record for a tool invocation decision or execution."""

    event_id: str = Field(default_factory=lambda: f"aud_{uuid.uuid4().hex[:12]}")
    call_id: str
    tenant_id: str
    user_id: str
    tool_id: str
    decision: str  # "allowed", "denied", "approval_required", "succeeded", "failed", "timed_out"
    reason_code: str
    timestamp: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat()
    )
    details: dict[str, Any] = Field(default_factory=dict)


def _sanitize_payload(payload: Any) -> Any:
    """Recursively redacts secrets from dictionary or list values."""
    if isinstance(payload, str):
        return sanitize_error_message(payload)
    if isinstance(payload, dict):
        sanitized: dict[str, Any] = {}
        for k, v in payload.items():
            if any(s in k.lower() for s in ("token", "secret", "password", "key", "auth")):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = _sanitize_payload(v)
        return sanitized
    if isinstance(payload, (list, tuple)):
        return [_sanitize_payload(item) for item in payload]
    return payload


class ToolAuditService:
    """Security audit event service for platform tool calls."""

    def __init__(self, max_buffer_size: int = 1000) -> None:
        self._events: collections.deque[ToolAuditEvent] = collections.deque(maxlen=max_buffer_size)

    async def record_invocation(
        self,
        request: ToolCallRequest,
        context: ToolContext,
        result: ToolCallResult,
    ) -> ToolAuditEvent:
        """Records an invocation attempt and its execution result."""
        decision_map = {
            "succeeded": "allowed",
            "denied": "denied",
            "approval_required": "approval_required",
            "timed_out": "failed",
            "failed": "failed",
        }
        decision = decision_map.get(result.status, "unknown")
        reason_code = result.error_code or ("SUCCESS" if result.status == "succeeded" else "UNKNOWN")

        event = ToolAuditEvent(
            call_id=request.call_id,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            tool_id=request.tool_id,
            decision=decision,
            reason_code=reason_code,
            details={
                "status": result.status,
                "duration_ms": result.duration_ms,
                "agent_execution_id": context.agent_execution_id,
                "workflow_execution_id": context.workflow_execution_id,
                "correlation_id": context.correlation_id,
                "input_summary": _sanitize_payload(request.arguments),
                "error_message": result.error_message,
            },
        )
        self._events.append(event)
        logger.info(
            "Audit record [%s]: tool=%s tenant=%s user=%s decision=%s reason=%s",
            event.event_id,
            event.tool_id,
            event.tenant_id,
            event.user_id,
            event.decision,
            event.reason_code,
        )
        return event

    async def record_denial(
        self,
        request: ToolCallRequest,
        context: ToolContext,
        reason: str,
        reason_code: str = "TOOL_PERMISSION_DENIED",
        details: dict[str, Any] | None = None,
    ) -> ToolAuditEvent:
        """Explicit helper to record policy or security authorization denials."""
        combined_details = {
            "reason": sanitize_error_message(reason),
            "input_summary": _sanitize_payload(request.arguments),
            "agent_execution_id": context.agent_execution_id,
            "correlation_id": context.correlation_id,
        }
        if details:
            combined_details.update(details)

        event = ToolAuditEvent(
            call_id=request.call_id,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            tool_id=request.tool_id,
            decision="denied",
            reason_code=reason_code,
            details=combined_details,
        )
        self._events.append(event)
        return event

    def get_audit_events(
        self,
        tenant_id: str,
        tool_id: str | None = None,
        limit: int = 50,
    ) -> list[ToolAuditEvent]:
        """Retrieves tenant-isolated audit event history."""
        results: list[ToolAuditEvent] = []
        for evt in reversed(self._events):
            if evt.tenant_id == tenant_id and (tool_id is None or evt.tool_id == tool_id):
                results.append(evt)
                if len(results) >= limit:
                    break
        return results
