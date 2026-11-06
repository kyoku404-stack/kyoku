"""Phase 3.7 - Final Quality Assurance, Security Audit & Production Release Schema Migration

Revision ID: 1b2c3d4e5f6a
Revises: 0a1b2c3d4e5f
Create Date: 2026-11-06 05:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1b2c3d4e5f6a"
down_revision: str | None = "0a1b2c3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. production_releases
    op.create_table(
        "production_releases",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("release_id", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("release_tag", sa.String(length=50), nullable=False),
        sa.Column("git_commit", sa.String(length=50), nullable=False),
        sa.Column("changelog", sa.Text(), nullable=False),
        sa.Column("environment", sa.String(length=50), nullable=False, server_default="production"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="COMPLETED"),
        sa.Column("preflight_score", sa.Numeric(precision=4, scale=2), nullable=False, server_default="1.0"),
        sa.Column("artifacts_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("deployed_by", sa.UUID(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["deployed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("release_id"),
    )
    op.create_index("idx_releases_version", "production_releases", ["version"])
    op.create_index("idx_releases_tag", "production_releases", ["release_tag"])
    op.create_index("idx_releases_created", "production_releases", ["created_at"])

    # 2. release_checklists
    op.create_table(
        "release_checklists",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("release_id", sa.String(length=100), nullable=False),
        sa.Column("check_name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PASSED"),
        sa.Column("score", sa.Numeric(precision=4, scale=2), nullable=False, server_default="1.0"),
        sa.Column("details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["release_id"], ["production_releases.release_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_checklist_release_cat", "release_checklists", ["release_id", "category"])
    op.create_index("idx_checklist_verified", "release_checklists", ["verified_at"])

    # 3. security_audit_records
    op.create_table(
        "security_audit_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("audit_type", sa.String(length=80), nullable=False, server_default="OWASP_TOP_10"),
        sa.Column("compliance_standard", sa.String(length=100), nullable=False, server_default="OWASP_TOP_10_AND_LLM_TOP_10"),
        sa.Column("total_controls", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("passed_controls", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("failed_controls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overall_score", sa.Numeric(precision=5, scale=2), nullable=False, server_default="100.0"),
        sa.Column("controls_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("findings_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("auditor_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["auditor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_security_audit_score", "security_audit_records", ["overall_score"])
    op.create_index("idx_security_audit_created", "security_audit_records", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_security_audit_created", table_name="security_audit_records")
    op.drop_index("idx_security_audit_score", table_name="security_audit_records")
    op.drop_table("security_audit_records")

    op.drop_index("idx_checklist_verified", table_name="release_checklists")
    op.drop_index("idx_checklist_release_cat", table_name="release_checklists")
    op.drop_table("release_checklists")

    op.drop_index("idx_releases_created", table_name="production_releases")
    op.drop_index("idx_releases_tag", table_name="production_releases")
    op.drop_index("idx_releases_version", table_name="production_releases")
    op.drop_table("production_releases")
