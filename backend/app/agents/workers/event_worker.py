"""KEEP Phase 4.10 — Durable Event Queue Worker, Retries & Dead-Letter Handling.

Polls/processes pending event deliveries with atomic lease claims, distinguishes
retryable failures from permanent failures, applies bounded exponential backoff
with jitter, routes dead-lettered items safely, and supports crash recovery & DLQ replay.

Owner: Member 3 (Queue, Scheduling & Reliability)
Specification: devdocs/p4/p4.10.txt (Section 7)
"""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from backend.app.agents.errors import (
    AgentLayerError,
    EventNotFoundError,
    EventValidationError,
    TriggerAccessDeniedError,
    TriggerWorkflowNotAllowedError,
)
from backend.app.agents.events.contracts import (
    EventAuditRecord,
    EventDeliveryRecord,
    EventSecurityContext,
    KeepEvent,
)
from backend.app.agents.events.event_store import BaseEventStore

logger = logging.getLogger("agents.workers.event_worker")


class PermanentDeliveryError(RuntimeError):
    """Explicit marker for non-retryable delivery errors routed directly to DLQ."""


class RetryableDeliveryError(RuntimeError):
    """Explicit marker for transient dependency failures eligible for backoff retry."""


DeliveryHandler = Callable[[KeepEvent, EventDeliveryRecord], Awaitable[None]]


class EventQueueWorker:
    """Durable queue processor managing leases, exponential backoff, DLQ, and crash recovery."""

    def __init__(
        self,
        event_store: BaseEventStore,
        *,
        handler: DeliveryHandler | None = None,
        lease_seconds: int = 30,
        base_backoff_seconds: float = 2.0,
        max_backoff_seconds: float = 120.0,
        poll_interval_seconds: float = 0.25,
    ) -> None:
        self.event_store = event_store
        self._handler = handler
        self.lease_seconds = lease_seconds
        self.base_backoff_seconds = base_backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self._running = False
        self._task: asyncio.Task[None] | None = None

    def bind_handler(self, handler: DeliveryHandler) -> None:
        self._handler = handler

    @staticmethod
    def is_permanent_error(exc: Exception) -> bool:
        return isinstance(
            exc,
            (
                PermanentDeliveryError,
                EventValidationError,
                TriggerAccessDeniedError,
                TriggerWorkflowNotAllowedError,
                ValueError,
                TypeError,
            ),
        )

    def compute_backoff(self, attempt: int) -> timedelta:
        """Bounded exponential backoff with jitter: `min(cap, base * 2^(attempt-1) + jitter)`."""
        raw = self.base_backoff_seconds * (2 ** max(0, attempt - 1))
        jitter = random.uniform(0.0, 0.5)
        seconds = min(self.max_backoff_seconds, raw + jitter)
        return timedelta(seconds=seconds)

    async def process_delivery(
        self,
        delivery_id: str,
        tenant_id: str,
        *,
        now: datetime | None = None,
    ) -> EventDeliveryRecord:
        """Claims lease, executes bound handler, and handles success / retry / DLQ transition."""
        current = now or datetime.now(UTC)
        claimed = await self.event_store.claim_delivery_lease(
            delivery_id,
            lease_until=current + timedelta(seconds=self.lease_seconds),
            now=current,
        )
        if claimed is None:
            existing = await self.event_store.get_delivery(delivery_id, tenant_id)
            if existing is None:
                raise EventNotFoundError(delivery_id)
            return existing

        event = await self.event_store.get_event(claimed.event_id, claimed.tenant_id)
        if event is None:
            raise EventNotFoundError(claimed.event_id)

        claimed.attempt += 1
        try:
            await self.event_store.update_event_status(
                event.event_id, event.tenant_id, "processing"
            )
            if self._handler is not None:
                await self._handler(event, claimed)
            claimed.status = "completed"
            claimed.worker_lease_until = None
            claimed.next_retry_at = None
            claimed.last_error = None
            updated = await self.event_store.update_delivery(claimed)
            await self.event_store.update_event_status(
                event.event_id, event.tenant_id, "processed"
            )
            return updated
        except (AgentLayerError, RuntimeError, TimeoutError, ValueError, TypeError, OSError) as exc:
            err_msg = f"{type(exc).__name__}: {exc}"[:500]
            claimed.worker_lease_until = None
            claimed.last_error = err_msg

            permanent = self.is_permanent_error(exc) or claimed.attempt >= claimed.max_attempts
            if permanent:
                claimed.status = "dead_letter"
                claimed.is_permanent_failure = self.is_permanent_error(exc)
                claimed.next_retry_at = None
                updated = await self.event_store.update_delivery(claimed)
                await self.event_store.update_event_status(
                    event.event_id, event.tenant_id, "dead_letter"
                )
                await self.event_store.append_audit(
                    EventAuditRecord(
                        tenant_id=event.tenant_id,
                        event_id=event.event_id,
                        action="event.dead_lettered",
                        actor_id="system:event_worker",
                        reason=err_msg,
                        details={
                            "delivery_id": claimed.delivery_id,
                            "attempt": claimed.attempt,
                            "permanent": claimed.is_permanent_failure,
                        },
                    )
                )
                return updated

            delay = self.compute_backoff(claimed.attempt)
            claimed.status = "retry_scheduled"
            claimed.next_retry_at = current + delay
            updated = await self.event_store.update_delivery(claimed)
            await self.event_store.append_audit(
                EventAuditRecord(
                    tenant_id=event.tenant_id,
                    event_id=event.event_id,
                    action="event.retry_scheduled",
                    actor_id="system:event_worker",
                    reason=err_msg,
                    details={
                        "delivery_id": claimed.delivery_id,
                        "attempt": claimed.attempt,
                        "next_retry_at": claimed.next_retry_at.isoformat(),
                    },
                )
            )
            return updated

    async def process_due_once(
        self,
        *,
        now: datetime | None = None,
        limit: int = 50,
    ) -> list[EventDeliveryRecord]:
        """Processes all due pending/retryable/expired-lease deliveries once."""
        due = await self.event_store.list_due_deliveries(now=now, limit=limit)
        results: list[EventDeliveryRecord] = []
        for d in due:
            res = await self.process_delivery(d.delivery_id, d.tenant_id, now=now)
            results.append(res)
        return results

    async def recover_pending_events(self, *, now: datetime | None = None) -> int:
        """Startup crash recovery sweeping any pending or stale-lease deliveries."""
        results = await self.process_due_once(now=now, limit=100)
        return len(results)

    async def replay_dead_letter(
        self,
        delivery_id: str,
        security_context: EventSecurityContext,
        *,
        process_immediately: bool = True,
    ) -> EventDeliveryRecord:
        """Resets a dead-lettered delivery safely and optionally re-processes it."""
        delivery = await self.event_store.get_delivery(delivery_id, security_context.tenant_id)
        if delivery is None:
            raise EventNotFoundError(delivery_id)

        delivery.status = "pending"
        delivery.attempt = 0
        delivery.is_permanent_failure = False
        delivery.next_retry_at = None
        delivery.worker_lease_until = None
        await self.event_store.update_delivery(delivery)
        await self.event_store.append_audit(
            EventAuditRecord(
                tenant_id=security_context.tenant_id,
                event_id=delivery.event_id,
                action="dlq.replayed",
                actor_id=security_context.user_id,
                reason="Operator replayed dead-letter delivery.",
                details={"delivery_id": delivery.delivery_id},
            )
        )
        if process_immediately:
            return await self.process_delivery(delivery.delivery_id, security_context.tenant_id)
        return delivery

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(), name="keep-event-queue-worker")

    async def stop(self) -> None:
        self._running = False
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    async def _loop(self) -> None:
        while self._running:
            try:
                await self.process_due_once(limit=25)
            except asyncio.CancelledError:
                break
            except (
                AgentLayerError,
                RuntimeError,
                TimeoutError,
                ValueError,
                OSError,
            ) as exc:  # pragma: no cover - background loop guard
                logger.warning("EventQueueWorker tick error: %s", exc)
            await asyncio.sleep(self.poll_interval_seconds)
