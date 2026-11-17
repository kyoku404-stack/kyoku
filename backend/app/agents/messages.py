"""KEEP Phase 4.1 — Inter-Agent Communication Message Contracts.

Defines versioned, tenant-scoped message envelopes and handoff payloads to
support future multi-agent orchestration (Phase 4.3) and collaboration
(Phase 4.8) without redesigning identifiers or tracing semantics.

Owner: Member 2 (Agent Contracts & Communication)
Specification: devdocs/p4/p4.1.txt (Sections 1, 3, 9)
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from backend.app.agents.contracts import (
    AGENT_CONTRACT_SCHEMA_VERSION,
    EvidenceReference,
    validate_contract_schema_version,
)
from backend.app.agents.errors import AgentErrorDetail
from pydantic import BaseModel, Field, field_validator


def generate_message_id() -> str:
    """Generates a unique inter-agent message identifier."""
    return f"msg_{uuid4().hex}"


class MessageType(str, Enum):
    """Canonical inter-agent envelope types."""

    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    HANDOFF = "handoff"
    EVENT = "event"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class MessagePriority(str, Enum):
    """Delivery priority hints for future Phase 4.3/4.8 message routing."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class AgentParticipant(BaseModel):
    """Identifies the sender or recipient of an inter-agent message."""

    agent_id: str = Field(..., min_length=1, max_length=64)
    role: str = Field(default="agent", max_length=64)
    version: str | None = Field(default=None, max_length=32)

    @field_validator("agent_id")
    @classmethod
    def normalize_agent_id(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("AgentParticipant.agent_id cannot be empty.")
        return cleaned


class AgentHandoffPayload(BaseModel):
    """Validated handoff payload passed between two agents in a multi-agent workflow."""

    summary: str = Field(..., min_length=1, max_length=4096)
    artifacts: dict[str, Any] = Field(default_factory=dict)
    next_goal: str | None = Field(default=None, max_length=2048)
    required_capabilities: list[str] = Field(default_factory=list)


class AgentMessageEnvelope(BaseModel):
    """Standard tenant-scoped, correlation-tracked inter-agent communication envelope."""

    message_id: str = Field(default_factory=generate_message_id, min_length=1, max_length=128)
    correlation_id: str = Field(..., min_length=1, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    task_id: str = Field(..., min_length=1, max_length=128)
    tenant_id: str = Field(..., min_length=1, max_length=128)
    sender: AgentParticipant
    recipient: AgentParticipant
    message_type: MessageType
    priority: MessagePriority = Field(default=MessagePriority.NORMAL)
    payload: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    error: AgentErrorDetail | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ttl_seconds: int = Field(default=300, ge=1, le=86400)
    schema_version: str = Field(default=AGENT_CONTRACT_SCHEMA_VERSION)

    @field_validator("correlation_id", "task_id", "tenant_id")
    @classmethod
    def validate_non_empty_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Message routing identifier cannot be empty.")
        return cleaned

    @field_validator("schema_version")
    @classmethod
    def check_schema_version(cls, value: str) -> str:
        return validate_contract_schema_version(value)

    def create_reply(
        self,
        *,
        message_type: MessageType = MessageType.TASK_RESPONSE,
        payload: dict[str, Any] | None = None,
        evidence: list[EvidenceReference] | None = None,
        error: AgentErrorDetail | None = None,
    ) -> AgentMessageEnvelope:
        """Builds a reply envelope preserving tenant_id, task_id, correlation_id, and causation lineage."""
        return AgentMessageEnvelope(
            correlation_id=self.correlation_id,
            causation_id=self.message_id,
            task_id=self.task_id,
            tenant_id=self.tenant_id,
            sender=self.recipient,
            recipient=self.sender,
            message_type=message_type,
            priority=self.priority,
            payload=payload or {},
            evidence=evidence or [],
            error=error,
            schema_version=self.schema_version,
        )
