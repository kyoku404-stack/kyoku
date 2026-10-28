"""Phase 3.5 - Plugin SDK, Extension Framework & Developer Ecosystem Schema Migration

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-10-29 12:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f4a5b6c7d8e9"
down_revision: str | None = "e3f4a5b6c7d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. plugins
    op.create_table(
        "plugins",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("developer", sa.String(length=150), nullable=False),
        sa.Column("current_version", sa.String(length=30), nullable=False, server_default="1.0.0"),
        sa.Column("verification_tier", sa.String(length=30), nullable=False, server_default="COMMUNITY"),
        sa.Column("rating", sa.Numeric(precision=3, scale=2), nullable=False, server_default="5.00"),
        sa.Column("installs_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("icon_url", sa.String(length=500), nullable=True),
        sa.Column("documentation_url", sa.String(length=500), nullable=True),
        sa.Column("source_repository", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_plugins_category", "plugins", ["category"])
    op.create_index("idx_plugins_tier", "plugins", ["verification_tier"])

    # 2. plugin_manifests
    op.create_table(
        "plugin_manifests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("plugin_id", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=30), nullable=False),
        sa.Column("manifest_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("min_keep_version", sa.String(length=30), nullable=False, server_default="3.0.0"),
        sa.Column("max_keep_version", sa.String(length=30), nullable=False, server_default="3.9.9"),
        sa.Column("entry_point", sa.String(length=255), nullable=False),
        sa.Column("permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("event_hooks", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("configuration_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["plugin_id"], ["plugins.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plugin_id", "version", name="uq_plugin_manifest_version"),
    )
    op.create_index("idx_plugin_manifests_lookup", "plugin_manifests", ["plugin_id", "version"])

    # 3. plugin_installations
    op.create_table(
        "plugin_installations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("plugin_id", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="ACTIVE"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("installed_by", sa.UUID(), nullable=True),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plugin_id"], ["plugins.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["installed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "plugin_id", name="uq_org_plugin_installation"),
    )
    op.create_index("idx_plugin_installations_org", "plugin_installations", ["organization_id", "status"])

    # 4. plugin_permissions
    op.create_table(
        "plugin_permissions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("installation_id", sa.UUID(), nullable=False),
        sa.Column("permission", sa.String(length=80), nullable=False),
        sa.Column("is_granted", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("granted_by", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["installation_id"], ["plugin_installations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("installation_id", "permission", name="uq_installation_permission"),
    )
    op.create_index("idx_plugin_permissions_inst", "plugin_permissions", ["installation_id"])

    # 5. plugin_event_hooks
    op.create_table(
        "plugin_event_hooks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("installation_id", sa.UUID(), nullable=False),
        sa.Column("event_topic", sa.String(length=120), nullable=False),
        sa.Column("handler_method", sa.String(length=120), nullable=False, server_default="on_event"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["installation_id"], ["plugin_installations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("installation_id", "event_topic", name="uq_installation_event"),
    )
    op.create_index("idx_plugin_event_hooks_topic", "plugin_event_hooks", ["event_topic", "is_active"])

    # 6. plugin_execution_logs
    op.create_table(
        "plugin_execution_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("installation_id", sa.UUID(), nullable=True),
        sa.Column("plugin_id", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("triggered_by", sa.String(length=50), nullable=False, server_default="direct_api"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("payload_preview", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["installation_id"], ["plugin_installations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_plugin_logs_org", "plugin_execution_logs", ["organization_id", "created_at"])
    op.create_index("idx_plugin_logs_status", "plugin_execution_logs", ["plugin_id", "status"])


def downgrade() -> None:
    op.drop_index("idx_plugin_logs_status", table_name="plugin_execution_logs")
    op.drop_index("idx_plugin_logs_org", table_name="plugin_execution_logs")
    op.drop_table("plugin_execution_logs")

    op.drop_index("idx_plugin_event_hooks_topic", table_name="plugin_event_hooks")
    op.drop_table("plugin_event_hooks")

    op.drop_index("idx_plugin_permissions_inst", table_name="plugin_permissions")
    op.drop_table("plugin_permissions")

    op.drop_index("idx_plugin_installations_org", table_name="plugin_installations")
    op.drop_table("plugin_installations")

    op.drop_index("idx_plugin_manifests_lookup", table_name="plugin_manifests")
    op.drop_table("plugin_manifests")

    op.drop_index("idx_plugins_tier", table_name="plugins")
    op.drop_index("idx_plugins_category", table_name="plugins")
    op.drop_table("plugins")
