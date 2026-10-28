"""Phase 3.1 - Enterprise Integrations & Connector Framework Schema Migration

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
Create Date: 2026-10-28 02:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b9c0d1e2f3a4"
down_revision: str | None = "a8b9c0d1e2f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. connectors
    op.create_table(
        "connectors",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("platform_type", sa.String(length=50), nullable=False),
        sa.Column("platform_category", sa.String(length=50), nullable=False),
        sa.Column("auth_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="CONFIGURED"),
        sa.Column(
            "config_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("encrypted_credentials", sa.Text(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_status", sa.String(length=30), nullable=True),
        sa.Column("total_documents_synced", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name", name="uq_connectors_org_name"),
    )
    op.create_index(
        "idx_connectors_tenant_platform",
        "connectors",
        ["organization_id", "platform_type"],
        unique=False,
    )
    op.create_index(
        "idx_connectors_tenant_status",
        "connectors",
        ["organization_id", "status"],
        unique=False,
    )

    # 2. connector_sync_jobs
    op.create_table(
        "connector_sync_jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("connector_id", sa.UUID(), nullable=False),
        sa.Column("sync_mode", sa.String(length=30), nullable=False, server_default="INCREMENTAL"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("trigger_type", sa.String(length=30), nullable=False, server_default="MANUAL"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("documents_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("documents_added", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("documents_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("documents_deleted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("documents_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("documents_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["connector_id"],
            ["connectors.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_sync_jobs_tenant_connector",
        "connector_sync_jobs",
        ["organization_id", "connector_id"],
        unique=False,
    )
    op.create_index(
        "idx_sync_jobs_status",
        "connector_sync_jobs",
        ["organization_id", "status"],
        unique=False,
    )

    # 3. connector_sync_logs
    op.create_table(
        "connector_sync_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("connector_id", sa.UUID(), nullable=False),
        sa.Column("sync_job_id", sa.UUID(), nullable=True),
        sa.Column("external_document_id", sa.String(length=255), nullable=False),
        sa.Column("document_title", sa.String(length=512), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("action_taken", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="SUCCESS"),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["connector_id"],
            ["connectors.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sync_job_id"],
            ["connector_sync_jobs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_sync_logs_tenant_connector",
        "connector_sync_logs",
        ["organization_id", "connector_id"],
        unique=False,
    )
    op.create_index(
        "idx_sync_logs_job",
        "connector_sync_logs",
        ["sync_job_id"],
        unique=False,
    )
    op.create_index(
        "idx_sync_logs_external_doc",
        "connector_sync_logs",
        ["organization_id", "connector_id", "external_document_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_sync_logs_external_doc", table_name="connector_sync_logs")
    op.drop_index("idx_sync_logs_job", table_name="connector_sync_logs")
    op.drop_index("idx_sync_logs_tenant_connector", table_name="connector_sync_logs")
    op.drop_table("connector_sync_logs")

    op.drop_index("idx_sync_jobs_status", table_name="connector_sync_jobs")
    op.drop_index("idx_sync_jobs_tenant_connector", table_name="connector_sync_jobs")
    op.drop_table("connector_sync_jobs")

    op.drop_index("idx_connectors_tenant_status", table_name="connectors")
    op.drop_index("idx_connectors_tenant_platform", table_name="connectors")
    op.drop_table("connectors")
