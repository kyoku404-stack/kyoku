"""Phase 4.6 - Tool-Calling Framework Schema Migration.

Revision ID: 6a7b8c9d0e1f
Revises: 5f6a7b8c9d0e
Create Date: 2026-11-19 12:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "6a7b8c9d0e1f"
down_revision: str | None = "5f6a7b8c9d0e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. tool_invocations
    op.create_table(
        "tool_invocations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("call_id", sa.String(length=128), nullable=False),
        sa.Column("tool_id", sa.String(length=128), nullable=False),
        sa.Column("tool_version", sa.String(length=32), nullable=False, server_default="1.0.0"),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("requested_by", sa.String(length=128), nullable=False),
        sa.Column("agent_execution_id", sa.String(length=128), nullable=True),
        sa.Column("workflow_execution_id", sa.String(length=128), nullable=True),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="succeeded"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column(
            "input_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "output_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("call_id"),
    )
    op.create_index("ix_tool_invocations_call_id", "tool_invocations", ["call_id"])
    op.create_index("ix_tool_invocations_tool_id", "tool_invocations", ["tool_id"])
    op.create_index("ix_tool_invocations_tenant_id", "tool_invocations", ["tenant_id"])
    op.create_index("ix_tool_invocations_requested_by", "tool_invocations", ["requested_by"])
    op.create_index("ix_tool_invocations_agent_execution_id", "tool_invocations", ["agent_execution_id"])
    op.create_index("ix_tool_invocations_workflow_execution_id", "tool_invocations", ["workflow_execution_id"])
    op.create_index("ix_tool_invocations_correlation_id", "tool_invocations", ["correlation_id"])
    op.create_index("ix_tool_invocations_status", "tool_invocations", ["status"])
    op.create_index(
        "idx_tool_invocations_tenant_status",
        "tool_invocations",
        ["tenant_id", "status"],
    )
    op.create_index(
        "idx_tool_invocations_tenant_tool",
        "tool_invocations",
        ["tenant_id", "tool_id"],
    )
    op.create_index(
        "idx_tool_invocations_idempotency",
        "tool_invocations",
        ["tenant_id", "requested_by", "idempotency_key"],
    )

    # 2. tool_audit_logs
    op.create_table(
        "tool_audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("call_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("tool_id", sa.String(length=128), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
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
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index("ix_tool_audit_logs_event_id", "tool_audit_logs", ["event_id"])
    op.create_index("ix_tool_audit_logs_call_id", "tool_audit_logs", ["call_id"])
    op.create_index("ix_tool_audit_logs_tenant_id", "tool_audit_logs", ["tenant_id"])
    op.create_index("ix_tool_audit_logs_user_id", "tool_audit_logs", ["user_id"])
    op.create_index("ix_tool_audit_logs_tool_id", "tool_audit_logs", ["tool_id"])
    op.create_index(
        "idx_tool_audit_tenant_tool",
        "tool_audit_logs",
        ["tenant_id", "tool_id"],
    )
    op.create_index(
        "idx_tool_audit_tenant_decision",
        "tool_audit_logs",
        ["tenant_id", "decision"],
    )


def downgrade() -> None:
    op.drop_table("tool_audit_logs")
    op.drop_table("tool_invocations")
