"""Phase 4.10 - Event-Driven & Trigger-Based Agents Schema Migration.

Revision ID: 0e1f2a3b4c5d
Revises: 9d0e1f2a3b4c
Create Date: 2026-11-25 16:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0e1f2a3b4c5d"
down_revision: str | None = "9d0e1f2a3b4c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. events
    op.create_table(
        "events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("outbox_published", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="accepted"),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
    )
    op.create_index(op.f("ix_events_event_id"), "events", ["event_id"], unique=True)
    op.create_index(op.f("ix_events_event_type"), "events", ["event_type"], unique=False)
    op.create_index(op.f("ix_events_source"), "events", ["source"], unique=False)
    op.create_index(op.f("ix_events_tenant_id"), "events", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_events_resource_id"), "events", ["resource_id"], unique=False)
    op.create_index(op.f("ix_events_correlation_id"), "events", ["correlation_id"], unique=False)
    op.create_index(op.f("ix_events_status"), "events", ["status"], unique=False)
    op.create_index("idx_events_tenant_type", "events", ["tenant_id", "event_type"])
    op.create_index("idx_events_tenant_status", "events", ["tenant_id", "status"])

    # 2. trigger_rules
    op.create_table(
        "trigger_rules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("trigger_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("workflow_id", sa.String(length=128), nullable=False),
        sa.Column("execution_mode", sa.String(length=32), nullable=False, server_default="workflow"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "allowed_sources",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "conditions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("cooldown_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_concurrent_runs", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trigger_rules")),
    )
    op.create_index(op.f("ix_trigger_rules_trigger_id"), "trigger_rules", ["trigger_id"], unique=True)
    op.create_index(op.f("ix_trigger_rules_tenant_id"), "trigger_rules", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_trigger_rules_event_type"), "trigger_rules", ["event_type"], unique=False)
    op.create_index(op.f("ix_trigger_rules_workflow_id"), "trigger_rules", ["workflow_id"], unique=False)
    op.create_index(
        "idx_trigger_rules_tenant_event", "trigger_rules", ["tenant_id", "event_type", "enabled"]
    )

    # 3. event_deliveries
    op.create_table(
        "event_deliveries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("delivery_id", sa.String(length=128), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("worker_lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("is_permanent_failure", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_deliveries")),
    )
    op.create_index(op.f("ix_event_deliveries_delivery_id"), "event_deliveries", ["delivery_id"], unique=True)
    op.create_index(op.f("ix_event_deliveries_event_id"), "event_deliveries", ["event_id"], unique=False)
    op.create_index(op.f("ix_event_deliveries_tenant_id"), "event_deliveries", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_event_deliveries_status"), "event_deliveries", ["status"], unique=False)
    op.create_index(op.f("ix_event_deliveries_next_retry_at"), "event_deliveries", ["next_retry_at"], unique=False)
    op.create_index("idx_event_deliveries_status_retry", "event_deliveries", ["status", "next_retry_at"])
    op.create_index("idx_event_deliveries_tenant_status", "event_deliveries", ["tenant_id", "status"])

    # 4. trigger_dispatches
    op.create_table(
        "trigger_dispatches",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("dispatch_id", sa.String(length=128), nullable=False),
        sa.Column("dispatch_key", sa.String(length=256), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("trigger_id", sa.String(length=128), nullable=False),
        sa.Column("trigger_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("workflow_id", sa.String(length=128), nullable=False),
        sa.Column("execution_mode", sa.String(length=32), nullable=False, server_default="workflow"),
        sa.Column("workflow_execution_id", sa.String(length=128), nullable=True),
        sa.Column("resource_key", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="claimed"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trigger_dispatches")),
    )
    op.create_index(op.f("ix_trigger_dispatches_dispatch_id"), "trigger_dispatches", ["dispatch_id"], unique=True)
    op.create_index(op.f("ix_trigger_dispatches_dispatch_key"), "trigger_dispatches", ["dispatch_key"], unique=True)
    op.create_index(op.f("ix_trigger_dispatches_event_id"), "trigger_dispatches", ["event_id"], unique=False)
    op.create_index(op.f("ix_trigger_dispatches_trigger_id"), "trigger_dispatches", ["trigger_id"], unique=False)
    op.create_index(op.f("ix_trigger_dispatches_tenant_id"), "trigger_dispatches", ["tenant_id"], unique=False)
    op.create_index(
        op.f("ix_trigger_dispatches_workflow_execution_id"),
        "trigger_dispatches",
        ["workflow_execution_id"],
        unique=False,
    )
    op.create_index(op.f("ix_trigger_dispatches_resource_key"), "trigger_dispatches", ["resource_key"], unique=False)
    op.create_index(op.f("ix_trigger_dispatches_status"), "trigger_dispatches", ["status"], unique=False)
    op.create_index(
        "idx_trigger_dispatches_trigger_created", "trigger_dispatches", ["trigger_id", "created_at"]
    )
    op.create_index("idx_trigger_dispatches_tenant_status", "trigger_dispatches", ["tenant_id", "status"])

    # 5. trigger_schedules
    op.create_table(
        "trigger_schedules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("schedule_id", sa.String(length=128), nullable=False),
        sa.Column("trigger_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("cron_expression", sa.String(length=64), nullable=True),
        sa.Column("interval_seconds", sa.Integer(), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column("missed_run_policy", sa.String(length=32), nullable=False, server_default="coalesce"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trigger_schedules")),
    )
    op.create_index(op.f("ix_trigger_schedules_schedule_id"), "trigger_schedules", ["schedule_id"], unique=True)
    op.create_index(op.f("ix_trigger_schedules_trigger_id"), "trigger_schedules", ["trigger_id"], unique=False)
    op.create_index(op.f("ix_trigger_schedules_tenant_id"), "trigger_schedules", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_trigger_schedules_next_run_at"), "trigger_schedules", ["next_run_at"], unique=False)
    op.create_index("idx_trigger_schedules_due", "trigger_schedules", ["enabled", "next_run_at"])

    # 6. event_audit_log
    op.create_table(
        "event_audit_log",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("audit_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=True),
        sa.Column("trigger_id", sa.String(length=128), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_audit_log")),
    )
    op.create_index(op.f("ix_event_audit_log_audit_id"), "event_audit_log", ["audit_id"], unique=True)
    op.create_index(op.f("ix_event_audit_log_tenant_id"), "event_audit_log", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_event_audit_log_event_id"), "event_audit_log", ["event_id"], unique=False)
    op.create_index(op.f("ix_event_audit_log_trigger_id"), "event_audit_log", ["trigger_id"], unique=False)
    op.create_index(op.f("ix_event_audit_log_action"), "event_audit_log", ["action"], unique=False)
    op.create_index("idx_event_audit_tenant_created", "event_audit_log", ["tenant_id", "created_at"])


def downgrade() -> None:
    op.drop_table("event_audit_log")
    op.drop_table("trigger_schedules")
    op.drop_table("trigger_dispatches")
    op.drop_table("event_deliveries")
    op.drop_table("trigger_rules")
    op.drop_table("events")
