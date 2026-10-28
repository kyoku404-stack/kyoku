"""Phase 3.3 - Enterprise Security, Compliance, Governance & Data Protection Schema Migration

Revision ID: d2e3f4a5b6c7
Revises: c0d1e2f3a4b5
Create Date: 2026-10-28 15:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d2e3f4a5b6c7"
down_revision: str | None = "c0d1e2f3a4b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. security_mfa_credentials
    op.create_table(
        "security_mfa_credentials",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("secret_key", sa.String(length=255), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("backup_codes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_mfa_user"),
    )
    op.create_index("idx_mfa_user", "security_mfa_credentials", ["user_id"], unique=False)

    # 2. security_audit_logs
    op.create_table(
        "security_audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("resource", sa.String(length=80), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=False, server_default="127.0.0.1"),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="SUCCESS"),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_sec_audit_org_created", "security_audit_logs", ["organization_id", "created_at"], unique=False)
    op.create_index("idx_sec_audit_action", "security_audit_logs", ["action", "created_at"], unique=False)
    op.create_index("idx_sec_audit_user", "security_audit_logs", ["user_id", "created_at"], unique=False)

    # 3. security_data_classifications
    op.create_table(
        "security_data_classifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("classification_level", sa.String(length=30), nullable=False, server_default="INTERNAL"),
        sa.Column("detected_pii_entities", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("pii_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("scan_status", sa.String(length=30), nullable=False, server_default="COMPLETED"),
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", name="uq_data_classification_doc"),
    )
    op.create_index("idx_data_class_org", "security_data_classifications", ["organization_id", "classification_level"], unique=False)

    # 4. security_ai_governance_logs
    op.create_table(
        "security_ai_governance_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("retrieved_sources", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("guardrail_status", sa.String(length=30), nullable=False, server_default="PASSED"),
        sa.Column("guardrail_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("token_usage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("user_feedback", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ai_gov_org", "security_ai_governance_logs", ["organization_id", "created_at"], unique=False)
    op.create_index("idx_ai_gov_guardrail", "security_ai_governance_logs", ["guardrail_status"], unique=False)

    # 5. security_compliance_policies
    op.create_table(
        "security_compliance_policies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("standard", sa.String(length=40), nullable=False),
        sa.Column("control_key", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="COMPLIANT"),
        sa.Column("score", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "standard", "control_key", name="uq_compliance_control"),
    )
    op.create_index("idx_compliance_org_standard", "security_compliance_policies", ["organization_id", "standard"], unique=False)

    # 6. security_data_retention_rules
    op.create_table(
        "security_data_retention_rules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("resource_type", sa.String(length=60), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="365"),
        sa.Column("action_on_expiry", sa.String(length=30), nullable=False, server_default="ARCHIVE"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "resource_type", name="uq_retention_resource"),
    )

    # 7. security_erasure_requests
    op.create_table(
        "security_erasure_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("requester_id", sa.UUID(), nullable=True),
        sa.Column("target_user_id", sa.UUID(), nullable=False),
        sa.Column("target_email", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="COMPLETED"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("anonymized_assets_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("certificate_hash", sa.String(length=64), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_erasure_org", "security_erasure_requests", ["organization_id", "created_at"], unique=False)

    # 8. security_threat_alerts
    op.create_table(
        "security_threat_alerts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("alert_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="MEDIUM"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_ip", sa.String(length=45), nullable=False, server_default="127.0.0.1"),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_threat_alerts_org", "security_threat_alerts", ["organization_id", "resolved", "triggered_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_threat_alerts_org", table_name="security_threat_alerts")
    op.drop_table("security_threat_alerts")

    op.drop_index("idx_erasure_org", table_name="security_erasure_requests")
    op.drop_table("security_erasure_requests")

    op.drop_table("security_data_retention_rules")

    op.drop_index("idx_compliance_org_standard", table_name="security_compliance_policies")
    op.drop_table("security_compliance_policies")

    op.drop_index("idx_ai_gov_guardrail", table_name="security_ai_governance_logs")
    op.drop_index("idx_ai_gov_org", table_name="security_ai_governance_logs")
    op.drop_table("security_ai_governance_logs")

    op.drop_index("idx_data_class_org", table_name="security_data_classifications")
    op.drop_table("security_data_classifications")

    op.drop_index("idx_sec_audit_user", table_name="security_audit_logs")
    op.drop_index("idx_sec_audit_action", table_name="security_audit_logs")
    op.drop_index("idx_sec_audit_org_created", table_name="security_audit_logs")
    op.drop_table("security_audit_logs")

    op.drop_index("idx_mfa_user", table_name="security_mfa_credentials")
    op.drop_table("security_mfa_credentials")
