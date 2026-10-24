"""KEEP Enterprise Platform — Ingestion Job Model (Phase 2.1).

Tracks the asynchronous ten-stage ingestion lifecycle, progress, OCR execution,
chunking statistics, and failure diagnostics.
Specification: devdocs/p2/p2.1.txt & docs/database/database-schema.md Section 3.13
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from backend.app.db.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.models.document import Document
    from backend.app.models.document_version import DocumentVersion
    from backend.app.models.organization import Organization


class IngestionJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Asynchronous ingestion pipeline task record for a document version."""

    __tablename__ = "ingestion_jobs"
    __table_args__ = (
        Index("idx_ingestion_jobs_tenant_status", "organization_id", "status"),
        Index("idx_ingestion_jobs_document", "document_id", "document_version_id"),
        Index("idx_ingestion_jobs_created_at", "created_at"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False, index=True
    )
    current_stage: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )
    progress_percent: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    total_pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunks_generated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    embeddings_generated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ocr_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    chunking_strategy: Mapped[str] = mapped_column(
        String(50), default="SEMANTIC_HEADING_AWARE", nullable=False
    )
    embedding_provider: Mapped[str] = mapped_column(
        String(50), default="OPENAI", nullable=False
    )
    embedding_model: Mapped[str] = mapped_column(
        String(100), default="text-embedding-3-small", nullable=False
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, server_default="{}", nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    @property
    def duration_seconds(self) -> float:
        """Calculates elapsed processing duration in seconds."""
        if not self.started_at:
            return 0.0
        end_time = self.completed_at or datetime.now(UTC)
        start = self.started_at
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=UTC)
        return max(0.0, round((end_time - start).total_seconds(), 2))

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    document: Mapped["Document"] = relationship("Document")
    document_version: Mapped["DocumentVersion"] = relationship("DocumentVersion")
