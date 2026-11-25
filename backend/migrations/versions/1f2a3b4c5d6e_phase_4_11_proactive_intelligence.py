"""Phase 4.11: Proactive Enterprise Intelligence tables.

Revision ID: 1f2a3b4c5d6e
Revises: 0e1f2a3b4c5d
Create Date: 2026-11-25 16:48:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "1f2a3b4c5d6e"
down_revision: str | None = "0e1f2a3b4c5d"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "intelligence_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("trigger_source", sa.String(length=64), nullable=False),
        sa.Column("source_event_id", sa.String(length=128), nullable=True),
        sa.Column("detector_versions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("candidates_generated", sa.Integer(), nullable=False),
        sa.Column("insights_published", sa.Integer(), nullable=False),
        sa.Column("insights_suppressed", sa.Integer(), nullable=False),
        sa.Column("detector_errors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id"),
    )
    op.create_index("idx_intel_runs_tenant_status", "intelligence_runs", ["tenant_id", "status"])
    op.create_index(op.f("ix_intelligence_runs_run_id"), "intelligence_runs", ["run_id"])
    op.create_index(op.f("ix_intelligence_runs_tenant_id"), "intelligence_runs", ["tenant_id"])

    op.create_table(
        "intelligence_insights",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("insight_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("observed_facts", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("inferred_explanation", sa.Text(), nullable=True),
        sa.Column("limitations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evidence_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("affected_resource_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("audience_roles", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("impact_score", sa.Float(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("evidence_quality_score", sa.Float(), nullable=False),
        sa.Column("urgency_score", sa.Float(), nullable=False),
        sa.Column("novelty_score", sa.Float(), nullable=False),
        sa.Column("priority_score", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("dedup_key", sa.String(length=255), nullable=False),
        sa.Column("detector_id", sa.String(length=128), nullable=False),
        sa.Column("detector_version", sa.String(length=32), nullable=False),
        sa.Column("ranking_version", sa.String(length=32), nullable=False),
        sa.Column("workflow_execution_id", sa.String(length=128), nullable=True),
        sa.Column("owner_id", sa.String(length=128), nullable=True),
        sa.Column("source_freshness_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("insight_id"),
    )
    op.create_index("idx_intel_insights_tenant_status", "intelligence_insights", ["tenant_id", "status"])
    op.create_index("idx_intel_insights_tenant_priority", "intelligence_insights", ["tenant_id", "priority_score"])
    op.create_index("idx_intel_insights_tenant_dedup", "intelligence_insights", ["tenant_id", "dedup_key"])
    op.create_index(op.f("ix_intelligence_insights_insight_id"), "intelligence_insights", ["insight_id"])
    op.create_index(op.f("ix_intelligence_insights_tenant_id"), "intelligence_insights", ["tenant_id"])

    op.create_table(
        "intelligence_evidence",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("evidence_id", sa.String(length=128), nullable=False),
        sa.Column("insight_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("resource_ref", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_version", sa.String(length=64), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("validation_outcome", sa.String(length=32), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evidence_id"),
    )
    op.create_index("idx_intel_evidence_tenant_insight", "intelligence_evidence", ["tenant_id", "insight_id"])

    op.create_table(
        "intelligence_feedback",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("feedback_id", sa.String(length=128), nullable=False),
        sa.Column("insight_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("feedback", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("feedback_id"),
    )
    op.create_index("idx_intel_feedback_tenant_insight", "intelligence_feedback", ["tenant_id", "insight_id"])

    op.create_table(
        "intelligence_suppressions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("suppression_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("dedup_key", sa.String(length=255), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("suppressed_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("suppression_id"),
    )
    op.create_index("idx_intel_suppress_tenant_dedup", "intelligence_suppressions", ["tenant_id", "dedup_key"])
    op.create_index("idx_intel_suppress_until", "intelligence_suppressions", ["suppressed_until"])

    op.create_table(
        "intelligence_audit_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("audit_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("insight_id", sa.String(length=128), nullable=True),
        sa.Column("run_id", sa.String(length=128), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("audit_id"),
    )
    op.create_index("idx_intel_audit_tenant_action", "intelligence_audit_events", ["tenant_id", "action"])


def downgrade() -> None:
    op.drop_table("intelligence_audit_events")
    op.drop_table("intelligence_suppressions")
    op.drop_table("intelligence_feedback")
    op.drop_table("intelligence_evidence")
    op.drop_table("intelligence_insights")
    op.drop_table("intelligence_runs")
