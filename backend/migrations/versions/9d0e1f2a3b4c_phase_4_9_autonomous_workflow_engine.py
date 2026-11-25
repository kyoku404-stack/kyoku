"""Phase 4.9 - Autonomous Workflow Engine Schema Migration.

Revision ID: 9d0e1f2a3b4c
Revises: 8c9d0e1f2a3b
Create Date: 2026-11-25 15:15:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "9d0e1f2a3b4c"
down_revision: str | None = "8c9d0e1f2a3b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. autonomous_workflows
    op.create_table(
        "autonomous_workflows",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("execution_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("requested_by", sa.String(length=128), nullable=False),
        sa.Column("workflow_id", sa.String(length=128), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column(
            "policy_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "current_plan",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("current_step_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("replan_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("termination_reason", sa.Text(), nullable=True),
        sa.Column(
            "limitations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "final_result",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("checkpoint_ref", sa.String(length=128), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("idempotency_fingerprint", sa.String(length=128), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_autonomous_workflows")),
    )
    op.create_index(op.f("ix_autonomous_workflows_execution_id"), "autonomous_workflows", ["execution_id"], unique=True)
    op.create_index(op.f("ix_autonomous_workflows_tenant_id"), "autonomous_workflows", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_autonomous_workflows_requested_by"), "autonomous_workflows", ["requested_by"], unique=False)
    op.create_index(op.f("ix_autonomous_workflows_workflow_id"), "autonomous_workflows", ["workflow_id"], unique=False)
    op.create_index(op.f("ix_autonomous_workflows_status"), "autonomous_workflows", ["status"], unique=False)
    op.create_index(op.f("ix_autonomous_workflows_idempotency_key"), "autonomous_workflows", ["idempotency_key"], unique=False)
    op.create_index("idx_auto_wf_tenant_status", "autonomous_workflows", ["tenant_id", "status"])
    op.create_index("idx_auto_wf_tenant_created", "autonomous_workflows", ["tenant_id", "created_at"])
    op.create_index(
        "idx_auto_wf_idempotency",
        "autonomous_workflows",
        ["tenant_id", "requested_by", "idempotency_key"],
    )

    # 2. autonomous_workflow_steps
    op.create_table(
        "autonomous_workflow_steps",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("step_id", sa.String(length=128), nullable=False),
        sa.Column("execution_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("plan_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("step_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("agent_id", sa.String(length=128), nullable=False),
        sa.Column("tool_id", sa.String(length=128), nullable=True),
        sa.Column(
            "required_capability",
            sa.String(length=128),
            nullable=False,
            server_default="knowledge.research",
        ),
        sa.Column("is_side_effecting", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="2"),
        sa.Column(
            "inputs",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "outputs",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_autonomous_workflow_steps")),
    )
    op.create_index(op.f("ix_autonomous_workflow_steps_step_id"), "autonomous_workflow_steps", ["step_id"], unique=True)
    op.create_index(op.f("ix_autonomous_workflow_steps_execution_id"), "autonomous_workflow_steps", ["execution_id"], unique=False)
    op.create_index(op.f("ix_autonomous_workflow_steps_tenant_id"), "autonomous_workflow_steps", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_autonomous_workflow_steps_agent_id"), "autonomous_workflow_steps", ["agent_id"], unique=False)
    op.create_index(op.f("ix_autonomous_workflow_steps_status"), "autonomous_workflow_steps", ["status"], unique=False)
    op.create_index("idx_auto_steps_exec_order", "autonomous_workflow_steps", ["execution_id", "plan_version", "step_order"])
    op.create_index("idx_auto_steps_tenant_status", "autonomous_workflow_steps", ["tenant_id", "status"])

    # 3. autonomy_decisions
    op.create_table(
        "autonomy_decisions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("decision_id", sa.String(length=128), nullable=False),
        sa.Column("execution_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "evaluation_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("remaining_steps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_autonomy_decisions")),
    )
    op.create_index(op.f("ix_autonomy_decisions_decision_id"), "autonomy_decisions", ["decision_id"], unique=True)
    op.create_index(op.f("ix_autonomy_decisions_execution_id"), "autonomy_decisions", ["execution_id"], unique=False)
    op.create_index(op.f("ix_autonomy_decisions_tenant_id"), "autonomy_decisions", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_autonomy_decisions_action"), "autonomy_decisions", ["action"], unique=False)
    op.create_index("idx_auto_decisions_exec_created", "autonomy_decisions", ["execution_id", "created_at"])

    # 4. autonomy_events
    op.create_table(
        "autonomy_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("execution_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_autonomy_events")),
    )
    op.create_index(op.f("ix_autonomy_events_event_id"), "autonomy_events", ["event_id"], unique=True)
    op.create_index(op.f("ix_autonomy_events_execution_id"), "autonomy_events", ["execution_id"], unique=False)
    op.create_index(op.f("ix_autonomy_events_tenant_id"), "autonomy_events", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_autonomy_events_event_type"), "autonomy_events", ["event_type"], unique=False)
    op.create_index("idx_auto_events_exec_created", "autonomy_events", ["execution_id", "created_at"])

    # 5. autonomy_budgets
    op.create_table(
        "autonomy_budgets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("execution_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("max_steps", sa.Integer(), nullable=False),
        sa.Column("steps_consumed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_replans", sa.Integer(), nullable=False),
        sa.Column("replans_consumed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_agent_attempts", sa.Integer(), nullable=False),
        sa.Column("total_agent_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deadline_seconds", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_autonomy_budgets")),
    )
    op.create_index(op.f("ix_autonomy_budgets_execution_id"), "autonomy_budgets", ["execution_id"], unique=True)
    op.create_index(op.f("ix_autonomy_budgets_tenant_id"), "autonomy_budgets", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_table("autonomy_budgets")
    op.drop_table("autonomy_events")
    op.drop_table("autonomy_decisions")
    op.drop_table("autonomous_workflow_steps")
    op.drop_table("autonomous_workflows")
