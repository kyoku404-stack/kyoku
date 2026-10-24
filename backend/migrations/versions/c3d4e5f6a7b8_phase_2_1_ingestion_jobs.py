"""Phase 2.1 - Ingestion Jobs Table Schema Migration

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-10-25 01:45:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create ingestion_jobs table
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("document_version_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="PENDING", nullable=False),
        sa.Column("current_stage", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("progress_percent", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("total_pages", sa.Integer(), server_default="0", nullable=False),
        sa.Column("processed_pages", sa.Integer(), server_default="0", nullable=False),
        sa.Column("chunks_generated", sa.Integer(), server_default="0", nullable=False),
        sa.Column("embeddings_generated", sa.Integer(), server_default="0", nullable=False),
        sa.Column("ocr_applied", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("chunking_strategy", sa.String(length=50), server_default="SEMANTIC_HEADING_AWARE", nullable=False),
        sa.Column("embedding_provider", sa.String(length=50), server_default="OPENAI", nullable=False),
        sa.Column("embedding_model", sa.String(length=100), server_default="text-embedding-3-small", nullable=False),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_retries", sa.Integer(), server_default="3", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_details_json", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "idx_ingestion_jobs_tenant_status",
        "ingestion_jobs",
        ["organization_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_ingestion_jobs_document",
        "ingestion_jobs",
        ["document_id", "document_version_id"],
        unique=False,
    )
    op.create_index(
        "idx_ingestion_jobs_created_at",
        "ingestion_jobs",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_ingestion_jobs_created_at", table_name="ingestion_jobs")
    op.drop_index("idx_ingestion_jobs_document", table_name="ingestion_jobs")
    op.drop_index("idx_ingestion_jobs_tenant_status", table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
