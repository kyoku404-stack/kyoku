"""Phase 4.3 - Multi-Agent Workflow Orchestration & Step Linkage Schema Migration.

Revision ID: 3d4e5f6a7b8c
Revises: 2c3d4e5f6a7b
Create Date: 2026-11-18 01:55:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "3d4e5f6a7b8c"
down_revision: str | None = "2c3d4e5f6a7b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. agent_workflow_executions
    op.create_table(
        "agent_workflow_executions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workflow_execution_id", sa.String(length=128), nullable=False),
        sa.Column("workflow_id", sa.String(length=64), nullable=False),
        sa.Column("workflow_version", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("requested_by", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("mode", sa.String(length=16), nullable=False, server_default="async"),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column(
            "input_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result_ref", sa.String(length=256), nullable=True),
        sa.Column(
            "warnings_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("error_code", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.String(length=512), nullable=True),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("checkpoint_ref", sa.String(length=128), nullable=True),
        sa.Column(
            "cancel_requested", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_execution_id"),
        sa.UniqueConstraint(
            "tenant_id", "requested_by", "idempotency_key", name="uq_agent_wf_exec_idempotency"
        ),
    )
    op.create_index(
        "ix_agent_workflow_executions_workflow_execution_id",
        "agent_workflow_executions",
        ["workflow_execution_id"],
    )
    op.create_index(
        "ix_agent_workflow_executions_workflow_id", "agent_workflow_executions", ["workflow_id"]
    )
    op.create_index(
        "ix_agent_workflow_executions_tenant_id", "agent_workflow_executions", ["tenant_id"]
    )
    op.create_index(
        "ix_agent_workflow_executions_status", "agent_workflow_executions", ["status"]
    )
    op.create_index(
        "ix_agent_workflow_executions_correlation_id",
        "agent_workflow_executions",
        ["correlation_id"],
    )
    op.create_index(
        "idx_agent_wf_exec_tenant_status", "agent_workflow_executions", ["tenant_id", "status"]
    )
    op.create_index(
        "idx_agent_wf_exec_tenant_created", "agent_workflow_executions", ["tenant_id", "created_at"]
    )

    # 2. agent_workflow_steps
    op.create_table(
        "agent_workflow_steps",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("step_id", sa.String(length=128), nullable=False),
        sa.Column("workflow_execution_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("node_name", sa.String(length=128), nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=False),
        sa.Column("agent_execution_id", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="required"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="SUCCEEDED"),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=128), nullable=True),
        sa.Column(
            "is_side_effecting", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("step_id"),
    )
    op.create_index("ix_agent_workflow_steps_step_id", "agent_workflow_steps", ["step_id"])
    op.create_index(
        "ix_agent_workflow_steps_workflow_execution_id",
        "agent_workflow_steps",
        ["workflow_execution_id"],
    )
    op.create_index("ix_agent_workflow_steps_tenant_id", "agent_workflow_steps", ["tenant_id"])
    op.create_index(
        "ix_agent_workflow_steps_agent_execution_id",
        "agent_workflow_steps",
        ["agent_execution_id"],
    )
    op.create_index(
        "idx_agent_wf_step_exec_tenant",
        "agent_workflow_steps",
        ["workflow_execution_id", "tenant_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_agent_wf_step_exec_tenant", table_name="agent_workflow_steps")
    op.drop_index("ix_agent_workflow_steps_agent_execution_id", table_name="agent_workflow_steps")
    op.drop_index("ix_agent_workflow_steps_tenant_id", table_name="agent_workflow_steps")
    op.drop_index(
        "ix_agent_workflow_steps_workflow_execution_id", table_name="agent_workflow_steps"
    )
    op.drop_index("ix_agent_workflow_steps_step_id", table_name="agent_workflow_steps")
    op.drop_table("agent_workflow_steps")

    op.drop_index("idx_agent_wf_exec_tenant_created", table_name="agent_workflow_executions")
    op.drop_index("idx_agent_wf_exec_tenant_status", table_name="agent_workflow_executions")
    op.drop_index("ix_agent_workflow_executions_correlation_id", table_name="agent_workflow_executions")
    op.drop_index("ix_agent_workflow_executions_status", table_name="agent_workflow_executions")
    op.drop_index("ix_agent_workflow_executions_tenant_id", table_name="agent_workflow_executions")
    op.drop_index("ix_agent_workflow_executions_workflow_id", table_name="agent_workflow_executions")
    op.drop_index(
        "ix_agent_workflow_executions_workflow_execution_id", table_name="agent_workflow_executions"
    )
    op.drop_table("agent_workflow_executions")
