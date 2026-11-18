"""Phase 4.4 - Planning & Reasoning Engine Schema Migration.

Revision ID: 4e5f6a7b8c9d
Revises: 3d4e5f6a7b8c
Create Date: 2026-11-18 19:33:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "4e5f6a7b8c9d"
down_revision: str | None = "3d4e5f6a7b8c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. agent_plans
    op.create_table(
        "agent_plans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("plan_id", sa.String(length=128), nullable=False),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("requested_by", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("goal_text", sa.Text(), nullable=False),
        sa.Column(
            "goal_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column(
            "input_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column(
            "execution_layers_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "validation_findings_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "approval_required", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "approval_reasons_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "clarification_questions_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("policy_version", sa.String(length=32), nullable=False, server_default="1.0.0"),
        sa.Column("max_steps", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("max_replans", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("replan_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "revision_reason",
            sa.String(length=512),
            nullable=False,
            server_default="Initial plan generation",
        ),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("source_request_id", sa.String(length=128), nullable=True),
        sa.Column("workflow_execution_id", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_id"),
    )
    op.create_index("ix_agent_plans_plan_id", "agent_plans", ["plan_id"])
    op.create_index("ix_agent_plans_tenant_id", "agent_plans", ["tenant_id"])
    op.create_index("ix_agent_plans_status", "agent_plans", ["status"])
    op.create_index("ix_agent_plans_correlation_id", "agent_plans", ["correlation_id"])
    op.create_index("ix_agent_plans_workflow_execution_id", "agent_plans", ["workflow_execution_id"])
    op.create_index("idx_agent_plans_tenant_status", "agent_plans", ["tenant_id", "status"])
    op.create_index("idx_agent_plans_tenant_created", "agent_plans", ["tenant_id", "created_at"])

    # 2. agent_plan_revisions
    op.create_table(
        "agent_plan_revisions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("revision_id", sa.String(length=128), nullable=False),
        sa.Column("plan_id", sa.String(length=128), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("revision_reason", sa.String(length=512), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False, server_default="1.0.0"),
        sa.Column(
            "snapshot_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "validation_findings_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("revision_id"),
    )
    op.create_index("ix_agent_plan_revisions_revision_id", "agent_plan_revisions", ["revision_id"])
    op.create_index("ix_agent_plan_revisions_plan_id", "agent_plan_revisions", ["plan_id"])
    op.create_index("ix_agent_plan_revisions_tenant_id", "agent_plan_revisions", ["tenant_id"])
    op.create_index("idx_agent_plan_rev_plan_ver", "agent_plan_revisions", ["plan_id", "version"])

    # 3. agent_plan_tasks
    op.create_table(
        "agent_plan_tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("plan_task_pk", sa.String(length=128), nullable=False),
        sa.Column("plan_id", sa.String(length=128), nullable=False),
        sa.Column("plan_version", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "required_capabilities_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "depends_on_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "input_refs_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("output_key", sa.String(length=128), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "requires_evidence", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "is_side_effecting", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("estimated_tokens", sa.Integer(), nullable=False, server_default="1500"),
        sa.Column("parallel_group", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resolved_agent_id", sa.String(length=64), nullable=True),
        sa.Column("resolved_agent_version", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_task_pk"),
    )
    op.create_index("ix_agent_plan_tasks_plan_task_pk", "agent_plan_tasks", ["plan_task_pk"])
    op.create_index("ix_agent_plan_tasks_plan_id", "agent_plan_tasks", ["plan_id"])
    op.create_index("ix_agent_plan_tasks_tenant_id", "agent_plan_tasks", ["tenant_id"])
    op.create_index("idx_agent_plan_tasks_plan_ver", "agent_plan_tasks", ["plan_id", "plan_version"])

    # 4. agent_plan_events
    op.create_table(
        "agent_plan_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("plan_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column(
            "details_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index("ix_agent_plan_events_event_id", "agent_plan_events", ["event_id"])
    op.create_index("ix_agent_plan_events_plan_id", "agent_plan_events", ["plan_id"])
    op.create_index("ix_agent_plan_events_tenant_id", "agent_plan_events", ["tenant_id"])
    op.create_index("ix_agent_plan_events_correlation_id", "agent_plan_events", ["correlation_id"])
    op.create_index(
        "idx_agent_plan_events_plan_tenant", "agent_plan_events", ["plan_id", "tenant_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_agent_plan_events_plan_tenant", table_name="agent_plan_events")
    op.drop_index("ix_agent_plan_events_correlation_id", table_name="agent_plan_events")
    op.drop_index("ix_agent_plan_events_tenant_id", table_name="agent_plan_events")
    op.drop_index("ix_agent_plan_events_plan_id", table_name="agent_plan_events")
    op.drop_index("ix_agent_plan_events_event_id", table_name="agent_plan_events")
    op.drop_table("agent_plan_events")

    op.drop_index("idx_agent_plan_tasks_plan_ver", table_name="agent_plan_tasks")
    op.drop_index("ix_agent_plan_tasks_tenant_id", table_name="agent_plan_tasks")
    op.drop_index("ix_agent_plan_tasks_plan_id", table_name="agent_plan_tasks")
    op.drop_index("ix_agent_plan_tasks_plan_task_pk", table_name="agent_plan_tasks")
    op.drop_table("agent_plan_tasks")

    op.drop_index("idx_agent_plan_rev_plan_ver", table_name="agent_plan_revisions")
    op.drop_index("ix_agent_plan_revisions_tenant_id", table_name="agent_plan_revisions")
    op.drop_index("ix_agent_plan_revisions_plan_id", table_name="agent_plan_revisions")
    op.drop_index("ix_agent_plan_revisions_revision_id", table_name="agent_plan_revisions")
    op.drop_table("agent_plan_revisions")

    op.drop_index("idx_agent_plans_tenant_created", table_name="agent_plans")
    op.drop_index("idx_agent_plans_tenant_status", table_name="agent_plans")
    op.drop_index("ix_agent_plans_workflow_execution_id", table_name="agent_plans")
    op.drop_index("ix_agent_plans_correlation_id", table_name="agent_plans")
    op.drop_index("ix_agent_plans_status", table_name="agent_plans")
    op.drop_index("ix_agent_plans_tenant_id", table_name="agent_plans")
    op.drop_index("ix_agent_plans_plan_id", table_name="agent_plans")
    op.drop_table("agent_plans")
