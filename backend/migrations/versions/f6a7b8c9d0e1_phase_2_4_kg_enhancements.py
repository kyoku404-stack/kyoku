"""Phase 2.4 - Knowledge Graph Enhancements Schema Migration

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-10-27 16:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add properties_json column to kg_relationships
    op.add_column(
        "kg_relationships",
        sa.Column(
            "properties_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=True,
        ),
    )

    # 2. Add performance & traversal indexes
    op.create_index(
        "idx_kg_entities_tenant_lookup",
        "kg_entities",
        ["organization_id", "entity_type", "is_deleted"],
        unique=False,
    )
    op.create_index(
        "idx_kg_rel_tenant_source",
        "kg_relationships",
        ["organization_id", "source_entity_id", "relation_type"],
        unique=False,
    )
    op.create_index(
        "idx_kg_rel_tenant_target",
        "kg_relationships",
        ["organization_id", "target_entity_id", "relation_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_kg_rel_tenant_target", table_name="kg_relationships")
    op.drop_index("idx_kg_rel_tenant_source", table_name="kg_relationships")
    op.drop_index("idx_kg_entities_tenant_lookup", table_name="kg_entities")
    op.drop_column("kg_relationships", "properties_json")
