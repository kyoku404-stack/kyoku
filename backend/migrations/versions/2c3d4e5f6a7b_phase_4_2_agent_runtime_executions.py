"""Phase 4.2 - Agent Runtime Executions & Graph Checkpoints Schema Migration.

Revision ID: 2c3d4e5f6a7b
Revises: 1b2c3d4e5f6a
Create Date: 2026-11-18 01:10:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "2c3d4e5f6a7b"
down_revision: str | None = "1b2c3d4e5f6a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. agent_executions
    op.create_table(
        "agent_executions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("execution_id", sa.String(length=128), nullable=False),
        sa.Column("task_id", sa.String(length=128), nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=False),
        sa.Column("agent_version", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("requested_by", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("mode", sa.String(length=16), nullable=False, server_default="sync"),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("input_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("input_ref", sa.String(length=256), nullable=True),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result_ref", sa.String(length=256), nullable=True),
        sa.Column("error_code", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.String(length=512), nullable=True),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("parent_execution_id", sa.String(length=128), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("cancel_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("queue_wait_ms", sa.Integer(), nullable=True),
        sa.Column("checkpoint_thread_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("execution_id"),
        sa.UniqueConstraint("tenant_id", "requested_by", "idempotency_key", name="uq_agent_exec_idempotency"),
    )
    op.create_index("ix_agent_executions_execution_id", "agent_executions", ["execution_id"])
    op.create_index("ix_agent_executions_task_id", "agent_executions", ["task_id"])
    op.create_index("ix_agent_executions_agent_id", "agent_executions", ["agent_id"])
    op.create_index("ix_agent_executions_tenant_id", "agent_executions", ["tenant_id"])
    op.create_index("ix_agent_executions_status", "agent_executions", ["status"])
    op.create_index("ix_agent_executions_correlation_id", "agent_executions", ["correlation_id"])
    op.create_index("idx_agent_exec_tenant_status", "agent_executions", ["tenant_id", "status"])
    op.create_index("idx_agent_exec_tenant_created", "agent_executions", ["tenant_id", "created_at"])

    # 2. agent_checkpoints
    op.create_table(
        "agent_checkpoints",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("checkpoint_id", sa.String(length=128), nullable=False),
        sa.Column("execution_id", sa.String(length=128), nullable=False),
        sa.Column("thread_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("step_name", sa.String(length=128), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("state_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("checkpoint_id"),
    )
    op.create_index("ix_agent_checkpoints_execution_id", "agent_checkpoints", ["execution_id"])
    op.create_index("ix_agent_checkpoints_thread_id", "agent_checkpoints", ["thread_id"])
    op.create_index("ix_agent_checkpoints_tenant_id", "agent_checkpoints", ["tenant_id"])
    op.create_index("idx_agent_chk_exec_step", "agent_checkpoints", ["execution_id", "step_number"])
    op.create_index("idx_agent_chk_tenant_thread", "agent_checkpoints", ["tenant_id", "thread_id"])


def downgrade() -> None:
    op.drop_index("idx_agent_chk_tenant_thread", table_name="agent_checkpoints")
    op.drop_index("idx_agent_chk_exec_step", table_name="agent_checkpoints")
    op.drop_index("ix_agent_checkpoints_tenant_id", table_name="agent_checkpoints")
    op.drop_index("ix_agent_checkpoints_thread_id", table_name="agent_checkpoints")
    op.drop_index("ix_agent_checkpoints_execution_id", table_name="agent_checkpoints")
    op.drop_table("agent_checkpoints")

    op.drop_index("idx_agent_exec_tenant_created", table_name="agent_executions")
    op.drop_index("idx_agent_exec_tenant_status", table_name="agent_executions")
    op.drop_index("ix_agent_executions_correlation_id", table_name="agent_executions")
    op.drop_index("ix_agent_executions_status", table_name="agent_executions")
    op.drop_index("ix_agent_executions_tenant_id", table_name="agent_executions")
    op.drop_index("ix_agent_executions_agent_id", table_name="agent_executions")
    op.drop_index("ix_agent_executions_task_id", table_name="agent_executions")
    op.drop_index("ix_agent_executions_execution_id", table_name="agent_executions")
    op.drop_table("agent_executions")
