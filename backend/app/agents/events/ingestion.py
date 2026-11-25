"""KEEP Phase 4.10 — Event Ingestion Service.

Enforces server-side tenant binding, validates event schemas & payload hygiene,
preserves correlation/schema metadata, supports idempotent event acceptance,
and enqueues durable delivery records.

Owner: Member 1 (Event Contracts & Ingestion)
Specification: devdocs/p4/p4.10.txt (Sections 3, 5, 7)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.app.agents.errors import (
    EventDuplicateError,
    EventNotFoundError,
    EventTenantMismatchError,
    EventValidationError,
)
from backend.app.agents.events.contracts import (
    EventAuditRecord,
    EventDeliveryRecord,
    EventPublishRequest,
    EventSecurityContext,
    KeepEvent,
    compute_event_fingerprint,
    generate_correlation_id,
    generate_event_id,
)
from backend.app.agents.events.event_store import BaseEventStore, InMemoryEventStore
from backend.app.agents.events.validation import EventSchemaRegistry, EventValidator


class EventIngestionService:
    """Zero-trust ingestion entrypoint converting validated triggers/events into durable queue items."""

    def __init__(
        self,
        event_store: BaseEventStore | None = None,
        *,
        schema_registry: EventSchemaRegistry | None = None,
        validator: EventValidator | None = None,
        on_delivery_enqueued: Any | None = None,
    ) -> None:
        self.event_store = event_store or InMemoryEventStore()
        self.schema_registry = schema_registry or EventSchemaRegistry()
        self.validator = validator or EventValidator(self.schema_registry)
        self.on_delivery_enqueued = on_delivery_enqueued

    async def ingest(
        self,
        request: EventPublishRequest,
        security_context: EventSecurityContext,
    ) -> tuple[KeepEvent, EventDeliveryRecord, bool]:
        """Validates, deduplicates, stores, and queues an incoming event.

        Returns `(event, delivery, deduplicated)`.
        """
        # Zero-trust tenant derivation: never accept payload overriding verified caller tenant
        if request.tenant_id is not None and request.tenant_id != security_context.tenant_id:
            await self.event_store.append_audit(
                EventAuditRecord(
                    tenant_id=security_context.tenant_id,
                    event_id=request.event_id,
                    action="event.rejected",
                    actor_id=security_context.user_id,
                    reason="Tenant spoofing rejected: payload tenant_id mismatches verified caller.",
                )
            )
            raise EventTenantMismatchError(security_context.tenant_id, request.tenant_id)

        source = security_context.trusted_source or request.source
        now = datetime.now(UTC)
        event_id = (request.event_id or "").strip() or generate_event_id()
        correlation_id = (
            (request.correlation_id or "").strip()
            or security_context.correlation_id
            or generate_correlation_id()
        )
        occurred_at = request.occurred_at or now
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=UTC)

        candidate = KeepEvent(
            event_id=event_id,
            event_type=request.event_type,
            schema_version=request.schema_version,
            source=source,
            occurred_at=occurred_at,
            published_at=now,
            tenant_id=security_context.tenant_id,
            resource_id=request.resource_id,
            correlation_id=correlation_id,
            payload=dict(request.payload),
            outbox_published=not request.use_outbox,
            status="accepted",
        )

        # Reject malformed / schema-invalid events BEFORE persistence/queueing
        try:
            self.validator.validate(candidate)
        except EventValidationError as exc:
            await self.event_store.append_audit(
                EventAuditRecord(
                    tenant_id=security_context.tenant_id,
                    event_id=candidate.event_id,
                    action="event.rejected",
                    actor_id=security_context.user_id,
                    reason=str(exc),
                    details={"event_type": candidate.event_type},
                )
            )
            raise

        # Cross-tenant collision guard: check existing event scope cleanly via save_event_if_absent
        saved_event, created = await self.event_store.save_event_if_absent(candidate)
        if not created:
            if saved_event.tenant_id != security_context.tenant_id:
                raise EventDuplicateError(event_id)
            req_fp = compute_event_fingerprint(
                candidate.event_type,
                candidate.schema_version,
                candidate.source,
                candidate.resource_id,
                candidate.payload,
            )
            saved_fp = compute_event_fingerprint(
                saved_event.event_type,
                saved_event.schema_version,
                saved_event.source,
                saved_event.resource_id,
                saved_event.payload,
            )
            if req_fp != saved_fp:
                raise EventDuplicateError(event_id)
            deliveries = await self.event_store.list_deliveries_for_event(
                saved_event.event_id, saved_event.tenant_id
            )
            delivery = (
                deliveries[0]
                if deliveries
                else EventDeliveryRecord(
                    event_id=saved_event.event_id, tenant_id=saved_event.tenant_id
                )
            )
            await self.event_store.append_audit(
                EventAuditRecord(
                    tenant_id=security_context.tenant_id,
                    event_id=saved_event.event_id,
                    action="event.deduplicated",
                    actor_id=security_context.user_id,
                    reason="Idempotent duplicate event delivery accepted without creating extra dispatch.",
                )
            )
            return saved_event, delivery, True

        delivery: EventDeliveryRecord
        if request.use_outbox:
            # Transactional outbox: deferred delivery creation handled by OutboxEventRelay
            delivery = EventDeliveryRecord(
                event_id=saved_event.event_id,
                tenant_id=saved_event.tenant_id,
                status="pending",
            )
        else:
            delivery = await self.event_store.create_delivery(
                EventDeliveryRecord(
                    event_id=saved_event.event_id,
                    tenant_id=saved_event.tenant_id,
                    status="pending",
                )
            )
            if self.on_delivery_enqueued is not None:
                await self.on_delivery_enqueued(saved_event, delivery)

        await self.event_store.append_audit(
            EventAuditRecord(
                tenant_id=security_context.tenant_id,
                event_id=saved_event.event_id,
                action="event.accepted",
                actor_id=security_context.user_id,
                reason=f"Accepted event '{saved_event.event_type}' (v{saved_event.schema_version}).",
                details={"delivery_id": delivery.delivery_id, "use_outbox": request.use_outbox},
            )
        )
        return saved_event, delivery, False

    async def get_event(
        self,
        event_id: str,
        security_context: EventSecurityContext,
    ) -> KeepEvent:
        ev = await self.event_store.get_event(event_id, security_context.tenant_id)
        if ev is None:
            raise EventNotFoundError(event_id)
        return ev
