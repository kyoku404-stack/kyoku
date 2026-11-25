"""KEEP Phase 4.10 — Trigger Rules, Dispatches & Schedules Repository.

Implements atomic `claim_dispatch` backed by unique database constraints on
`dispatch_key` (`{event_id}:{trigger_id}:{trigger_version}`) so duplicate
event deliveries and worker restarts never launch duplicate workflows.

Owner: Member 2 (Trigger Registry, Rule Engine & Persistence)
Specification: devdocs/p4/p4.10.txt (Sections 7, 8, 9, 11)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime

from backend.app.agents.triggers.models import (
    DispatchStatus,
    TriggerDispatchRecord,
    TriggerRule,
    TriggerSchedule,
    build_dispatch_key,
)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


class BaseTriggerRepository(ABC):
    """Abstract tenant-scoped store for trigger rules, dispatches, and schedules."""

    @abstractmethod
    async def create_trigger(self, trigger: TriggerRule) -> TriggerRule: ...

    @abstractmethod
    async def get_trigger(self, trigger_id: str, tenant_id: str) -> TriggerRule | None: ...

    @abstractmethod
    async def update_trigger(self, trigger: TriggerRule) -> TriggerRule: ...

    @abstractmethod
    async def list_triggers(
        self,
        tenant_id: str,
        *,
        event_type: str | None = None,
        enabled_only: bool = False,
        limit: int = 100,
    ) -> list[TriggerRule]: ...

    @abstractmethod
    async def claim_dispatch(
        self,
        *,
        event_id: str,
        trigger: TriggerRule,
        resource_key: str | None = None,
    ) -> tuple[TriggerDispatchRecord, bool]:
        """Atomically claims `{event_id}:{trigger_id}:{version}`; returns `(record, claimed_bool)`."""

    @abstractmethod
    async def update_dispatch(self, dispatch: TriggerDispatchRecord) -> TriggerDispatchRecord: ...

    @abstractmethod
    async def list_dispatches_for_trigger(
        self, trigger_id: str, tenant_id: str, limit: int = 100
    ) -> list[TriggerDispatchRecord]: ...

    @abstractmethod
    async def list_dispatches_for_event(
        self, event_id: str, tenant_id: str
    ) -> list[TriggerDispatchRecord]: ...

    @abstractmethod
    async def count_active_dispatches(self, trigger_id: str, tenant_id: str) -> int: ...

    @abstractmethod
    async def get_latest_dispatch_for_resource(
        self, trigger_id: str, tenant_id: str, resource_key: str
    ) -> TriggerDispatchRecord | None: ...

    @abstractmethod
    async def create_schedule(self, schedule: TriggerSchedule) -> TriggerSchedule: ...

    @abstractmethod
    async def get_schedule(self, schedule_id: str, tenant_id: str) -> TriggerSchedule | None: ...

    @abstractmethod
    async def list_due_schedules(
        self, *, now: datetime | None = None, limit: int = 50
    ) -> list[TriggerSchedule]: ...

    @abstractmethod
    async def update_schedule(self, schedule: TriggerSchedule) -> TriggerSchedule: ...


class InMemoryTriggerRepository(BaseTriggerRepository):
    """In-memory tenant-isolated trigger & unique dispatch repository."""

    def __init__(self) -> None:
        self._triggers: dict[str, TriggerRule] = {}
        self._dispatches: dict[str, TriggerDispatchRecord] = {}
        self._dispatch_by_key: dict[str, str] = {}
        self._schedules: dict[str, TriggerSchedule] = {}

    async def create_trigger(self, trigger: TriggerRule) -> TriggerRule:
        copy = trigger.model_copy(deep=True)
        self._triggers[copy.trigger_id] = copy
        return copy.model_copy(deep=True)

    async def get_trigger(self, trigger_id: str, tenant_id: str) -> TriggerRule | None:
        t = self._triggers.get(trigger_id)
        if t is None or t.tenant_id != tenant_id:
            return None
        return t.model_copy(deep=True)

    async def update_trigger(self, trigger: TriggerRule) -> TriggerRule:
        existing = self._triggers.get(trigger.trigger_id)
        if existing is not None and existing.tenant_id == trigger.tenant_id:
            updated = trigger.model_copy(deep=True)
            updated.updated_at = datetime.now(UTC)
            self._triggers[trigger.trigger_id] = updated
            return updated.model_copy(deep=True)
        return trigger.model_copy(deep=True)

    async def list_triggers(
        self,
        tenant_id: str,
        *,
        event_type: str | None = None,
        enabled_only: bool = False,
        limit: int = 100,
    ) -> list[TriggerRule]:
        items = [
            t.model_copy(deep=True)
            for t in self._triggers.values()
            if t.tenant_id == tenant_id
            and (event_type is None or t.event_type == event_type)
            and (not enabled_only or t.enabled)
        ]
        items.sort(key=lambda t: t.created_at, reverse=True)
        return items[:limit]

    async def claim_dispatch(
        self,
        *,
        event_id: str,
        trigger: TriggerRule,
        resource_key: str | None = None,
    ) -> tuple[TriggerDispatchRecord, bool]:
        d_key = build_dispatch_key(event_id, trigger.trigger_id, trigger.version)
        existing_id = self._dispatch_by_key.get(d_key)
        if existing_id is not None:
            return self._dispatches[existing_id].model_copy(deep=True), False

        rec = TriggerDispatchRecord(
            dispatch_key=d_key,
            event_id=event_id,
            trigger_id=trigger.trigger_id,
            trigger_version=trigger.version,
            tenant_id=trigger.tenant_id,
            workflow_id=trigger.workflow_id,
            execution_mode=trigger.execution_mode,
            resource_key=resource_key,
            status="claimed",
        )
        self._dispatches[rec.dispatch_id] = rec
        self._dispatch_by_key[d_key] = rec.dispatch_id
        return rec.model_copy(deep=True), True

    async def update_dispatch(self, dispatch: TriggerDispatchRecord) -> TriggerDispatchRecord:
        existing = self._dispatches.get(dispatch.dispatch_id)
        if existing is not None and existing.tenant_id == dispatch.tenant_id:
            updated = dispatch.model_copy(deep=True)
            self._dispatches[dispatch.dispatch_id] = updated
            return updated.model_copy(deep=True)
        return dispatch.model_copy(deep=True)

    async def list_dispatches_for_trigger(
        self, trigger_id: str, tenant_id: str, limit: int = 100
    ) -> list[TriggerDispatchRecord]:
        items = [
            d.model_copy(deep=True)
            for d in self._dispatches.values()
            if d.trigger_id == trigger_id and d.tenant_id == tenant_id
        ]
        items.sort(key=lambda d: d.created_at, reverse=True)
        return items[:limit]

    async def list_dispatches_for_event(
        self, event_id: str, tenant_id: str
    ) -> list[TriggerDispatchRecord]:
        return [
            d.model_copy(deep=True)
            for d in self._dispatches.values()
            if d.event_id == event_id and d.tenant_id == tenant_id
        ]

    async def count_active_dispatches(self, trigger_id: str, tenant_id: str) -> int:
        active_states: tuple[DispatchStatus, ...] = ("claimed", "dispatched")
        return sum(
            1
            for d in self._dispatches.values()
            if d.trigger_id == trigger_id
            and d.tenant_id == tenant_id
            and d.status in active_states
        )

    async def get_latest_dispatch_for_resource(
        self, trigger_id: str, tenant_id: str, resource_key: str
    ) -> TriggerDispatchRecord | None:
        matches = [
            d
            for d in self._dispatches.values()
            if d.trigger_id == trigger_id
            and d.tenant_id == tenant_id
            and d.resource_key == resource_key
            and d.status in ("claimed", "dispatched", "completed")
        ]
        if not matches:
            return None
        matches.sort(key=lambda d: d.created_at, reverse=True)
        return matches[0].model_copy(deep=True)

    async def create_schedule(self, schedule: TriggerSchedule) -> TriggerSchedule:
        copy = schedule.model_copy(deep=True)
        self._schedules[copy.schedule_id] = copy
        return copy.model_copy(deep=True)

    async def get_schedule(self, schedule_id: str, tenant_id: str) -> TriggerSchedule | None:
        s = self._schedules.get(schedule_id)
        if s is None or s.tenant_id != tenant_id:
            return None
        return s.model_copy(deep=True)

    async def list_due_schedules(
        self, *, now: datetime | None = None, limit: int = 50
    ) -> list[TriggerSchedule]:
        current = now or datetime.now(UTC)
        due = [
            s.model_copy(deep=True)
            for s in self._schedules.values()
            if s.enabled and (_ensure_utc(s.next_run_at) or current) <= current
        ]
        due.sort(key=lambda s: s.next_run_at)
        return due[:limit]

    async def update_schedule(self, schedule: TriggerSchedule) -> TriggerSchedule:
        existing = self._schedules.get(schedule.schedule_id)
        if existing is not None and existing.tenant_id == schedule.tenant_id:
            updated = schedule.model_copy(deep=True)
            self._schedules[schedule.schedule_id] = updated
            return updated.model_copy(deep=True)
        return schedule.model_copy(deep=True)


class SqlAlchemyTriggerRepository(BaseTriggerRepository):
    """Persistent PostgreSQL/SQLite repository backing trigger rules, unique claims & schedules."""

    def __init__(self, session_factory: object | None = None) -> None:
        self._session_factory = session_factory
        self._fallback = InMemoryTriggerRepository()

    @staticmethod
    def _to_trigger(row: object) -> TriggerRule:
        return TriggerRule(
            trigger_id=row.trigger_id,  # type: ignore[attr-defined]
            tenant_id=row.tenant_id,  # type: ignore[attr-defined]
            owner_id=row.owner_id,  # type: ignore[attr-defined]
            name=row.name,  # type: ignore[attr-defined]
            event_type=row.event_type,  # type: ignore[attr-defined]
            workflow_id=row.workflow_id,  # type: ignore[attr-defined]
            execution_mode=row.execution_mode,  # type: ignore[attr-defined]
            version=row.version,  # type: ignore[attr-defined]
            enabled=bool(row.enabled),  # type: ignore[attr-defined]
            allowed_sources=list(row.allowed_sources or []),  # type: ignore[attr-defined]
            conditions=dict(row.conditions or {}),  # type: ignore[attr-defined]
            cooldown_seconds=row.cooldown_seconds,  # type: ignore[attr-defined]
            max_concurrent_runs=row.max_concurrent_runs,  # type: ignore[attr-defined]
            last_triggered_at=_ensure_utc(row.last_triggered_at),  # type: ignore[attr-defined]
            created_at=_ensure_utc(row.created_at) or datetime.now(UTC),  # type: ignore[attr-defined]
            updated_at=_ensure_utc(row.updated_at) or datetime.now(UTC),  # type: ignore[attr-defined]
        )

    @staticmethod
    def _to_dispatch(row: object) -> TriggerDispatchRecord:
        return TriggerDispatchRecord(
            dispatch_id=row.dispatch_id,  # type: ignore[attr-defined]
            dispatch_key=row.dispatch_key,  # type: ignore[attr-defined]
            event_id=row.event_id,  # type: ignore[attr-defined]
            trigger_id=row.trigger_id,  # type: ignore[attr-defined]
            trigger_version=row.trigger_version,  # type: ignore[attr-defined]
            tenant_id=row.tenant_id,  # type: ignore[attr-defined]
            workflow_id=row.workflow_id,  # type: ignore[attr-defined]
            execution_mode=row.execution_mode,  # type: ignore[attr-defined]
            workflow_execution_id=row.workflow_execution_id,  # type: ignore[attr-defined]
            resource_key=row.resource_key,  # type: ignore[attr-defined]
            status=row.status,  # type: ignore[attr-defined]
            reason=row.reason,  # type: ignore[attr-defined]
            created_at=_ensure_utc(row.created_at) or datetime.now(UTC),  # type: ignore[attr-defined]
        )

    @staticmethod
    def _to_schedule(row: object) -> TriggerSchedule:
        return TriggerSchedule(
            schedule_id=row.schedule_id,  # type: ignore[attr-defined]
            trigger_id=row.trigger_id,  # type: ignore[attr-defined]
            tenant_id=row.tenant_id,  # type: ignore[attr-defined]
            cron_expression=row.cron_expression,  # type: ignore[attr-defined]
            interval_seconds=row.interval_seconds,  # type: ignore[attr-defined]
            timezone=row.timezone,  # type: ignore[attr-defined]
            missed_run_policy=row.missed_run_policy,  # type: ignore[attr-defined]
            enabled=bool(row.enabled),  # type: ignore[attr-defined]
            next_run_at=_ensure_utc(row.next_run_at) or datetime.now(UTC),  # type: ignore[attr-defined]
            last_run_at=_ensure_utc(row.last_run_at),  # type: ignore[attr-defined]
        )

    async def create_trigger(self, trigger: TriggerRule) -> TriggerRule:
        if self._session_factory is None:
            return await self._fallback.create_trigger(trigger)

        from backend.app.models.agent_triggers import TriggerRuleModel

        async with self._session_factory() as db:  # type: ignore[operator]
            db.add(
                TriggerRuleModel(
                    trigger_id=trigger.trigger_id,
                    tenant_id=trigger.tenant_id,
                    owner_id=trigger.owner_id,
                    name=trigger.name,
                    event_type=trigger.event_type,
                    workflow_id=trigger.workflow_id,
                    execution_mode=trigger.execution_mode,
                    version=trigger.version,
                    enabled=trigger.enabled,
                    allowed_sources=list(trigger.allowed_sources),
                    conditions=dict(trigger.conditions),
                    cooldown_seconds=trigger.cooldown_seconds,
                    max_concurrent_runs=trigger.max_concurrent_runs,
                    last_triggered_at=trigger.last_triggered_at,
                    created_at=trigger.created_at,
                    updated_at=trigger.updated_at,
                )
            )
            await db.commit()
        return trigger.model_copy(deep=True)

    async def get_trigger(self, trigger_id: str, tenant_id: str) -> TriggerRule | None:
        if self._session_factory is None:
            return await self._fallback.get_trigger(trigger_id, tenant_id)

        from backend.app.models.agent_triggers import TriggerRuleModel
        from sqlalchemy import select

        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = select(TriggerRuleModel).where(
                TriggerRuleModel.trigger_id == trigger_id,
                TriggerRuleModel.tenant_id == tenant_id,
            )
            row = (await db.execute(stmt)).scalar_one_or_none()
            return self._to_trigger(row) if row is not None else None

    async def update_trigger(self, trigger: TriggerRule) -> TriggerRule:
        if self._session_factory is None:
            return await self._fallback.update_trigger(trigger)

        from backend.app.models.agent_triggers import TriggerRuleModel
        from sqlalchemy import select

        now = datetime.now(UTC)
        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = select(TriggerRuleModel).where(
                TriggerRuleModel.trigger_id == trigger.trigger_id,
                TriggerRuleModel.tenant_id == trigger.tenant_id,
            )
            row = (await db.execute(stmt)).scalar_one_or_none()
            if row is not None:
                row.name = trigger.name
                row.workflow_id = trigger.workflow_id
                row.execution_mode = trigger.execution_mode
                row.version = trigger.version
                row.enabled = trigger.enabled
                row.allowed_sources = list(trigger.allowed_sources)
                row.conditions = dict(trigger.conditions)
                row.cooldown_seconds = trigger.cooldown_seconds
                row.max_concurrent_runs = trigger.max_concurrent_runs
                row.last_triggered_at = trigger.last_triggered_at
                row.updated_at = now
                await db.commit()
        res = trigger.model_copy(deep=True)
        res.updated_at = now
        return res

    async def list_triggers(
        self,
        tenant_id: str,
        *,
        event_type: str | None = None,
        enabled_only: bool = False,
        limit: int = 100,
    ) -> list[TriggerRule]:
        if self._session_factory is None:
            return await self._fallback.list_triggers(
                tenant_id, event_type=event_type, enabled_only=enabled_only, limit=limit
            )

        from backend.app.models.agent_triggers import TriggerRuleModel
        from sqlalchemy import select

        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = (
                select(TriggerRuleModel)
                .where(TriggerRuleModel.tenant_id == tenant_id)
                .order_by(TriggerRuleModel.created_at.desc())
                .limit(limit)
            )
            if event_type is not None:
                stmt = stmt.where(TriggerRuleModel.event_type == event_type)
            if enabled_only:
                stmt = stmt.where(TriggerRuleModel.enabled.is_(True))
            rows = (await db.execute(stmt)).scalars().all()
            return [self._to_trigger(r) for r in rows]

    async def claim_dispatch(
        self,
        *,
        event_id: str,
        trigger: TriggerRule,
        resource_key: str | None = None,
    ) -> tuple[TriggerDispatchRecord, bool]:
        if self._session_factory is None:
            return await self._fallback.claim_dispatch(
                event_id=event_id, trigger=trigger, resource_key=resource_key
            )

        from backend.app.models.agent_triggers import TriggerDispatchModel
        from sqlalchemy import select
        from sqlalchemy.exc import IntegrityError

        d_key = build_dispatch_key(event_id, trigger.trigger_id, trigger.version)
        rec = TriggerDispatchRecord(
            dispatch_key=d_key,
            event_id=event_id,
            trigger_id=trigger.trigger_id,
            trigger_version=trigger.version,
            tenant_id=trigger.tenant_id,
            workflow_id=trigger.workflow_id,
            execution_mode=trigger.execution_mode,
            resource_key=resource_key,
            status="claimed",
        )
        try:
            async with self._session_factory() as db:  # type: ignore[operator]
                db.add(
                    TriggerDispatchModel(
                        dispatch_id=rec.dispatch_id,
                        dispatch_key=rec.dispatch_key,
                        event_id=rec.event_id,
                        trigger_id=rec.trigger_id,
                        trigger_version=rec.trigger_version,
                        tenant_id=rec.tenant_id,
                        workflow_id=rec.workflow_id,
                        execution_mode=rec.execution_mode,
                        workflow_execution_id=rec.workflow_execution_id,
                        resource_key=rec.resource_key,
                        status=rec.status,
                        reason=rec.reason,
                        created_at=rec.created_at,
                    )
                )
                await db.commit()
            return rec, True
        except IntegrityError:
            async with self._session_factory() as db:  # type: ignore[operator]
                stmt = select(TriggerDispatchModel).where(
                    TriggerDispatchModel.dispatch_key == d_key,
                    TriggerDispatchModel.tenant_id == trigger.tenant_id,
                )
                existing = (await db.execute(stmt)).scalar_one()
                return self._to_dispatch(existing), False

    async def update_dispatch(self, dispatch: TriggerDispatchRecord) -> TriggerDispatchRecord:
        if self._session_factory is None:
            return await self._fallback.update_dispatch(dispatch)

        from backend.app.models.agent_triggers import TriggerDispatchModel
        from sqlalchemy import select

        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = select(TriggerDispatchModel).where(
                TriggerDispatchModel.dispatch_id == dispatch.dispatch_id,
                TriggerDispatchModel.tenant_id == dispatch.tenant_id,
            )
            row = (await db.execute(stmt)).scalar_one_or_none()
            if row is not None:
                row.workflow_execution_id = dispatch.workflow_execution_id
                row.status = dispatch.status
                row.reason = dispatch.reason
                await db.commit()
        return dispatch.model_copy(deep=True)

    async def list_dispatches_for_trigger(
        self, trigger_id: str, tenant_id: str, limit: int = 100
    ) -> list[TriggerDispatchRecord]:
        if self._session_factory is None:
            return await self._fallback.list_dispatches_for_trigger(
                trigger_id, tenant_id, limit=limit
            )

        from backend.app.models.agent_triggers import TriggerDispatchModel
        from sqlalchemy import select

        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = (
                select(TriggerDispatchModel)
                .where(
                    TriggerDispatchModel.trigger_id == trigger_id,
                    TriggerDispatchModel.tenant_id == tenant_id,
                )
                .order_by(TriggerDispatchModel.created_at.desc())
                .limit(limit)
            )
            rows = (await db.execute(stmt)).scalars().all()
            return [self._to_dispatch(r) for r in rows]

    async def list_dispatches_for_event(
        self, event_id: str, tenant_id: str
    ) -> list[TriggerDispatchRecord]:
        if self._session_factory is None:
            return await self._fallback.list_dispatches_for_event(event_id, tenant_id)

        from backend.app.models.agent_triggers import TriggerDispatchModel
        from sqlalchemy import select

        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = select(TriggerDispatchModel).where(
                TriggerDispatchModel.event_id == event_id,
                TriggerDispatchModel.tenant_id == tenant_id,
            )
            rows = (await db.execute(stmt)).scalars().all()
            return [self._to_dispatch(r) for r in rows]

    async def count_active_dispatches(self, trigger_id: str, tenant_id: str) -> int:
        if self._session_factory is None:
            return await self._fallback.count_active_dispatches(trigger_id, tenant_id)

        from backend.app.models.agent_triggers import TriggerDispatchModel
        from sqlalchemy import func, select

        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = select(func.count()).select_from(TriggerDispatchModel).where(
                TriggerDispatchModel.trigger_id == trigger_id,
                TriggerDispatchModel.tenant_id == tenant_id,
                TriggerDispatchModel.status.in_(["claimed", "dispatched"]),
            )
            return int((await db.execute(stmt)).scalar_one() or 0)

    async def get_latest_dispatch_for_resource(
        self, trigger_id: str, tenant_id: str, resource_key: str
    ) -> TriggerDispatchRecord | None:
        if self._session_factory is None:
            return await self._fallback.get_latest_dispatch_for_resource(
                trigger_id, tenant_id, resource_key
            )

        from backend.app.models.agent_triggers import TriggerDispatchModel
        from sqlalchemy import select

        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = (
                select(TriggerDispatchModel)
                .where(
                    TriggerDispatchModel.trigger_id == trigger_id,
                    TriggerDispatchModel.tenant_id == tenant_id,
                    TriggerDispatchModel.resource_key == resource_key,
                    TriggerDispatchModel.status.in_(["claimed", "dispatched", "completed"]),
                )
                .order_by(TriggerDispatchModel.created_at.desc())
                .limit(1)
            )
            row = (await db.execute(stmt)).scalar_one_or_none()
            return self._to_dispatch(row) if row is not None else None

    async def create_schedule(self, schedule: TriggerSchedule) -> TriggerSchedule:
        if self._session_factory is None:
            return await self._fallback.create_schedule(schedule)

        from backend.app.models.agent_triggers import TriggerScheduleModel

        async with self._session_factory() as db:  # type: ignore[operator]
            db.add(
                TriggerScheduleModel(
                    schedule_id=schedule.schedule_id,
                    trigger_id=schedule.trigger_id,
                    tenant_id=schedule.tenant_id,
                    cron_expression=schedule.cron_expression,
                    interval_seconds=schedule.interval_seconds,
                    timezone=schedule.timezone,
                    missed_run_policy=schedule.missed_run_policy,
                    enabled=schedule.enabled,
                    next_run_at=schedule.next_run_at,
                    last_run_at=schedule.last_run_at,
                )
            )
            await db.commit()
        return schedule.model_copy(deep=True)

    async def get_schedule(self, schedule_id: str, tenant_id: str) -> TriggerSchedule | None:
        if self._session_factory is None:
            return await self._fallback.get_schedule(schedule_id, tenant_id)

        from backend.app.models.agent_triggers import TriggerScheduleModel
        from sqlalchemy import select

        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = select(TriggerScheduleModel).where(
                TriggerScheduleModel.schedule_id == schedule_id,
                TriggerScheduleModel.tenant_id == tenant_id,
            )
            row = (await db.execute(stmt)).scalar_one_or_none()
            return self._to_schedule(row) if row is not None else None

    async def list_due_schedules(
        self, *, now: datetime | None = None, limit: int = 50
    ) -> list[TriggerSchedule]:
        if self._session_factory is None:
            return await self._fallback.list_due_schedules(now=now, limit=limit)

        from backend.app.models.agent_triggers import TriggerScheduleModel
        from sqlalchemy import select

        current = now or datetime.now(UTC)
        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = (
                select(TriggerScheduleModel)
                .where(
                    TriggerScheduleModel.enabled.is_(True),
                    TriggerScheduleModel.next_run_at <= current,
                )
                .order_by(TriggerScheduleModel.next_run_at.asc())
                .limit(limit)
            )
            rows = (await db.execute(stmt)).scalars().all()
            return [self._to_schedule(r) for r in rows]

    async def update_schedule(self, schedule: TriggerSchedule) -> TriggerSchedule:
        if self._session_factory is None:
            return await self._fallback.update_schedule(schedule)

        from backend.app.models.agent_triggers import TriggerScheduleModel
        from sqlalchemy import select

        async with self._session_factory() as db:  # type: ignore[operator]
            stmt = select(TriggerScheduleModel).where(
                TriggerScheduleModel.schedule_id == schedule.schedule_id,
                TriggerScheduleModel.tenant_id == schedule.tenant_id,
            )
            row = (await db.execute(stmt)).scalar_one_or_none()
            if row is not None:
                row.enabled = schedule.enabled
                row.next_run_at = schedule.next_run_at
                row.last_run_at = schedule.last_run_at
                await db.commit()
        return schedule.model_copy(deep=True)
