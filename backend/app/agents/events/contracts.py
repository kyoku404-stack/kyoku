"""KEEP Phase 4.10 — Event Contracts, Envelopes & Security Contexts.

Defines immutable event schemas (`KeepEvent`), delivery lifecycle statuses,
trusted caller security contexts, schema specifications, and webhook configs.

Owner: Member 1 (Event Contracts & Ingestion)
Specification: devdocs/p4/p4.10.txt (Sections 3, 4, 5, 11)
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

EventStatus = Literal["accepted", "processing", "processed", "dead_letter"]
DeliveryStatus = Literal["pending", "processing", "completed", "retry_scheduled", "dead_letter"]


def generate_event_id() -> str:
    return f"evt_{uuid4().hex[:16]}"


def generate_correlation_id() -> str:
    return f"corr_{uuid4().hex[:12]}"


def generate_delivery_id() -> str:
    return f"delv_{uuid4().hex[:16]}"


def generate_event_audit_id() -> str:
    return f"ev_aud_{uuid4().hex[:16]}"


def compute_event_fingerprint(
    event_type: str,
    schema_version: int,
    source: str,
    resource_id: str | None,
    payload: dict[str, Any],
) -> str:
    """Computes canonical SHA-256 fingerprint for idempotent event verification."""
    canonical = json.dumps(
        {
            "event_type": event_type,
            "schema_version": schema_version,
            "source": source,
            "resource_id": resource_id,
            "payload": payload,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class EventSecurityContext(BaseModel):
    """Server-side verified tenant and producer identity."""

    tenant_id: str = Field(..., min_length=1, max_length=128)
    user_id: str = Field(..., min_length=1, max_length=128)
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    trusted_source: str | None = Field(default=None, max_length=128)
    correlation_id: str | None = Field(default=None, max_length=128)


class KeepEvent(BaseModel):
    """Canonical data-only KEEP event envelope (never an agent instruction)."""

    event_id: str = Field(default_factory=generate_event_id, min_length=3, max_length=128)
    event_type: str = Field(..., min_length=3, max_length=128)
    schema_version: int = Field(default=1, ge=1, le=100)
    source: str = Field(..., min_length=2, max_length=128)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    published_at: datetime | None = None
    tenant_id: str = Field(..., min_length=1, max_length=128)
    resource_id: str | None = Field(default=None, max_length=128)
    correlation_id: str = Field(default_factory=generate_correlation_id, min_length=1, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)
    outbox_published: bool = True
    status: EventStatus = "accepted"

    @field_validator("event_type", "source")
    @classmethod
    def normalize_non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or whitespace.")
        return cleaned


class EventPublishRequest(BaseModel):
    """API / internal request to publish an event into KEEP ingestion."""

    event_id: str | None = Field(default=None, max_length=128)
    event_type: str = Field(..., min_length=3, max_length=128)
    schema_version: int = Field(default=1, ge=1, le=100)
    source: str = Field(default="keep.internal", min_length=2, max_length=128)
    occurred_at: datetime | None = None
    tenant_id: str | None = Field(default=None, max_length=128)
    resource_id: str | None = Field(default=None, max_length=128)
    correlation_id: str | None = Field(default=None, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)
    use_outbox: bool = False


class EventSchemaSpec(BaseModel):
    """Registered schema specification constraining valid event shapes."""

    event_type: str
    supported_versions: list[int] = Field(default_factory=lambda: [1])
    required_fields: list[str] = Field(default_factory=list)
    allowed_sources: list[str] = Field(default_factory=list)
    description: str = ""


class EventDeliveryRecord(BaseModel):
    """Durable queue delivery state for an accepted KeepEvent."""

    delivery_id: str = Field(default_factory=generate_delivery_id)
    event_id: str
    tenant_id: str
    status: DeliveryStatus = "pending"
    attempt: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=3, ge=1, le=10)
    worker_lease_until: datetime | None = None
    next_retry_at: datetime | None = None
    last_error: str | None = None
    is_permanent_failure: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EventAuditRecord(BaseModel):
    """Immutable audit trail entry for event & trigger lifecycle actions."""

    audit_id: str = Field(default_factory=generate_event_audit_id)
    tenant_id: str
    event_id: str | None = None
    trigger_id: str | None = None
    action: str
    actor_id: str
    reason: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WebhookSourceConfig(BaseModel):
    """Registered external webhook source credential & policy mapping."""

    source_id: str = Field(..., min_length=2, max_length=128)
    tenant_id: str = Field(..., min_length=1, max_length=128)
    secret: str = Field(..., min_length=8, max_length=256)
    event_type: str = Field(default="webhook.external.received")
    enabled: bool = True
    max_payload_bytes: int = Field(default=65536, ge=256, le=1_048_576)
    replay_window_seconds: int = Field(default=300, ge=30, le=3600)


class EventInspectionResponse(BaseModel):
    """Combined event state, delivery attempts, and matched dispatches."""

    event: KeepEvent
    deliveries: list[EventDeliveryRecord] = Field(default_factory=list)
    dispatches: list[dict[str, Any]] = Field(default_factory=list)


class WebhookReceipt(BaseModel):
    """Acknowledgement returned to an authenticated external webhook producer."""

    accepted: bool = True
    source_id: str
    event_id: str
    delivery_id: str
    deduplicated: bool = False
