"""KEEP Phase 4.10 — Persistent Trigger Scheduler.

Schedules time-based triggers (cron OR interval) across timezones with DST
safety, missed-run policies (`skip`, `coalesce`, `replay_latest`), and unique
scheduled-run deduplication keys routed cleanly through EventIngestionService.

Owner: Member 3 (Queue, Scheduling & Reliability)
Specification: devdocs/p4/p4.10.txt (Section 9)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from backend.app.agents.errors import EventValidationError, TriggerNotFoundError
from backend.app.agents.events.contracts import (
    EventPublishRequest,
    EventSecurityContext,
    KeepEvent,
)
from backend.app.agents.events.ingestion import EventIngestionService
from backend.app.agents.triggers.models import (
    ScheduleCreateRequest,
    TriggerSchedule,
    generate_schedule_id,
)
from backend.app.agents.triggers.repository import BaseTriggerRepository


def _parse_cron_field(expr: str, min_val: int, max_val: int) -> set[int]:
    """Parses a single 5-field cron component supporting `*`, `*/N`, ranges, and lists."""
    allowed: set[int] = set()
    for part in expr.split(","):
        part = part.strip()
        if part == "*":
            allowed.update(range(min_val, max_val + 1))
        elif part.startswith("*/"):
            step = int(part[2:])
            if step <= 0:
                raise ValueError("Cron step must be > 0")
            allowed.update(range(min_val, max_val + 1, step))
        elif "-" in part:
            start_s, end_s = part.split("-", 1)
            allowed.update(range(int(start_s), int(end_s) + 1))
        else:
            allowed.add(int(part))
    return {v for v in allowed if min_val <= v <= max_val}


def _resolve_timezone(timezone_name: str) -> tzinfo:
    upper = timezone_name.strip().upper()
    if upper in ("UTC", "Z", "GMT"):
        return UTC
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        from datetime import timezone

        windows_fallback = {
            "AMERICA/NEW_YORK": timezone(timedelta(hours=-5)),
            "AMERICA/LOS_ANGELES": timezone(timedelta(hours=-8)),
            "EUROPE/LONDON": UTC,
            "ASIA/KOLKATA": timezone(timedelta(hours=5, minutes=30)),
            "ASIA/TOKYO": timezone(timedelta(hours=9)),
        }
        if upper in windows_fallback:
            return windows_fallback[upper]
        raise EventValidationError(f"Unsupported timezone '{timezone_name}'.") from exc


def compute_next_run(
    *,
    cron_expression: str | None,
    interval_seconds: int | None,
    timezone_name: str,
    after: datetime,
) -> datetime:
    """Computes next UTC execution timestamp honoring DST/IANA timezone boundaries."""
    tz = _resolve_timezone(timezone_name)

    base_utc = after if after.tzinfo is not None else after.replace(tzinfo=UTC)
    if interval_seconds is not None:
        return base_utc + timedelta(seconds=interval_seconds)

    assert cron_expression is not None
    fields = cron_expression.strip().split()
    if len(fields) != 5:
        raise EventValidationError(
            f"Invalid 5-field cron_expression '{cron_expression}'."
        )

    try:
        minutes = _parse_cron_field(fields[0], 0, 59)
        hours = _parse_cron_field(fields[1], 0, 23)
        days = _parse_cron_field(fields[2], 1, 31)
        months = _parse_cron_field(fields[3], 1, 12)
        weekdays = _parse_cron_field(fields[4], 0, 6)
    except ValueError as exc:
        raise EventValidationError(f"Invalid cron expression: {exc}") from exc

    if not (minutes and hours and days and months and weekdays):
        raise EventValidationError("Cron expression matches no valid calendar instants.")

    cursor = base_utc.astimezone(tz).replace(second=0, microsecond=0) + timedelta(minutes=1)
    # Bounded search up to 31 days ahead
    for _ in range(31 * 24 * 60):
        cron_dow = (cursor.weekday() + 1) % 7  # Sunday=0 in standard cron
        if (
            cursor.minute in minutes
            and cursor.hour in hours
            and cursor.day in days
            and cursor.month in months
            and cron_dow in weekdays
        ):
            return cursor.astimezone(UTC)
        cursor += timedelta(minutes=1)
    return base_utc + timedelta(days=1)


class TriggerScheduler:
    """Manages time-based schedules and emits deduplicated `schedule.triggered` events."""

    def __init__(
        self,
        trigger_repository: BaseTriggerRepository,
        ingestion_service: EventIngestionService,
    ) -> None:
        self.trigger_repository = trigger_repository
        self.ingestion_service = ingestion_service

    async def create_schedule(
        self,
        trigger_id: str,
        request: ScheduleCreateRequest,
        security_context: EventSecurityContext,
        *,
        now: datetime | None = None,
    ) -> TriggerSchedule:
        trigger = await self.trigger_repository.get_trigger(
            trigger_id, security_context.tenant_id
        )
        if trigger is None:
            raise TriggerNotFoundError(trigger_id)

        current = now or datetime.now(UTC)
        next_run = compute_next_run(
            cron_expression=request.cron_expression,
            interval_seconds=request.interval_seconds,
            timezone_name=request.timezone,
            after=current,
        )
        schedule = TriggerSchedule(
            schedule_id=generate_schedule_id(),
            trigger_id=trigger.trigger_id,
            tenant_id=security_context.tenant_id,
            cron_expression=request.cron_expression,
            interval_seconds=request.interval_seconds,
            timezone=request.timezone,
            missed_run_policy=request.missed_run_policy,
            enabled=request.enabled,
            next_run_at=next_run,
            last_run_at=None,
        )
        return await self.trigger_repository.create_schedule(schedule)

    async def tick(self, *, now: datetime | None = None, limit: int = 50) -> list[KeepEvent]:
        """Evaluates due schedules, handles missed runs cleanly, and publishes trigger events."""
        current = now or datetime.now(UTC)
        due = await self.trigger_repository.list_due_schedules(now=current, limit=limit)
        emitted: list[KeepEvent] = []

        for sch in due:
            scheduled_at = (
                sch.next_run_at
                if sch.next_run_at.tzinfo is not None
                else sch.next_run_at.replace(tzinfo=UTC)
            )
            # Determine if run was missed by more than one full interval or > 60s
            gap_seconds = (current - scheduled_at).total_seconds()
            is_missed = gap_seconds > max(60, sch.interval_seconds or 60)

            next_run = compute_next_run(
                cron_expression=sch.cron_expression,
                interval_seconds=sch.interval_seconds,
                timezone_name=sch.timezone,
                after=current,
            )

            if is_missed and sch.missed_run_policy == "skip":
                sch.next_run_at = next_run
                await self.trigger_repository.update_schedule(sch)
                continue

            # Advance schedule metadata before ingestion; unique scheduled run key prevents duplicates
            run_epoch = int(scheduled_at.timestamp())
            event_id = f"sched_{sch.schedule_id}_{run_epoch}"
            sch.last_run_at = current
            sch.next_run_at = next_run
            await self.trigger_repository.update_schedule(sch)

            ctx = EventSecurityContext(
                tenant_id=sch.tenant_id,
                user_id=f"scheduler:{sch.schedule_id}",
                roles=["service"],
                permissions=["agent.invoke", "agent.read"],
                trusted_source="keep.scheduler",
            )
            req = EventPublishRequest(
                event_id=event_id,
                event_type="schedule.triggered",
                source="keep.scheduler",
                occurred_at=scheduled_at,
                resource_id=sch.trigger_id,
                payload={
                    "schedule_id": sch.schedule_id,
                    "trigger_id": sch.trigger_id,
                    "scheduled_for": scheduled_at.isoformat(),
                    "missed_coalesced": is_missed,
                },
            )
            ev, _, deduplicated = await self.ingestion_service.ingest(req, ctx)
            if not deduplicated:
                emitted.append(ev)

        return emitted
