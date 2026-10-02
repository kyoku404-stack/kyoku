"""Initial schema

Revision ID: daede4011b68
Revises:
Create Date: 2026-10-02 17:11:56.756057+00:00

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "daede4011b68"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
