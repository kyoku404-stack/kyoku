"""Phase 3.4 - Workflow Automation, Notifications & Event-Driven Intelligence Schema Migration

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-10-29 01:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e3f4a5b6c7d8"
down_revision: str | None = "d2e3f4a5b6c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. workflows
    op.create_table(
        "workflows",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("trigger_type", sa.String(length=50), nullable=False, server_default="EVENT"),
        sa.Column("event_pattern", sa.String(length=120), nullable=True),
        sa.Column("cron_expression", sa.String(length=60), nullable=True),
        sa.Column("condition_rules", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("trigger_type IN ('EVENT', 'SCHEDULE', 'MANUAL')", name="chk_workflow_trigger"),
    )
    op.create_index("idx_workflows_org_active", "workflows", ["organization_id", "is_active"])
    op.create_index("idx_workflows_event_pattern", "workflows", ["organization_id", "event_pattern"])

    # 2. workflow_steps
    op.create_table(
        "workflow_steps",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workflow_id", sa.UUID(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("action_type", sa.String(length=60), nullable=False),
        sa.Column("configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("depends_on_step_id", sa.UUID(), nullable=True),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["depends_on_step_id"], ["workflow_steps.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_id", "step_order", name="uq_workflow_step_order"),
    )
    op.create_index("idx_workflow_steps_order", "workflow_steps", ["workflow_id", "step_order"])

    # 3. workflow_executions
    op.create_table(
        "workflow_executions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workflow_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("triggered_by_event_id", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="RUNNING"),
        sa.Column("current_step_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("input_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("output_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("status IN ('RUNNING', 'WAITING_APPROVAL', 'COMPLETED', 'FAILED', 'CANCELLED')", name="chk_execution_status"),
    )
    op.create_index("idx_executions_org_status", "workflow_executions", ["organization_id", "status", "started_at"])
    op.create_index("idx_executions_workflow", "workflow_executions", ["workflow_id", "started_at"])

    # 4. workflow_execution_steps
    op.create_table(
        "workflow_execution_steps",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("execution_id", sa.UUID(), nullable=False),
        sa.Column("step_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="PENDING"),
        sa.Column("input_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("output_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["execution_id"], ["workflow_executions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["step_id"], ["workflow_steps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_exec_steps_execution", "workflow_execution_steps", ["execution_id"])

    # 5. workflow_approvals
    op.create_table(
        "workflow_approvals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("execution_id", sa.UUID(), nullable=False),
        sa.Column("step_id", sa.UUID(), nullable=True),
        sa.Column("requester_id", sa.UUID(), nullable=True),
        sa.Column("approver_id", sa.UUID(), nullable=True),
        sa.Column("approver_role", sa.String(length=50), nullable=False, server_default="OrgAdmin"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("decision_comments", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["execution_id"], ["workflow_executions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["step_id"], ["workflow_steps.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approver_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("status IN ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED')", name="chk_approval_status"),
    )
    op.create_index("idx_approvals_user_status", "workflow_approvals", ["approver_id", "status"])
    op.create_index("idx_approvals_execution", "workflow_approvals", ["execution_id"])

    # 6. Enhance notifications table with Phase 3.4 multi-channel columns
    op.add_column("notifications", sa.Column("channel", sa.String(length=30), nullable=False, server_default="IN_APP"))
    op.add_column("notifications", sa.Column("priority", sa.String(length=20), nullable=False, server_default="NORMAL"))
    op.add_column("notifications", sa.Column("category", sa.String(length=40), nullable=False, server_default="WORKFLOW"))
    op.add_column("notifications", sa.Column("read_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("notifications", sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")))

    # 7. notification_preferences
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "channel", "category", name="uq_user_channel_category"),
    )
    op.create_index("idx_notification_prefs_user", "notification_preferences", ["user_id"])

    # 8. workflow_templates
    op.create_table(
        "workflow_templates",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("trigger_type", sa.String(length=50), nullable=False, server_default="EVENT"),
        sa.Column("event_pattern", sa.String(length=120), nullable=True),
        sa.Column("cron_expression", sa.String(length=60), nullable=True),
        sa.Column("steps_definition", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("is_system_template", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("workflow_templates")
    op.drop_table("notification_preferences")

    op.drop_column("notifications", "metadata_json")
    op.drop_column("notifications", "read_at")
    op.drop_column("notifications", "category")
    op.drop_column("notifications", "priority")
    op.drop_column("notifications", "channel")

    op.drop_table("workflow_approvals")
    op.drop_table("workflow_execution_steps")
    op.drop_table("workflow_executions")
    op.drop_table("workflow_steps")
    op.drop_table("workflows")
