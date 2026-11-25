"""KEEP Phase 4.10 — Unified Trigger & Event Automation Facade Service.

Coordinates TriggerRegistry CRUD, EventIngestionService, EventQueueWorker,
TriggerScheduler, TriggerDispatcher, Dead-Letter Inspection/Replay, and Audits.

Owner: Member 4 (Workflow Dispatch, API & Integration)
Specification: devdocs/p4/p4.10.txt (Sections 3, 10)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.app.agents.errors import EventNotFoundError
from backend.app.agents.events.contracts import (
    EventDeliveryRecord,
    EventInspectionResponse,
    EventPublishRequest,
    EventSecurityContext,
    KeepEvent,
)
from backend.app.agents.events.event_store import BaseEventStore, InMemoryEventStore
from backend.app.agents.events.ingestion import EventIngestionService
from backend.app.agents.events.validation import EventSchemaRegistry
from backend.app.agents.triggers.dispatcher import TriggerDispatcher
from backend.app.agents.triggers.models import (
    ScheduleCreateRequest,
    TriggerCreateRequest,
    TriggerDispatchRecord,
    TriggerRule,
    TriggerSchedule,
    TriggerUpdateRequest,
)
from backend.app.agents.triggers.policies import TriggerPolicyEngine
from backend.app.agents.triggers.registry import TriggerRegistry
from backend.app.agents.triggers.repository import (
    BaseTriggerRepository,
    InMemoryTriggerRepository,
)
from backend.app.agents.triggers.scheduler import TriggerScheduler
from backend.app.agents.workers.event_worker import EventQueueWorker


class TriggerService:
    """Master Phase 4.10 service powering /api/v1/triggers and /api/v1/events endpoints."""

    def __init__(
        self,
        *,
        event_store: BaseEventStore | None = None,
        trigger_repository: BaseTriggerRepository | None = None,
        workflow_registry: Any | None = None,
        orchestration_service: Any | None = None,
        autonomy_service: Any | None = None,
        schema_registry: EventSchemaRegistry | None = None,
    ) -> None:
        self.event_store = event_store or InMemoryEventStore()
        self.trigger_repository = trigger_repository or InMemoryTriggerRepository()
        self.schema_registry = schema_registry or EventSchemaRegistry()
        self.policy_engine = TriggerPolicyEngine(self.trigger_repository, self.event_store)
        self.registry = TriggerRegistry(
            self.trigger_repository,
            workflow_registry=workflow_registry,
            schema_registry=self.schema_registry,
        )
        self.dispatcher = TriggerDispatcher(
            self.trigger_repository,
            event_store=self.event_store,
            workflow_registry=workflow_registry,
            policy_engine=self.policy_engine,
            orchestration_service=orchestration_service,
            autonomy_service=autonomy_service,
        )
        self.worker = EventQueueWorker(
            self.event_store,
            handler=self._handle_delivery,
        )
        self.ingestion_service = EventIngestionService(
            self.event_store,
            schema_registry=self.schema_registry,
            on_delivery_enqueued=None,
        )
        self.scheduler = TriggerScheduler(self.trigger_repository, self.ingestion_service)

    async def _handle_delivery(
        self, event: KeepEvent, delivery: EventDeliveryRecord
    ) -> None:
        await self.dispatcher.process_event_matches(event)

    # ------------------------------------------------------------------
    # Trigger CRUD & Schedules
    # ------------------------------------------------------------------

    async def create_trigger(
        self,
        request: TriggerCreateRequest,
        security_context: EventSecurityContext,
    ) -> TriggerRule:
        self.policy_engine.authorize_manage(security_context)
        return await self.registry.create_trigger(request, security_context)

    async def list_triggers(
        self,
        security_context: EventSecurityContext,
        *,
        event_type: str | None = None,
        enabled_only: bool = False,
        limit: int = 100,
    ) -> list[TriggerRule]:
        self.policy_engine.authorize_read(security_context.tenant_id, security_context)
        return await self.registry.list_triggers(
            security_context,
            event_type=event_type,
            enabled_only=enabled_only,
            limit=limit,
        )

    async def get_trigger(
        self,
        trigger_id: str,
        security_context: EventSecurityContext,
    ) -> TriggerRule:
        self.policy_engine.authorize_read(security_context.tenant_id, security_context)
        return await self.registry.get_trigger(trigger_id, security_context)

    async def update_trigger(
        self,
        trigger_id: str,
        request: TriggerUpdateRequest,
        security_context: EventSecurityContext,
    ) -> TriggerRule:
        self.policy_engine.authorize_manage(security_context)
        return await self.registry.update_trigger(trigger_id, request, security_context)

    async def set_trigger_enabled(
        self,
        trigger_id: str,
        *,
        enabled: bool,
        security_context: EventSecurityContext,
    ) -> TriggerRule:
        self.policy_engine.authorize_manage(security_context)
        return await self.registry.set_enabled(
            trigger_id, enabled=enabled, security_context=security_context
        )

    async def list_trigger_runs(
        self,
        trigger_id: str,
        security_context: EventSecurityContext,
        *,
        limit: int = 100,
    ) -> list[TriggerDispatchRecord]:
        await self.get_trigger(trigger_id, security_context)
        return await self.trigger_repository.list_dispatches_for_trigger(
            trigger_id, security_context.tenant_id, limit=limit
        )

    async def create_schedule(
        self,
        trigger_id: str,
        request: ScheduleCreateRequest,
        security_context: EventSecurityContext,
    ) -> TriggerSchedule:
        self.policy_engine.authorize_manage(security_context)
        return await self.scheduler.create_schedule(trigger_id, request, security_context)

    # ------------------------------------------------------------------
    # Event Publishing, Processing & Inspection
    # ------------------------------------------------------------------

    async def publish_and_process(
        self,
        request: EventPublishRequest,
        security_context: EventSecurityContext,
        *,
        process_immediately: bool = True,
    ) -> tuple[KeepEvent, EventDeliveryRecord, list[TriggerDispatchRecord], bool]:
        self.policy_engine.authorize_manage(security_context)
        event, delivery, deduplicated = await self.ingestion_service.ingest(
            request, security_context
        )
        if process_immediately and not request.use_outbox and not deduplicated:
            await self.worker.process_delivery(delivery.delivery_id, security_context.tenant_id)
        updated_event = await self.event_store.get_event(
            event.event_id, security_context.tenant_id
        )
        updated_deliv = await self.event_store.get_delivery(
            delivery.delivery_id, security_context.tenant_id
        )
        dispatches = await self.trigger_repository.list_dispatches_for_event(
            event.event_id, security_context.tenant_id
        )
        return (
            updated_event or event,
            updated_deliv or delivery,
            dispatches,
            deduplicated,
        )

    async def inspect_event(
        self,
        event_id: str,
        security_context: EventSecurityContext,
    ) -> EventInspectionResponse:
        self.policy_engine.authorize_read(security_context.tenant_id, security_context)
        event = await self.event_store.get_event(event_id, security_context.tenant_id)
        if event is None:
            raise EventNotFoundError(event_id)
        deliveries = await self.event_store.list_deliveries_for_event(
            event_id, security_context.tenant_id
        )
        dispatches = await self.trigger_repository.list_dispatches_for_event(
            event_id, security_context.tenant_id
        )
        return EventInspectionResponse(
            event=event,
            deliveries=deliveries,
            dispatches=[d.model_dump(mode="json") for d in dispatches],
        )

    async def list_dead_letters(
        self,
        security_context: EventSecurityContext,
        *,
        limit: int = 50,
    ) -> list[EventDeliveryRecord]:
        self.policy_engine.authorize_read(security_context.tenant_id, security_context)
        return await self.event_store.list_dead_letter_deliveries(
            security_context.tenant_id, limit=limit
        )

    async def replay_dead_letter(
        self,
        delivery_id: str,
        security_context: EventSecurityContext,
    ) -> EventDeliveryRecord:
        self.policy_engine.authorize_manage(security_context)
        return await self.worker.replay_dead_letter(
            delivery_id, security_context, process_immediately=True
        )

    async def tick_schedules(self, *, now: datetime | None = None) -> list[KeepEvent]:
        events = await self.scheduler.tick(now=now)
        for ev in events:
            delivs = await self.event_store.list_deliveries_for_event(ev.event_id, ev.tenant_id)
            for d in delivs:
                await self.worker.process_delivery(d.delivery_id, ev.tenant_id, now=now)
        return events
