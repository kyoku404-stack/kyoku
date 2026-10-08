"""Initial schema

Revision ID: daede4011b68
Revises:
Create Date: 2026-10-02 17:11:56.756057+00:00

"""

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "daede4011b68"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 0. Enable pgvector extension if PostgreSQL
    bind = op.get_bind()
    if bind and bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 1. organizations
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("subscription", sa.String(length=50), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_organizations_domain", "organizations", ["domain"], unique=True)

    # 2. teams
    op.create_table(
        "teams",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_teams_organization_id", "teams", ["organization_id"], unique=False)

    # 3. users
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), server_default="Member", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("team_id", sa.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_organization_id", "users", ["organization_id"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # 4. projects
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="PLANNED", nullable=False),
        sa.Column("priority", sa.String(length=50), server_default="MEDIUM", nullable=False),
        sa.Column("timeline", sa.String(length=255), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_projects_organization_id", "projects", ["organization_id"], unique=False)

    # 5. project_users association
    op.create_table(
        "project_users",
        sa.Column("project_id", sa.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    )

    # 6. documents
    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploader_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("project_id", sa.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="PENDING", nullable=False),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_documents_organization_id", "documents", ["organization_id"], unique=False)

    # 7. document_chunks
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("document_id", sa.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(1536), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"], unique=False)

    # 8. meetings
    op.create_table(
        "meetings",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", sa.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("organizer_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("metadata_json", sa.String(length=1000), nullable=True),
        sa.Column("transcript_reference", sa.String(length=500), nullable=True),
        sa.Column("recording", sa.String(length=500), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 9. tasks
    op.create_table(
        "tasks",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", sa.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("assignment", sa.String(length=255), nullable=True),
        sa.Column("priority", sa.String(length=50), server_default="MEDIUM", nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="PENDING", nullable=False),
        sa.Column("completion_percentage", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tasks_project_id", "tasks", ["project_id"], unique=False)

    # 10. chat_sessions
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("metadata_json", sa.String(length=1000), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"], unique=False)

    # 11. chat_messages
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", sa.UUID(as_uuid=True), sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations_json", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"], unique=False)

    # 12. activity_logs
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=True),
        sa.Column("resource_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("details", sa.String(length=1000), nullable=True),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_activity_logs_organization_id", "activity_logs", ["organization_id"], unique=False)
    op.create_index("ix_activity_logs_user_id", "activity_logs", ["user_id"], unique=False)

    # 13. kg_entities
    op.create_table(
        "kg_entities",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("properties_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_kg_entities_organization_id", "kg_entities", ["organization_id"], unique=False)

    # 14. kg_relationships
    op.create_table(
        "kg_relationships",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_entity_id", sa.UUID(as_uuid=True), sa.ForeignKey("kg_entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_entity_id", sa.UUID(as_uuid=True), sa.ForeignKey("kg_entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.String(length=100), nullable=False),
        sa.Column("weight", sa.Float(), server_default=sa.text("1.0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_kg_relationships_organization_id", "kg_relationships", ["organization_id"], unique=False)


def downgrade() -> None:
    op.drop_table("kg_relationships")
    op.drop_table("kg_entities")
    op.drop_table("activity_logs")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("tasks")
    op.drop_table("meetings")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("project_users")
    op.drop_table("projects")
    op.drop_table("users")
    op.drop_table("teams")
    op.drop_table("organizations")
