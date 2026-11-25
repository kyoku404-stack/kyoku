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


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


class SqlAlchemyEventStore(BaseEventStore):
    """Durable PostgreSQL/SQLite repository for KEEP events, deliveries, and audits."""

    def __init__(self, session_factory: object | None = None) -> None:
        self._session_factory = session_factory
        self._fallback = InMemoryEventStore()

    @staticmethod
    def _to_event(row: object) -> KeepEvent:
        return KeepEvent(
            event_id=row.event_id,  # type: ignore[attr-defined]
            event_type=row.event_type,  # type: ignore[attr-defined]
            schema_version=row.schema_version,  # type: ignore[attr-defined]
            source=row.source,  # type: ignore[attr-defined]
            occurred_at=_ensure_utc(row.occurred_at) or datetime.now(UTC),  # type: ignore[attr-defined]
            published_at=_ensure_utc(row.published_at),  # type: ignore[attr-defined]
            tenant_id=row.tenant_id,  # type: ignore[attr-defined]
            resource_id=row.resource_id,  # type: ignore[attr-defined]
            correlation_id=row.correlation_id,  # type: ignore[attr-defined]
            payload=dict(row.payload or {}),  # type: ignore[attr-defined]
            outbox_published=bool(row.outbox_published),  # type: ignore[attr-defined]
            status=row.status,  # type: ignore[attr-defined]
        )

    @staticmethod
    def _to_delivery(row: object) -> EventDeliveryRecord:
        return EventDeliveryRecord(
            delivery_id=row.delivery_id,  # type: ignore[attr-defined]
            event_id=row.event_id,  # type: ignore[attr-defined]
            tenant_id=row.tenant_id,  # type: ignore[attr-defined]
            status=row.status,  # type: ignore[attr-defined]
            attempt=row.attempt,  # type: ignore[attr-defined]
            max_attempts=row.max_attempts,  # type: ignore[attr-defined]
            worker_lease_until=_ensure_utc(row.worker_lease_until),  # type: ignore[attr-defined]
            next_retry_at=_ensure_utc(row.next_retry_at),  # type: ignore[attr-defined]
            last_error=row.last_error,  # type: ignore[attr-defined]
            is_permanent_failure=bool(row.is_permanent_failure),  # type: ignore[attr-defined]
            created_at=_ensure_utc(row.created_at) or datetime.now(UTC),  # type: ignore[attr-defined]
            updated_at=_ensure_utc(row.updated_at) or datetime.now(UTC),  # type: ignore[attr-defined]
        )

    async def save_event_if_absent(self, event: KeepEvent) -> tuple[KeepEvent, bool]:
        if self._session_factory is None:
            return await self._fallback.save_event_if_absent(event)

        from backend.app.models.agent_triggers import AgentEventModel
        from sqlalchemy import select
        from sqlalchemy.exc import IntegrityError

        row = AgentEventModel(
            event_id=event.event_id,
            event_type=event.event_type,
            schema_version=event.schema_version,
            source=event.source,
            tenant_id=event.tenant_id,
            resource_id=event.resource_id,
            correlation_id=event.correlation_id,
            occurred_at=event.occurred_at,
            published_at=event.published_at or datetime.now(UTC),
            outbox_published=event.outbox_published,
            status=event.status,
            payload=dict(event.payload),
        )
        try:
            async with self._session_factory() as db:  # type: ignore[operator]
                db.add(row)
                await db.commit()
            return event.model_copy(deep=True), True
        except IntegrityError:
            async with self._session_factory() as db:  # type: ignore[operator]
                stmt = select(AgentEventModel).where(
                    AgentEventModel.event_id == event.event_id
                )
                existing = (await db.execute(stmt)).scalar_one()
                return self._to_event(existing), False

    async def get_event(self, event_id: str, tenant_id: str) -> KeepEvent | None:
        if self._session_factory is None:
            return await self._fallback.get_event(event_id, tenant_id)

        from backend.app.models.agent_triggers import AgentEventModel
        from sqlalchemy import select

        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = select(AgentEventModel).where(
                AgentEventModel.event_id == event_id,
                AgentEventModel.tenant_id == tenant_id,
            )
            row = (await db.execute(stmt)).scalar_one_or_none()
            return self._to_event(row) if row is not None else None

    async def update_event_status(
        self,
        event_id: str,
        tenant_id: str,
        status: EventStatus,
        *,
        outbox_published: bool | None = None,
    ) -> None:
        if self._session_factory is None:
            await self._fallback.update_event_status(
                event_id, tenant_id, status, outbox_published=outbox_published
            )
            return

        from backend.app.models.agent_triggers import AgentEventModel
        from sqlalchemy import select

        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = select(AgentEventModel).where(
                AgentEventModel.event_id == event_id,
                AgentEventModel.tenant_id == tenant_id,
            )
            row = (await db.execute(stmt)).scalar_one_or_none()
            if row is not None:
                row.status = status
                if outbox_published is not None:
                    row.outbox_published = outbox_published
                await db.commit()

    async def list_unpublished_outbox(self, tenant_id: str | None = None) -> list[KeepEvent]:
        if self._session_factory is None:
            return await self._fallback.list_unpublished_outbox(tenant_id=tenant_id)

        from backend.app.models.agent_triggers import AgentEventModel
        from sqlalchemy import select

        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = select(AgentEventModel).where(AgentEventModel.outbox_published.is_(False))
            if tenant_id is not None:
                stmt = stmt.where(AgentEventModel.tenant_id == tenant_id)
            rows = (await db.execute(stmt)).scalars().all()
            return [self._to_event(r) for r in rows]

    async def create_delivery(self, delivery: EventDeliveryRecord) -> EventDeliveryRecord:
        if self._session_factory is None:
            return await self._fallback.create_delivery(delivery)

        from backend.app.models.agent_triggers import EventDeliveryModel

        async with self._session_factory() as db:  # type: ignore[operator]
            db.add(
                EventDeliveryModel(
                    delivery_id=delivery.delivery_id,
                    event_id=delivery.event_id,
                    tenant_id=delivery.tenant_id,
                    status=delivery.status,
                    attempt=delivery.attempt,
                    max_attempts=delivery.max_attempts,
                    worker_lease_until=delivery.worker_lease_until,
                    next_retry_at=delivery.next_retry_at,
                    last_error=delivery.last_error,
                    is_permanent_failure=delivery.is_permanent_failure,
                    created_at=delivery.created_at,
                    updated_at=delivery.updated_at,
                )
            )
            await db.commit()
        return delivery.model_copy(deep=True)

    async def get_delivery(self, delivery_id: str, tenant_id: str) -> EventDeliveryRecord | None:
        if self._session_factory is None:
            return await self._fallback.get_delivery(delivery_id, tenant_id)

        from backend.app.models.agent_triggers import EventDeliveryModel
        from sqlalchemy import select

        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = select(EventDeliveryModel).where(
                EventDeliveryModel.delivery_id == delivery_id,
                EventDeliveryModel.tenant_id == tenant_id,
            )
            row = (await db.execute(stmt)).scalar_one_or_none()
            return self._to_delivery(row) if row is not None else None

    async def list_deliveries_for_event(
        self, event_id: str, tenant_id: str
    ) -> list[EventDeliveryRecord]:
        if self._session_factory is None:
            return await self._fallback.list_deliveries_for_event(event_id, tenant_id)

        from backend.app.models.agent_triggers import EventDeliveryModel
        from sqlalchemy import select

        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = select(EventDeliveryModel).where(
                EventDeliveryModel.event_id == event_id,
                EventDeliveryModel.tenant_id == tenant_id,
            )
            rows = (await db.execute(stmt)).scalars().all()
            return [self._to_delivery(r) for r in rows]

    async def list_due_deliveries(
        self, *, now: datetime | None = None, limit: int = 50
    ) -> list[EventDeliveryRecord]:
        if self._session_factory is None:
            return await self._fallback.list_due_deliveries(now=now, limit=limit)

        from backend.app.models.agent_triggers import EventDeliveryModel
        from sqlalchemy import or_, select

        current = now or datetime.now(UTC)
        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = (
                select(EventDeliveryModel)
                .where(
                    or_(
                        EventDeliveryModel.status == "pending",
                        (EventDeliveryModel.status == "retry_scheduled")
                        & (
                            (EventDeliveryModel.next_retry_at.is_(None))
                            | (EventDeliveryModel.next_retry_at <= current)
                        ),
                        (EventDeliveryModel.status == "processing")
                        & (EventDeliveryModel.worker_lease_until.is_not(None))
                        & (EventDeliveryModel.worker_lease_until <= current),
                    )
                )
                .order_by(EventDeliveryModel.created_at.asc())
                .limit(limit)
            )
            rows = (await db.execute(stmt)).scalars().all()
            return [self._to_delivery(r) for r in rows]

    async def list_dead_letter_deliveries(
        self, tenant_id: str, limit: int = 50
    ) -> list[EventDeliveryRecord]:
        if self._session_factory is None:
            return await self._fallback.list_dead_letter_deliveries(tenant_id, limit=limit)

        from backend.app.models.agent_triggers import EventDeliveryModel
        from sqlalchemy import select

        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = (
                select(EventDeliveryModel)
                .where(
                    EventDeliveryModel.tenant_id == tenant_id,
                    EventDeliveryModel.status == "dead_letter",
                )
                .order_by(EventDeliveryModel.updated_at.desc())
                .limit(limit)
            )
            rows = (await db.execute(stmt)).scalars().all()
            return [self._to_delivery(r) for r in rows]

    async def update_delivery(self, delivery: EventDeliveryRecord) -> EventDeliveryRecord:
        if self._session_factory is None:
            return await self._fallback.update_delivery(delivery)

        from backend.app.models.agent_triggers import EventDeliveryModel
        from sqlalchemy import select

        now = datetime.now(UTC)
        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = select(EventDeliveryModel).where(
                EventDeliveryModel.delivery_id == delivery.delivery_id,
                EventDeliveryModel.tenant_id == delivery.tenant_id,
            )
            row = (await db.execute(stmt)).scalar_one_or_none()
            if row is not None:
                row.status = delivery.status
                row.attempt = delivery.attempt
                row.worker_lease_until = delivery.worker_lease_until
                row.next_retry_at = delivery.next_retry_at
                row.last_error = delivery.last_error
                row.is_permanent_failure = delivery.is_permanent_failure
                row.updated_at = now
                await db.commit()
        res = delivery.model_copy(deep=True)
        res.updated_at = now
        return res

    async def claim_delivery_lease(
        self,
        delivery_id: str,
        *,
        lease_until: datetime,
        now: datetime | None = None,
    ) -> EventDeliveryRecord | None:
        if self._session_factory is None:
            return await self._fallback.claim_delivery_lease(
                delivery_id, lease_until=lease_until, now=now
            )

        from backend.app.models.agent_triggers import EventDeliveryModel
        from sqlalchemy import select

        current = now or datetime.now(UTC)
        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = select(EventDeliveryModel).where(EventDeliveryModel.delivery_id == delivery_id)
            row = (await db.execute(stmt)).scalar_one_or_none()
            if row is None:
                return None
            lease_exp = row.status == "processing" and (
                row.worker_lease_until is not None
                and (_ensure_utc(row.worker_lease_until) or current) <= current
            )
            if row.status not in ("pending", "retry_scheduled") and not lease_exp:
                return None
            row.status = "processing"
            row.worker_lease_until = lease_until
            row.updated_at = current
            await db.commit()
            return self._to_delivery(row)

    async def append_audit(self, audit: EventAuditRecord) -> EventAuditRecord:
        if self._session_factory is None:
            return await self._fallback.append_audit(audit)

        from backend.app.models.agent_triggers import EventAuditLogModel

        async with self._session_factory() as db:  # type: ignore[operator]
            db.add(
                EventAuditLogModel(
                    audit_id=audit.audit_id,
                    tenant_id=audit.tenant_id,
                    event_id=audit.event_id,
                    trigger_id=audit.trigger_id,
                    action=audit.action,
                    actor_id=audit.actor_id,
                    reason=audit.reason,
                    details=dict(audit.details),
                    created_at=audit.created_at,
                )
            )
            await db.commit()
        return audit.model_copy(deep=True)

    async def list_audits(
        self,
        tenant_id: str,
        *,
        event_id: str | None = None,
        trigger_id: str | None = None,
        limit: int = 100,
    ) -> list[EventAuditRecord]:
        if self._session_factory is None:
            return await self._fallback.list_audits(
                tenant_id, event_id=event_id, trigger_id=trigger_id, limit=limit
            )

        from backend.app.models.agent_triggers import EventAuditLogModel
        from sqlalchemy import select

        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = (
                select(EventAuditLogModel)
                .where(EventAuditLogModel.tenant_id == tenant_id)
                .order_by(EventAuditLogModel.created_at.asc())
                .limit(limit)
            )
            if event_id is not None:
                stmt = stmt.where(EventAuditLogModel.event_id == event_id)
            if trigger_id is not None:
                stmt = stmt.where(EventAuditLogModel.trigger_id == trigger_id)
            rows = (await db.execute(stmt)).scalars().all()
            return [
                EventAuditRecord(
                    audit_id=r.audit_id,
                    tenant_id=r.tenant_id,
                    event_id=r.event_id,
                    trigger_id=r.trigger_id,
                    action=r.action,
                    actor_id=r.actor_id,
                    reason=r.reason,
                    details=dict(r.details or {}),
                    created_at=_ensure_utc(r.created_at) or datetime.now(UTC),
                )
                for r in rows
            ]
