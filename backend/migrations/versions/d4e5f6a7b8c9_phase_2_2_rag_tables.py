"""Phase 2.2 - RAG Queries and Feedback Schema Migration

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-10-26 02:45:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create rag_queries table
    op.create_table(
        "rag_queries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("normalized_query", sa.Text(), nullable=True),
        sa.Column("response_text", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("is_grounded", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("dense_candidates_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("sparse_candidates_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reranked_chunks_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("retrieval_latency_ms", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("generation_latency_ms", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("total_latency_ms", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("completion_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "citations_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=True,
        ),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "idx_rag_queries_org_created",
        "rag_queries",
        ["organization_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_rag_queries_user",
        "rag_queries",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_rag_queries_session",
        "rag_queries",
        ["session_id"],
        unique=False,
    )

    # 2. Create rag_feedbacks table
    op.create_table(
        "rag_feedbacks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("query_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("is_helpful", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["query_id"], ["rag_queries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "idx_rag_feedbacks_query",
        "rag_feedbacks",
        ["query_id"],
        unique=False,
    )
    op.create_index(
        "idx_rag_feedbacks_org",
        "rag_feedbacks",
        ["organization_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_rag_feedbacks_org", table_name="rag_feedbacks")
    op.drop_index("idx_rag_feedbacks_query", table_name="rag_feedbacks")
    op.drop_table("rag_feedbacks")

    op.drop_index("idx_rag_queries_session", table_name="rag_queries")
    op.drop_index("idx_rag_queries_user", table_name="rag_queries")
    op.drop_index("idx_rag_queries_org_created", table_name="rag_queries")
    op.drop_table("rag_queries")
