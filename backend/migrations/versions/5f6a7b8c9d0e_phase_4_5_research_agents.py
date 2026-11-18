"""Phase 4.5 - Research Agents Schema Migration.

Revision ID: 5f6a7b8c9d0e
Revises: 4e5f6a7b8c9d
Create Date: 2026-11-18 21:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "5f6a7b8c9d0e"
down_revision: str | None = "4e5f6a7b8c9d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. research_runs
    op.create_table(
        "research_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("research_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("requested_by", sa.String(length=128), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column(
            "required_output",
            sa.String(length=32),
            nullable=False,
            server_default="detailed_report",
        ),
        sa.Column("max_sources", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "contradictions_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "unresolved_questions_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "follow_up_suggestions_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "warnings_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("correction_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sources_retrieved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sources_retained", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retrieval_latency_ms", sa.Integer(), nullable=True),
        sa.Column("synthesis_latency_ms", sa.Integer(), nullable=True),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("plan_id", sa.String(length=128), nullable=True),
        sa.Column("workflow_execution_id", sa.String(length=128), nullable=True),
        sa.Column("agent_execution_id", sa.String(length=128), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("error_code", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.String(length=512), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("research_id"),
    )
    op.create_index("ix_research_runs_research_id", "research_runs", ["research_id"])
    op.create_index("ix_research_runs_tenant_id", "research_runs", ["tenant_id"])
    op.create_index("ix_research_runs_requested_by", "research_runs", ["requested_by"])
    op.create_index("ix_research_runs_status", "research_runs", ["status"])
    op.create_index("ix_research_runs_correlation_id", "research_runs", ["correlation_id"])
    op.create_index("ix_research_runs_plan_id", "research_runs", ["plan_id"])
    op.create_index(
        "ix_research_runs_workflow_execution_id", "research_runs", ["workflow_execution_id"]
    )
    op.create_index("ix_research_runs_agent_execution_id", "research_runs", ["agent_execution_id"])
    op.create_index("idx_research_runs_tenant_status", "research_runs", ["tenant_id", "status"])
    op.create_index("idx_research_runs_tenant_created", "research_runs", ["tenant_id", "created_at"])
    op.create_index(
        "idx_research_runs_idempotency",
        "research_runs",
        ["tenant_id", "requested_by", "idempotency_key"],
    )

    # 2. research_evidence
    op.create_table(
        "research_evidence",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("record_pk", sa.String(length=128), nullable=False),
        sa.Column("research_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("source_title", sa.String(length=256), nullable=False),
        sa.Column("passage", sa.Text(), nullable=False),
        sa.Column("retrieval_reference", sa.String(length=256), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("document_date", sa.String(length=64), nullable=True),
        sa.Column("access_tier", sa.String(length=32), nullable=False, server_default="read"),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("record_pk"),
    )
    op.create_index("ix_research_evidence_record_pk", "research_evidence", ["record_pk"])
    op.create_index("ix_research_evidence_research_id", "research_evidence", ["research_id"])
    op.create_index("ix_research_evidence_tenant_id", "research_evidence", ["tenant_id"])
    op.create_index(
        "idx_research_evidence_run_tenant", "research_evidence", ["research_id", "tenant_id"]
    )

    # 3. research_findings
    op.create_table(
        "research_findings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("finding_pk", sa.String(length=128), nullable=False),
        sa.Column("research_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("finding_id", sa.String(length=64), nullable=False),
        sa.Column("claim", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(length=32), nullable=False, server_default="factual"),
        sa.Column(
            "evidence_ids_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("confidence", sa.String(length=16), nullable=False, server_default="low"),
        sa.Column(
            "limitations_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "has_contradiction", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("finding_pk"),
    )
    op.create_index("ix_research_findings_finding_pk", "research_findings", ["finding_pk"])
    op.create_index("ix_research_findings_research_id", "research_findings", ["research_id"])
    op.create_index("ix_research_findings_tenant_id", "research_findings", ["tenant_id"])
    op.create_index(
        "idx_research_findings_run_tenant", "research_findings", ["research_id", "tenant_id"]
    )

    # 4. research_events
    op.create_table(
        "research_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("research_id", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column(
            "details_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index("ix_research_events_event_id", "research_events", ["event_id"])
    op.create_index("ix_research_events_research_id", "research_events", ["research_id"])
    op.create_index("ix_research_events_tenant_id", "research_events", ["tenant_id"])
    op.create_index("ix_research_events_correlation_id", "research_events", ["correlation_id"])
    op.create_index(
        "idx_research_events_run_tenant", "research_events", ["research_id", "tenant_id"]
    )


def downgrade() -> None:
    op.drop_table("research_events")
    op.drop_table("research_findings")
    op.drop_table("research_evidence")
    op.drop_table("research_runs")
