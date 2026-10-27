"""Phase 2.5 - Enterprise Intelligence & Predictive Analytics Schema Migration

Revision ID: a8b9c0d1e2f3
Revises: f6a7b8c9d0e1
Create Date: 2026-10-28 00:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a8b9c0d1e2f3"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. analytics_snapshots
    op.create_table(
        "analytics_snapshots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("metric_category", sa.String(length=50), nullable=False),
        sa.Column("health_score", sa.Integer(), nullable=True),
        sa.Column(
            "metrics_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_analytics_snapshots_tenant_date",
        "analytics_snapshots",
        ["organization_id", "snapshot_date"],
        unique=False,
    )
    op.create_index(
        "idx_analytics_snapshots_category",
        "analytics_snapshots",
        ["organization_id", "metric_category"],
        unique=False,
    )

    # 2. ai_recommendations
    op.create_table(
        "ai_recommendations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("impact_score", sa.Float(), nullable=False),
        sa.Column("effort_score", sa.Float(), nullable=False),
        sa.Column("priority_index", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column(
            "action_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_recommendations_tenant_status",
        "ai_recommendations",
        ["organization_id", "status", "priority_index"],
        unique=False,
    )

    # 3. detected_anomalies
    op.create_table(
        "detected_anomalies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("anomaly_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), server_default="MEDIUM", nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("deviation_score", sa.Float(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_anomalies_tenant_time",
        "detected_anomalies",
        ["organization_id", "detected_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_anomalies_tenant_time", table_name="detected_anomalies")
    op.drop_table("detected_anomalies")

    op.drop_index("idx_recommendations_tenant_status", table_name="ai_recommendations")
    op.drop_table("ai_recommendations")

    op.drop_index("idx_analytics_snapshots_category", table_name="analytics_snapshots")
    op.drop_index("idx_analytics_snapshots_tenant_date", table_name="analytics_snapshots")
    op.drop_table("analytics_snapshots")
