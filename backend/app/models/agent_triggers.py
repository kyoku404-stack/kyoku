"""KEEP Phase 4.10 — Event-Driven & Trigger-Based Agents SQLAlchemy ORM Models.

Persists events (`events`), declarative trigger rules (`trigger_rules`),
queue delivery state (`event_deliveries`), unique workflow dispatch claims
(`trigger_dispatches`), schedules (`trigger_schedules`), and audit log (`event_audit_log`).

Specification: devdocs/p4/p4.10.txt (Section 11) & docs/Database/database-schema.md (Section 3.33)
Owner: Member 2 (Triggers, Schemas, Persistence & Migrations)
"""

from __future__ import annotations

import datetime
from typing import Any

from backend.app.db.base import Base, UUIDPrimaryKeyMixin
from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class AgentEventModel(Base, UUIDPrimaryKeyMixin):
    """Durable accepted KEEP event record."""

    __tablename__ = "events"
    __table_args__ = (
        Index("idx_events_tenant_type", "tenant_id", "event_type"),
        Index("idx_events_tenant_status", "tenant_id", "status"),
    )

    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    source: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    occurred_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
    outbox_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, default="accepted", nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class TriggerRuleModel(Base, UUIDPrimaryKeyMixin):
    """Tenant-scoped declarative event-to-workflow trigger rule."""

    __tablename__ = "trigger_rules"
    __table_args__ = (
        Index("idx_trigger_rules_tenant_event", "tenant_id", "event_type", "enabled"),
    )

    trigger_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    owner_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    workflow_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(32), default="workflow", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allowed_sources: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    conditions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_concurrent_runs: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_triggered_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )


class EventDeliveryModel(Base, UUIDPrimaryKeyMixin):
    """Durable event delivery queue record with retry backoff and dead-letter state."""

    __tablename__ = "event_deliveries"
    __table_args__ = (
        Index("idx_event_deliveries_status_retry", "status", "next_retry_at"),
        Index("idx_event_deliveries_tenant_status", "tenant_id", "status"),
    )

    delivery_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    event_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, default="pending", nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    worker_lease_until: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_retry_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), index=True, nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_permanent_failure: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )


class TriggerDispatchModel(Base, UUIDPrimaryKeyMixin):
    """Effectively-once workflow dispatch record guarded by unique dispatch_key."""

    __tablename__ = "trigger_dispatches"
    __table_args__ = (
        Index("idx_trigger_dispatches_trigger_created", "trigger_id", "created_at"),
        Index("idx_trigger_dispatches_tenant_status", "tenant_id", "status"),
    )

    dispatch_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    dispatch_key: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    event_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    trigger_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    trigger_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    workflow_id: Mapped[str] = mapped_column(String(128), nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(32), default="workflow", nullable=False)
    workflow_execution_id: Mapped[str | None] = mapped_column(
        String(128), index=True, nullable=True
    )
    resource_key: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="claimed", nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )


class TriggerScheduleModel(Base, UUIDPrimaryKeyMixin):
    """Persistent cron/interval schedule tied to a TriggerRule."""

    __tablename__ = "trigger_schedules"
    __table_args__ = (
        Index("idx_trigger_schedules_due", "enabled", "next_run_at"),
    )

    schedule_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    trigger_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    cron_expression: Mapped[str | None] = mapped_column(String(64), nullable=True)
    interval_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    missed_run_policy: Mapped[str] = mapped_column(String(32), default="coalesce", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    next_run_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    last_run_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class EventAuditLogModel(Base, UUIDPrimaryKeyMixin):
    """Append-only audit log for event ingestion, trigger matches, and webhook checks."""

    __tablename__ = "event_audit_log"
    __table_args__ = (
        Index("idx_event_audit_tenant_created", "tenant_id", "created_at"),
    )

    audit_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    event_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    trigger_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
