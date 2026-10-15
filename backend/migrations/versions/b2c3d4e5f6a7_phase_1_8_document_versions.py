"""Phase 1.8 - Document Versions Table and Enhanced Documents Schema

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-15 12:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add Phase 1.8 columns to documents table
    op.add_column(
        "documents",
        sa.Column(
            "original_filename",
            sa.String(length=255),
            server_default="",
            nullable=False,
        ),
    )
    op.add_column("documents", sa.Column("title", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "documents",
        sa.Column(
            "mime_type",
            sa.String(length=100),
            server_default="application/octet-stream",
            nullable=False,
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "checksum_sha256", sa.String(length=64), server_default="", nullable=False
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "category", sa.String(length=50), server_default="REPORTS", nullable=False
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "current_version_number", sa.Integer(), server_default="1", nullable=False
        ),
    )
    op.add_column(
        "documents",
        sa.Column("current_version_id", sa.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("chunk_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column("documents", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column(
        "documents",
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )

    # 2. Create document_versions table
    op.create_table(
        "document_versions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "document_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column(
            "uploader_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("change_notes", sa.Text(), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "document_id", "version_number", name="uq_doc_versions_doc_num"
        ),
    )

    # 3. Add foreign key from documents.current_version_id to document_versions.id
    op.create_foreign_key(
        "fk_documents_current_version_id",
        "documents",
        "document_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
        use_alter=True,
    )

    # 4. Add document_version_id column to document_chunks
    op.add_column(
        "document_chunks",
        sa.Column(
            "document_version_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("document_versions.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )

    # 5. Create composite and single-column performance indexes
    op.create_index(
        "idx_docs_org_checksum",
        "documents",
        ["organization_id", "checksum_sha256"],
        unique=False,
    )
    op.create_index(
        "idx_docs_category",
        "documents",
        ["organization_id", "category"],
        unique=False,
    )
    op.create_index(
        "idx_docs_project",
        "documents",
        ["organization_id", "project_id"],
        unique=False,
    )
    op.create_index(
        "idx_doc_versions_doc_ver",
        "document_versions",
        ["document_id", "version_number"],
        unique=False,
    )
    op.create_index(
        "idx_doc_versions_checksum",
        "document_versions",
        ["checksum_sha256"],
        unique=False,
    )
    op.create_index(
        "idx_chunks_doc_version",
        "document_chunks",
        ["document_version_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_chunks_doc_version", table_name="document_chunks")
    op.drop_index("idx_doc_versions_checksum", table_name="document_versions")
    op.drop_index("idx_doc_versions_doc_ver", table_name="document_versions")
    op.drop_index("idx_docs_project", table_name="documents")
    op.drop_index("idx_docs_category", table_name="documents")
    op.drop_index("idx_docs_org_checksum", table_name="documents")

    # Drop document_version_id from document_chunks
    op.drop_column("document_chunks", "document_version_id")

    # Drop foreign key constraint
    op.drop_constraint(
        "fk_documents_current_version_id", "documents", type_="foreignkey"
    )

    # Drop document_versions table
    op.drop_table("document_versions")

    # Drop columns from documents
    op.drop_column("documents", "metadata_json")
    op.drop_column("documents", "error_message")
    op.drop_column("documents", "chunk_count")
    op.drop_column("documents", "current_version_id")
    op.drop_column("documents", "current_version_number")
    op.drop_column("documents", "tags")
    op.drop_column("documents", "category")
    op.drop_column("documents", "checksum_sha256")
    op.drop_column("documents", "mime_type")
    op.drop_column("documents", "description")
    op.drop_column("documents", "title")
    op.drop_column("documents", "original_filename")
