"""KEEP Phase 4.10 — Trigger Rule, Schedule & Dispatch Models.

Defines declarative TriggerRule contracts, schedules (cron XOR interval),
unique dispatch records, and CRUD request/response models.

Owner: Member 2 (Trigger Registry & Rule Engine)
Specification: devdocs/p4/p4.10.txt (Sections 6, 8, 9, 11)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

TriggerExecutionMode = Literal["workflow", "autonomous_workflow"]
DispatchStatus = Literal["claimed", "dispatched", "completed", "failed", "suppressed"]
MissedRunPolicy = Literal["skip", "coalesce", "replay_latest"]


def generate_trigger_id() -> str:
    return f"trg_{uuid4().hex[:16]}"


def generate_dispatch_id() -> str:
    return f"dsp_{uuid4().hex[:16]}"


def generate_schedule_id() -> str:
    return f"sch_{uuid4().hex[:16]}"


def build_dispatch_key(event_id: str, trigger_id: str, trigger_version: int) -> str:
    """Deterministic idempotency claim key across duplicate deliveries."""
    return f"{event_id}:{trigger_id}:{trigger_version}"


class TriggerRule(BaseModel):
    """Declarative rule binding a registered event type to an approved KEEP workflow."""

    trigger_id: str = Field(default_factory=generate_trigger_id, min_length=2, max_length=128)
    tenant_id: str = Field(..., min_length=1, max_length=128)
    owner_id: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=256)
    event_type: str = Field(..., min_length=3, max_length=128)
    workflow_id: str = Field(..., min_length=2, max_length=128)
    execution_mode: TriggerExecutionMode = "workflow"
    version: int = Field(default=1, ge=1)
    enabled: bool = True
    allowed_sources: list[str] = Field(default_factory=list)
    conditions: dict[str, Any] = Field(default_factory=dict)
    cooldown_seconds: int = Field(default=0, ge=0, le=86400)
    max_concurrent_runs: int = Field(default=1, ge=1, le=20)
    last_triggered_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TriggerCreateRequest(BaseModel):
    """Payload to register a new tenant-scoped trigger rule."""

    trigger_id: str | None = Field(default=None, max_length=128)
    name: str = Field(..., min_length=1, max_length=256)
    event_type: str = Field(..., min_length=3, max_length=128)
    workflow_id: str = Field(..., min_length=2, max_length=128)
    execution_mode: TriggerExecutionMode = "workflow"
    enabled: bool = True
    allowed_sources: list[str] = Field(default_factory=list)
    conditions: dict[str, Any] = Field(default_factory=dict)
    cooldown_seconds: int = Field(default=0, ge=0, le=86400)
    max_concurrent_runs: int = Field(default=1, ge=1, le=20)


class TriggerUpdateRequest(BaseModel):
    """Mutable configuration updates advancing trigger version cleanly."""

    name: str | None = Field(default=None, min_length=1, max_length=256)
    workflow_id: str | None = Field(default=None, min_length=2, max_length=128)
    execution_mode: TriggerExecutionMode | None = None
    allowed_sources: list[str] | None = None
    conditions: dict[str, Any] | None = None
    cooldown_seconds: int | None = Field(default=None, ge=0, le=86400)
    max_concurrent_runs: int | None = Field(default=None, ge=1, le=20)


class TriggerSchedule(BaseModel):
    """Persistent cron/interval schedule attached to an approved TriggerRule."""

    schedule_id: str = Field(default_factory=generate_schedule_id, min_length=2, max_length=128)
    trigger_id: str
    tenant_id: str
    cron_expression: str | None = Field(default=None, max_length=64)
    interval_seconds: int | None = Field(default=None, gt=0, le=2_592_000)
    timezone: str = Field(default="UTC", max_length=64)
    missed_run_policy: MissedRunPolicy = "coalesce"
    enabled: bool = True
    next_run_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_run_at: datetime | None = None

    @model_validator(mode="after")
    def validate_exclusive_schedule_mode(self) -> TriggerSchedule:
        has_cron = bool(self.cron_expression and self.cron_expression.strip())
        has_interval = self.interval_seconds is not None
        if has_cron == has_interval:
            raise ValueError(
                "Supply exactly one schedule mode: either 'cron_expression' OR 'interval_seconds'."
            )
        return self


class ScheduleCreateRequest(BaseModel):
    """Request to attach a schedule to an existing trigger."""

    cron_expression: str | None = Field(default=None, max_length=64)
    interval_seconds: int | None = Field(default=None, gt=0, le=2_592_000)
    timezone: str = Field(default="UTC", max_length=64)
    missed_run_policy: MissedRunPolicy = "coalesce"
    enabled: bool = True

    @model_validator(mode="after")
    def validate_exclusive_schedule_mode(self) -> ScheduleCreateRequest:
        has_cron = bool(self.cron_expression and self.cron_expression.strip())
        has_interval = self.interval_seconds is not None
        if has_cron == has_interval:
            raise ValueError(
                "Supply exactly one schedule mode: either 'cron_expression' OR 'interval_seconds'."
            )
        return self


class TriggerDispatchRecord(BaseModel):
    """Durable workflow dispatch claim & execution history record."""

    dispatch_id: str = Field(default_factory=generate_dispatch_id)
    dispatch_key: str
    event_id: str
    trigger_id: str
    trigger_version: int = 1
    tenant_id: str
    workflow_id: str
    execution_mode: TriggerExecutionMode = "workflow"
    workflow_execution_id: str | None = None
    resource_key: str | None = None
    status: DispatchStatus = "claimed"
    reason: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TriggerRuleMatch(BaseModel):
    """Result of evaluating an event against a candidate TriggerRule."""

    trigger: TriggerRule
    matched: bool
    reason: str
    resource_key: str | None = None
