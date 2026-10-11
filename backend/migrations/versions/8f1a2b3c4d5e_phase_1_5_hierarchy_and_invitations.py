"""Phase 1.5 - Organization hierarchy, departments, teams, projects, and invitations

Revision ID: 8f1a2b3c4d5e
Revises: daede4011b68
Create Date: 2026-10-11 12:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f1a2b3c4d5e"
down_revision: str | None = "daede4011b68"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add new columns to organizations
    op.add_column("organizations", sa.Column("industry", sa.String(length=100), nullable=True))
    op.add_column("organizations", sa.Column("company_size", sa.String(length=50), nullable=True))
    op.add_column("organizations", sa.Column("time_zone", sa.String(length=100), server_default="UTC", nullable=True))
    op.add_column("organizations", sa.Column("default_language", sa.String(length=20), server_default="en-US", nullable=True))
    op.add_column("organizations", sa.Column("logo_url", sa.String(length=512), nullable=True))
    op.add_column("organizations", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("organizations", sa.Column("settings_json", sa.Text(), nullable=True))

    # 2. Create departments table
    op.create_table(
        "departments",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("manager_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_departments_organization_id", "departments", ["organization_id"], unique=False)
    op.create_unique_constraint("uq_departments_org_name", "departments", ["organization_id", "name"])

    # 3. Add department_id and lead_user_id to teams
    op.add_column("teams", sa.Column("department_id", sa.UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True))
    op.add_column("teams", sa.Column("lead_user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_teams_department_id", "teams", ["department_id"], unique=False)

    # 4. Add department_id to users
    op.add_column("users", sa.Column("department_id", sa.UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_users_department_id", "users", ["department_id"], unique=False)

    # 5. Add team_id and owner_id to projects
    op.add_column("projects", sa.Column("team_id", sa.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True))
    op.add_column("projects", sa.Column("owner_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_projects_team_id", "projects", ["team_id"], unique=False)

    # 6. Create invitations table
    op.create_table(
        "invitations",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("department_id", sa.UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("team_id", sa.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), server_default="Member", nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="PENDING", nullable=False),
        sa.Column("invited_by_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_invitations_organization_id", "invitations", ["organization_id"], unique=False)
    op.create_index("ix_invitations_email", "invitations", ["email"], unique=False)
    op.create_index("ix_invitations_token", "invitations", ["token"], unique=True)
    op.create_unique_constraint("uq_invitations_org_email_pending", "invitations", ["organization_id", "email", "status"])


def downgrade() -> None:
    op.drop_table("invitations")

    op.drop_index("ix_projects_team_id", table_name="projects")
    op.drop_column("projects", "owner_id")
    op.drop_column("projects", "team_id")

    op.drop_index("ix_users_department_id", table_name="users")
    op.drop_column("users", "department_id")

    op.drop_index("ix_teams_department_id", table_name="teams")
    op.drop_column("teams", "lead_user_id")
    op.drop_column("teams", "department_id")

    op.drop_table("departments")

    op.drop_column("organizations", "settings_json")
    op.drop_column("organizations", "description")
    op.drop_column("organizations", "logo_url")
    op.drop_column("organizations", "default_language")
    op.drop_column("organizations", "time_zone")
    op.drop_column("organizations", "company_size")
    op.drop_column("organizations", "industry")
