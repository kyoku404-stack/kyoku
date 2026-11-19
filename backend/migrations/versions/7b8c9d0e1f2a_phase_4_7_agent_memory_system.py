"""Phase 4.7 - Agent Memory System Schema Migration.

Revision ID: 7b8c9d0e1f2a
Revises: 6a7b8c9d0e1f
Create Date: 2026-11-19 18:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "7b8c9d0e1f2a"
down_revision: str | None = "6a7b8c9d0e1f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. memories
    op.create_table(
        "memories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("memory_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("memory_type", sa.String(length=64), nullable=False, server_default="preference"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False, server_default="user_input"),
        sa.Column("source_reference", sa.String(length=128), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("superseded_by", sa.String(length=128), nullable=True),
        sa.Column(
            "meta_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memories")),
    )
    op.create_index(op.f("ix_memories_memory_id"), "memories", ["memory_id"], unique=True)
    op.create_index(op.f("ix_memories_tenant_id"), "memories", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_memories_scope"), "memories", ["scope"], unique=False)
    op.create_index(op.f("ix_memories_owner_id"), "memories", ["owner_id"], unique=False)
    op.create_index(op.f("ix_memories_memory_type"), "memories", ["memory_type"], unique=False)
    op.create_index(op.f("ix_memories_content_hash"), "memories", ["content_hash"], unique=False)
    op.create_index(op.f("ix_memories_source_reference"), "memories", ["source_reference"], unique=False)
    op.create_index(op.f("ix_memories_status"), "memories", ["status"], unique=False)
    op.create_index(op.f("ix_memories_superseded_by"), "memories", ["superseded_by"], unique=False)
    op.create_index(op.f("ix_memories_expires_at"), "memories", ["expires_at"], unique=False)
    op.create_index(
        "idx_memories_tenant_scope",
        "memories",
        ["tenant_id", "scope"],
        unique=False,
    )
    op.create_index(
        "idx_memories_tenant_owner",
        "memories",
        ["tenant_id", "owner_id"],
        unique=False,
    )
    op.create_index(
        "idx_memories_tenant_status",
        "memories",
        ["tenant_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_memories_content_hash",
        "memories",
        ["tenant_id", "content_hash"],
        unique=False,
    )

    # 2. memory_proposals
    op.create_table(
        "memory_proposals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("proposal_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("proposer_id", sa.String(length=128), nullable=False),
        sa.Column("proposer_type", sa.String(length=32), nullable=False, server_default="agent"),
        sa.Column("memory_type", sa.String(length=64), nullable=False, server_default="preference"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("source_reference", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("rejection_reason", sa.String(length=256), nullable=True),
        sa.Column("approved_memory_id", sa.String(length=128), nullable=True),
        sa.Column(
            "meta_data",
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
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memory_proposals")),
    )
    op.create_index(op.f("ix_memory_proposals_proposal_id"), "memory_proposals", ["proposal_id"], unique=True)
    op.create_index(op.f("ix_memory_proposals_tenant_id"), "memory_proposals", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_memory_proposals_scope"), "memory_proposals", ["scope"], unique=False)
    op.create_index(op.f("ix_memory_proposals_owner_id"), "memory_proposals", ["owner_id"], unique=False)
    op.create_index(op.f("ix_memory_proposals_proposer_id"), "memory_proposals", ["proposer_id"], unique=False)
    op.create_index(op.f("ix_memory_proposals_status"), "memory_proposals", ["status"], unique=False)
    op.create_index(
        "idx_memory_proposals_tenant_status",
        "memory_proposals",
        ["tenant_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_memory_proposals_tenant_owner",
        "memory_proposals",
        ["tenant_id", "owner_id"],
        unique=False,
    )

    # 3. memory_versions
    op.create_table(
        "memory_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("memory_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=256), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memory_versions")),
    )
    op.create_index(op.f("ix_memory_versions_memory_id"), "memory_versions", ["memory_id"], unique=False)
    op.create_index(op.f("ix_memory_versions_tenant_id"), "memory_versions", ["tenant_id"], unique=False)
    op.create_index(
        "idx_memory_versions_memory_version",
        "memory_versions",
        ["memory_id", "version"],
        unique=False,
    )
    op.create_index(
        "idx_memory_versions_tenant_memory",
        "memory_versions",
        ["tenant_id", "memory_id"],
        unique=False,
    )

    # 4. memory_access_events
    op.create_table(
        "memory_access_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("memory_id", sa.String(length=128), nullable=True),
        sa.Column("scope", sa.String(length=32), nullable=True),
        sa.Column("allowed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("denial_reason", sa.String(length=64), nullable=True),
        sa.Column(
            "query_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("correlation_id", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memory_access_events")),
    )
    op.create_index(op.f("ix_memory_access_events_event_id"), "memory_access_events", ["event_id"], unique=True)
    op.create_index(op.f("ix_memory_access_events_tenant_id"), "memory_access_events", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_memory_access_events_user_id"), "memory_access_events", ["user_id"], unique=False)
    op.create_index(op.f("ix_memory_access_events_action"), "memory_access_events", ["action"], unique=False)
    op.create_index(op.f("ix_memory_access_events_memory_id"), "memory_access_events", ["memory_id"], unique=False)
    op.create_index(op.f("ix_memory_access_events_correlation_id"), "memory_access_events", ["correlation_id"], unique=False)
    op.create_index(
        "idx_memory_access_events_tenant_time",
        "memory_access_events",
        ["tenant_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_memory_access_events_tenant_memory",
        "memory_access_events",
        ["tenant_id", "memory_id"],
        unique=False,
    )
    op.create_index(
        "idx_memory_access_events_tenant_action",
        "memory_access_events",
        ["tenant_id", "action"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("memory_access_events")
    op.drop_table("memory_versions")
    op.drop_table("memory_proposals")
    op.drop_table("memories")
