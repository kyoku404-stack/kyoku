"""KEEP Phase 4.10 — Event Store Protocol & In-Memory Store.

Stores accepted KeepEvents, pending queue deliveries, outbox events, and
append-only event audit records scoped strictly by tenant_id.

Owner: Member 1 (Core Ingestion) / Member 3 (Queue Reliability)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime

from backend.app.agents.events.contracts import (
    DeliveryStatus,
    EventAuditRecord,
    EventDeliveryRecord,
    EventStatus,
    KeepEvent,
)


class BaseEventStore(ABC):
    """Abstract tenant-scoped storage interface for KEEP events and deliveries."""

    @abstractmethod
    async def save_event_if_absent(self, event: KeepEvent) -> tuple[KeepEvent, bool]:
        """Atomically persists event if event_id is new; returns (event, created_bool)."""

    @abstractmethod
    async def get_event(self, event_id: str, tenant_id: str) -> KeepEvent | None: ...

    @abstractmethod
    async def update_event_status(
        self, event_id: str, tenant_id: str, status: EventStatus, *, outbox_published: bool | None = None
    ) -> None: ...

    @abstractmethod
    async def list_unpublished_outbox(self, tenant_id: str | None = None) -> list[KeepEvent]: ...

    @abstractmethod
    async def create_delivery(self, delivery: EventDeliveryRecord) -> EventDeliveryRecord: ...

    @abstractmethod
    async def get_delivery(self, delivery_id: str, tenant_id: str) -> EventDeliveryRecord | None: ...

    @abstractmethod
    async def list_deliveries_for_event(
        self, event_id: str, tenant_id: str
    ) -> list[EventDeliveryRecord]: ...

    @abstractmethod
    async def list_due_deliveries(
        self, *, now: datetime | None = None, limit: int = 50
    ) -> list[EventDeliveryRecord]: ...

    @abstractmethod
    async def list_dead_letter_deliveries(
        self, tenant_id: str, limit: int = 50
    ) -> list[EventDeliveryRecord]: ...

    @abstractmethod
    async def update_delivery(self, delivery: EventDeliveryRecord) -> EventDeliveryRecord: ...

    @abstractmethod
    async def claim_delivery_lease(
        self,
        delivery_id: str,
        *,
        lease_until: datetime,
        now: datetime | None = None,
    ) -> EventDeliveryRecord | None: ...

    @abstractmethod
    async def append_audit(self, audit: EventAuditRecord) -> EventAuditRecord: ...

    @abstractmethod
    async def list_audits(
        self,
        tenant_id: str,
        *,
        event_id: str | None = None,
        trigger_id: str | None = None,
        limit: int = 100,
    ) -> list[EventAuditRecord]: ...


class InMemoryEventStore(BaseEventStore):
    """Deterministic in-memory event & delivery store for unit testing and fallback."""

    def __init__(self) -> None:
        self._events: dict[str, KeepEvent] = {}
        self._deliveries: dict[str, EventDeliveryRecord] = {}
        self._audits: list[EventAuditRecord] = []

    async def save_event_if_absent(self, event: KeepEvent) -> tuple[KeepEvent, bool]:
        existing = self._events.get(event.event_id)
        if existing is not None:
            return existing.model_copy(deep=True), False
        copy = event.model_copy(deep=True)
        self._events[event.event_id] = copy
        return copy.model_copy(deep=True), True

    async def get_event(self, event_id: str, tenant_id: str) -> KeepEvent | None:
        ev = self._events.get(event_id)
        if ev is None or ev.tenant_id != tenant_id:
            return None
        return ev.model_copy(deep=True)

    async def update_event_status(
        self,
        event_id: str,
        tenant_id: str,
        status: EventStatus,
        *,
        outbox_published: bool | None = None,
    ) -> None:
        ev = self._events.get(event_id)
        if ev is not None and ev.tenant_id == tenant_id:
            ev.status = status
            if outbox_published is not None:
                ev.outbox_published = outbox_published

    async def list_unpublished_outbox(self, tenant_id: str | None = None) -> list[KeepEvent]:
        return [
            ev.model_copy(deep=True)
            for ev in self._events.values()
            if not ev.outbox_published and (tenant_id is None or ev.tenant_id == tenant_id)
        ]

    async def create_delivery(self, delivery: EventDeliveryRecord) -> EventDeliveryRecord:
        copy = delivery.model_copy(deep=True)
        self._deliveries[copy.delivery_id] = copy
        return copy.model_copy(deep=True)

    async def get_delivery(self, delivery_id: str, tenant_id: str) -> EventDeliveryRecord | None:
        d = self._deliveries.get(delivery_id)
        if d is None or d.tenant_id != tenant_id:
            return None
        return d.model_copy(deep=True)

    async def list_deliveries_for_event(
        self, event_id: str, tenant_id: str
    ) -> list[EventDeliveryRecord]:
        return [
            d.model_copy(deep=True)
            for d in self._deliveries.values()
            if d.event_id == event_id and d.tenant_id == tenant_id
        ]

    async def list_due_deliveries(
        self, *, now: datetime | None = None, limit: int = 50
    ) -> list[EventDeliveryRecord]:
        current = now or datetime.now(UTC)
        results: list[EventDeliveryRecord] = []
        for d in self._deliveries.values():
            if d.status in ("pending", "retry_scheduled"):
                if d.next_retry_at is None or d.next_retry_at <= current:
                    results.append(d.model_copy(deep=True))
            elif (
                d.status == "processing"
                and d.worker_lease_until is not None
                and d.worker_lease_until <= current
            ):
                results.append(d.model_copy(deep=True))
        results.sort(key=lambda item: item.created_at)
        return results[:limit]

    async def list_dead_letter_deliveries(
        self, tenant_id: str, limit: int = 50
    ) -> list[EventDeliveryRecord]:
        items = [
            d.model_copy(deep=True)
            for d in self._deliveries.values()
            if d.tenant_id == tenant_id and d.status == "dead_letter"
        ]
        items.sort(key=lambda item: item.updated_at, reverse=True)
        return items[:limit]

    async def update_delivery(self, delivery: EventDeliveryRecord) -> EventDeliveryRecord:
        existing = self._deliveries.get(delivery.delivery_id)
        if existing is not None and existing.tenant_id == delivery.tenant_id:
            updated = delivery.model_copy(deep=True)
            updated.updated_at = datetime.now(UTC)
            self._deliveries[delivery.delivery_id] = updated
            return updated.model_copy(deep=True)
        return delivery.model_copy(deep=True)

    async def claim_delivery_lease(
        self,
        delivery_id: str,
        *,
        lease_until: datetime,
        now: datetime | None = None,
    ) -> EventDeliveryRecord | None:
        current = now or datetime.now(UTC)
        d = self._deliveries.get(delivery_id)
        if d is None:
            return None
        claimable_statuses: tuple[DeliveryStatus, ...] = ("pending", "retry_scheduled")
        lease_expired = d.status == "processing" and (
            d.worker_lease_until is not None and d.worker_lease_until <= current
        )
        if d.status not in claimable_statuses and not lease_expired:
            return None
        d.status = "processing"
        d.worker_lease_until = lease_until
        d.updated_at = current
        return d.model_copy(deep=True)

    async def append_audit(self, audit: EventAuditRecord) -> EventAuditRecord:
        copy = audit.model_copy(deep=True)
        self._audits.append(copy)
        return copy.model_copy(deep=True)

    async def list_audits(
        self,
        tenant_id: str,
        *,
        event_id: str | None = None,
        trigger_id: str | None = None,
        limit: int = 100,
    ) -> list[EventAuditRecord]:
        items = [
            a.model_copy(deep=True)
            for a in self._audits
            if a.tenant_id == tenant_id
            and (event_id is None or a.event_id == event_id)
            and (trigger_id is None or a.trigger_id == trigger_id)
        ]
        return items[-limit:]
