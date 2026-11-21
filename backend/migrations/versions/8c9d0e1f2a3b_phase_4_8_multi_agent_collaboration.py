"""Phase 4.8 - Multi-Agent Collaboration Schema Migration.

Revision ID: 8c9d0e1f2a3b
Revises: 7b8c9d0e1f2a
Create Date: 2026-11-21 12:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "8c9d0e1f2a3b"
down_revision: str | None = "7b8c9d0e1f2a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. collaboration_sessions
    op.create_table(
        "collaboration_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("requested_by", sa.String(length=128), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="planning"),
        sa.Column("workflow_id", sa.String(length=128), nullable=True),
        sa.Column("max_agents", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("require_review", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("max_revisions", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "report",
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
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collaboration_sessions")),
    )
    op.create_index(op.f("ix_collaboration_sessions_session_id"), "collaboration_sessions", ["session_id"], unique=True)
    op.create_index(op.f("ix_collaboration_sessions_tenant_id"), "collaboration_sessions", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_collaboration_sessions_status"), "collaboration_sessions", ["status"], unique=False)
    op.create_index(op.f("ix_collaboration_sessions_workflow_id"), "collaboration_sessions", ["workflow_id"], unique=False)
    op.create_index("idx_collab_sessions_tenant_status", "collaboration_sessions", ["tenant_id", "status"])
    op.create_index("idx_collab_sessions_workflow", "collaboration_sessions", ["tenant_id", "workflow_id"])
    op.create_index("idx_collab_sessions_created_at", "collaboration_sessions", ["tenant_id", "created_at"])

    # 2. collaboration_tasks
    op.create_table(
        "collaboration_tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.String(length=128), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("agent_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column(
            "dependencies",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collaboration_tasks")),
    )
    op.create_index(op.f("ix_collaboration_tasks_task_id"), "collaboration_tasks", ["task_id"], unique=True)
    op.create_index(op.f("ix_collaboration_tasks_session_id"), "collaboration_tasks", ["session_id"], unique=False)
    op.create_index(op.f("ix_collaboration_tasks_tenant_id"), "collaboration_tasks", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_collaboration_tasks_agent_id"), "collaboration_tasks", ["agent_id"], unique=False)
    op.create_index(op.f("ix_collaboration_tasks_status"), "collaboration_tasks", ["status"], unique=False)
    op.create_index("idx_collab_tasks_session_status", "collaboration_tasks", ["session_id", "status"])
    op.create_index("idx_collab_tasks_tenant_agent", "collaboration_tasks", ["tenant_id", "agent_id"])

    # 3. collaboration_messages
    op.create_table(
        "collaboration_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("message_id", sa.String(length=128), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("sender_id", sa.String(length=128), nullable=False),
        sa.Column("recipient_id", sa.String(length=128), nullable=False),
        sa.Column("task_id", sa.String(length=128), nullable=True),
        sa.Column("message_type", sa.String(length=64), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("correlation_id", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collaboration_messages")),
    )
    op.create_index(op.f("ix_collaboration_messages_message_id"), "collaboration_messages", ["message_id"], unique=True)
    op.create_index(op.f("ix_collaboration_messages_session_id"), "collaboration_messages", ["session_id"], unique=False)
    op.create_index(op.f("ix_collaboration_messages_tenant_id"), "collaboration_messages", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_collaboration_messages_sender_id"), "collaboration_messages", ["sender_id"], unique=False)
    op.create_index(op.f("ix_collaboration_messages_recipient_id"), "collaboration_messages", ["recipient_id"], unique=False)
    op.create_index(op.f("ix_collaboration_messages_task_id"), "collaboration_messages", ["task_id"], unique=False)
    op.create_index(op.f("ix_collaboration_messages_correlation_id"), "collaboration_messages", ["correlation_id"], unique=False)
    op.create_index("idx_collab_messages_session_created", "collaboration_messages", ["session_id", "created_at"])
    op.create_index("idx_collab_messages_routing", "collaboration_messages", ["tenant_id", "sender_id", "recipient_id"])

    # 4. collaboration_findings
    op.create_table(
        "collaboration_findings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("finding_id", sa.String(length=128), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("task_id", sa.String(length=128), nullable=False),
        sa.Column("claim", sa.Text(), nullable=False),
        sa.Column(
            "evidence_refs",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "provenance",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("limitations", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collaboration_findings")),
    )
    op.create_index(op.f("ix_collaboration_findings_finding_id"), "collaboration_findings", ["finding_id"], unique=True)
    op.create_index(op.f("ix_collaboration_findings_session_id"), "collaboration_findings", ["session_id"], unique=False)
    op.create_index(op.f("ix_collaboration_findings_tenant_id"), "collaboration_findings", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_collaboration_findings_task_id"), "collaboration_findings", ["task_id"], unique=False)
    op.create_index("idx_collab_findings_session_task", "collaboration_findings", ["session_id", "task_id"])
    op.create_index("idx_collab_findings_tenant_created", "collaboration_findings", ["tenant_id", "created_at"])

    # 5. collaboration_reviews
    op.create_table(
        "collaboration_reviews",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("review_id", sa.String(length=128), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("reviewer_id", sa.String(length=128), nullable=False),
        sa.Column(
            "finding_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column(
            "reasons",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "unsupported_claims",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "missing_evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collaboration_reviews")),
    )
    op.create_index(op.f("ix_collaboration_reviews_review_id"), "collaboration_reviews", ["review_id"], unique=True)
    op.create_index(op.f("ix_collaboration_reviews_session_id"), "collaboration_reviews", ["session_id"], unique=False)
    op.create_index(op.f("ix_collaboration_reviews_tenant_id"), "collaboration_reviews", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_collaboration_reviews_reviewer_id"), "collaboration_reviews", ["reviewer_id"], unique=False)
    op.create_index("idx_collab_reviews_session_reviewer", "collaboration_reviews", ["session_id", "reviewer_id"])
    op.create_index("idx_collab_reviews_tenant_created", "collaboration_reviews", ["tenant_id", "created_at"])

    # 6. collaboration_conflicts
    op.create_table(
        "collaboration_conflicts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("conflict_id", sa.String(length=128), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column(
            "finding_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="detected"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("resolved_by", sa.String(length=128), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collaboration_conflicts")),
    )
    op.create_index(op.f("ix_collaboration_conflicts_conflict_id"), "collaboration_conflicts", ["conflict_id"], unique=True)
    op.create_index(op.f("ix_collaboration_conflicts_session_id"), "collaboration_conflicts", ["session_id"], unique=False)
    op.create_index(op.f("ix_collaboration_conflicts_tenant_id"), "collaboration_conflicts", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_collaboration_conflicts_status"), "collaboration_conflicts", ["status"], unique=False)
    op.create_index("idx_collab_conflicts_session_status", "collaboration_conflicts", ["session_id", "status"])
    op.create_index("idx_collab_conflicts_tenant_created", "collaboration_conflicts", ["tenant_id", "created_at"])


def downgrade() -> None:
    op.drop_table("collaboration_conflicts")
    op.drop_table("collaboration_reviews")
    op.drop_table("collaboration_findings")
    op.drop_table("collaboration_messages")
    op.drop_table("collaboration_tasks")
    op.drop_table("collaboration_sessions")
