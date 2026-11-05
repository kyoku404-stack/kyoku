"""Phase 3.6 - Production Infrastructure, Scalability & Observability Schema Migration

Revision ID: 0a1b2c3d4e5f
Revises: f4a5b6c7d8e9
Create Date: 2026-11-06 03:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0a1b2c3d4e5f"
down_revision: str | None = "f4a5b6c7d8e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. system_deployments
    op.create_table(
        "system_deployments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("deployment_id", sa.String(length=100), nullable=False),
        sa.Column("service_name", sa.String(length=100), nullable=False, server_default="all"),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("strategy", sa.String(length=50), nullable=False, server_default="ROLLING"),
        sa.Column("environment", sa.String(length=50), nullable=False, server_default="production"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("rollback_version", sa.String(length=50), nullable=True),
        sa.Column("auto_rollback_on_failure", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("deployed_by", sa.UUID(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["deployed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deployment_id"),
    )
    op.create_index("idx_system_deployments_env_status", "system_deployments", ["environment", "status"])
    op.create_index("idx_system_deployments_started", "system_deployments", ["started_at"])

    # 2. system_backups
    op.create_table(
        "system_backups",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("backup_name", sa.String(length=120), nullable=False),
        sa.Column("backup_type", sa.String(length=50), nullable=False, server_default="DATABASE"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("storage_location", sa.String(length=255), nullable=False),
        sa.Column("rpo_drift_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("backup_name"),
    )
    op.create_index("idx_system_backups_status", "system_backups", ["status"])
    op.create_index("idx_system_backups_created", "system_backups", ["created_at"])

    # 3. system_health_snapshots
    op.create_table(
        "system_health_snapshots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="HEALTHY"),
        sa.Column("cpu_percent", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0.00"),
        sa.Column("memory_percent", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0.00"),
        sa.Column("disk_percent", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0.00"),
        sa.Column("active_requests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("subsystems", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_system_health_created", "system_health_snapshots", ["created_at"])

    # 4. system_audit_logs
    op.create_table(
        "system_audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("service_name", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False, server_default="INFO"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("trace_id", sa.String(length=100), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_system_audit_service_severity", "system_audit_logs", ["service_name", "severity"])
    op.create_index("idx_system_audit_trace", "system_audit_logs", ["trace_id"])
    op.create_index("idx_system_audit_created", "system_audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_system_audit_created", table_name="system_audit_logs")
    op.drop_index("idx_system_audit_trace", table_name="system_audit_logs")
    op.drop_index("idx_system_audit_service_severity", table_name="system_audit_logs")
    op.drop_table("system_audit_logs")

    op.drop_index("idx_system_health_created", table_name="system_health_snapshots")
    op.drop_table("system_health_snapshots")

    op.drop_index("idx_system_backups_created", table_name="system_backups")
    op.drop_index("idx_system_backups_status", table_name="system_backups")
    op.drop_table("system_backups")

    op.drop_index("idx_system_deployments_started", table_name="system_deployments")
    op.drop_index("idx_system_deployments_env_status", table_name="system_deployments")
    op.drop_table("system_deployments")
