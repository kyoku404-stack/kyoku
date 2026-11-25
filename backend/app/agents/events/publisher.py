"""KEEP Phase 4.10 — Internal Event Publisher & Transactional Outbox Relay.

Provides clean publisher interfaces so KEEP services (Documents, Ingestion,
Connectors, Scheduled Jobs) publish events safely into the ingestion pipeline.

Owner: Member 1 (Event Contracts & Ingestion)
Specification: devdocs/p4/p4.10.txt (Sections 3, 7)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol, runtime_checkable

from backend.app.agents.events.contracts import (
    EventDeliveryRecord,
    EventPublishRequest,
    EventSecurityContext,
    KeepEvent,
)
from backend.app.agents.events.event_store import BaseEventStore


@runtime_checkable
class EventPublisherInterface(Protocol):
    """Protocol for publishing validated KEEP events into the trigger pipeline."""

    async def publish(
        self,
        request: EventPublishRequest,
        security_context: EventSecurityContext,
    ) -> tuple[KeepEvent, EventDeliveryRecord, bool]: ...


class InternalEventPublisher:
    """Publishes internal KEEP events via registered ingestion callback."""

    def __init__(
        self,
        ingest_fn: Callable[
            [EventPublishRequest, EventSecurityContext],
            Awaitable[tuple[KeepEvent, EventDeliveryRecord, bool]],
        ],
    ) -> None:
        self._ingest_fn = ingest_fn

    async def publish(
        self,
        request: EventPublishRequest,
        security_context: EventSecurityContext,
    ) -> tuple[KeepEvent, EventDeliveryRecord, bool]:
        return await self._ingest_fn(request, security_context)


class OutboxEventRelay:
    """Relays transactional outbox events (`outbox_published=False`) into queued deliveries."""

    def __init__(self, event_store: BaseEventStore) -> None:
        self.event_store = event_store

    async def relay_pending(self, *, tenant_id: str | None = None) -> list[EventDeliveryRecord]:
        unpublished = await self.event_store.list_unpublished_outbox(tenant_id=tenant_id)
        created_deliveries: list[EventDeliveryRecord] = []
        for event in unpublished:
            existing = await self.event_store.list_deliveries_for_event(
                event.event_id, event.tenant_id
            )
            if not existing:
                delivery = await self.event_store.create_delivery(
                    EventDeliveryRecord(
                        event_id=event.event_id,
                        tenant_id=event.tenant_id,
                    )
                )
                created_deliveries.append(delivery)
            await self.event_store.update_event_status(
                event.event_id,
                event.tenant_id,
                event.status,
                outbox_published=True,
            )
        return created_deliveries
