"""Phase 3.2 - Real-Time Collaboration, Team Workspaces & Knowledge Sharing Schema Migration

Revision ID: c0d1e2f3a4b5
Revises: b9c0d1e2f3a4
Create Date: 2026-10-28 09:30:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c0d1e2f3a4b5"
down_revision: str | None = "b9c0d1e2f3a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. workspaces
    op.create_table(
        "workspaces",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("avatar_color", sa.String(length=30), nullable=False, server_default="#4F46E5"),
        sa.Column("is_private", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "slug", name="uq_workspace_org_slug"),
    )
    op.create_index("idx_workspaces_tenant", "workspaces", ["organization_id", "is_archived"], unique=False)
    op.create_index("idx_workspaces_slug", "workspaces", ["organization_id", "slug"], unique=False)

    # 2. workspace_members
    op.create_table(
        "workspace_members",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False, server_default="MEMBER"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
        sa.CheckConstraint("role IN ('ADMIN', 'MEMBER', 'VIEWER', 'GUEST')", name="chk_workspace_member_role"),
    )
    op.create_index("idx_workspace_members_user", "workspace_members", ["user_id"], unique=False)
    op.create_index("idx_workspace_members_workspace", "workspace_members", ["workspace_id", "role"], unique=False)

    # 3. document_comments
    op.create_table(
        "document_comments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=True),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("parent_comment_id", sa.UUID(), nullable=True),
        sa.Column("author_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("highlight_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="OPEN"),
        sa.Column("resolved_by_id", sa.UUID(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "mentions_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_comment_id"], ["document_comments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("status IN ('OPEN', 'RESOLVED', 'ARCHIVED')", name="chk_comment_status"),
    )
    op.create_index("idx_comments_doc", "document_comments", ["document_id", "parent_comment_id", "created_at"], unique=False)
    op.create_index("idx_comments_workspace", "document_comments", ["workspace_id", "status"], unique=False)
    op.create_index("idx_comments_author", "document_comments", ["author_id"], unique=False)

    # 4. document_version_history
    op.create_table(
        "document_version_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("editor_id", sa.UUID(), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=True),
        sa.Column("approval_status", sa.String(length=30), nullable=False, server_default="APPROVED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["editor_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "version_number", name="uq_doc_version"),
        sa.CheckConstraint("approval_status IN ('DRAFT', 'PENDING_REVIEW', 'APPROVED', 'REJECTED')", name="chk_approval_status"),
    )
    op.create_index("idx_version_history_doc", "document_version_history", ["document_id", "version_number"], unique=False)

    # 5. collaboration_activities
    op.create_table(
        "collaboration_activities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=True),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("activity_type", sa.String(length=60), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("entity_type", sa.String(length=60), nullable=False),
        sa.Column("entity_title", sa.String(length=512), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "activity_type IN ('DOCUMENT_UPLOAD', 'DOCUMENT_UPDATE', 'COMMENT_ADDED', 'REPLY_ADDED', "
            "'USER_MENTION', 'PROJECT_CREATED', 'MEMBER_JOINED', 'AI_SUMMARY_GENERATED', "
            "'DISCUSSION_RESOLVED', 'VERSION_CHECKPOINT')",
            name="chk_activity_type",
        ),
    )
    op.create_index("idx_activities_workspace", "collaboration_activities", ["workspace_id", "created_at"], unique=False)
    op.create_index("idx_activities_actor", "collaboration_activities", ["actor_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_table("collaboration_activities")
    op.drop_table("document_version_history")
    op.drop_table("document_comments")
    op.drop_table("workspace_members")
    op.drop_table("workspaces")
