"""KEEP Enterprise Platform — Document Version Model (Phase 1.8).

Stores immutable physical file revisions, author attributions, change notes,
and version snapshots for audit and rollback.
Specification: devdocs/p1/p1.8.txt Chapter 11 & docs/database/database-schema.md Section 3.5.1
"""

import uuid
from typing import TYPE_CHECKING, Any

from backend.app.db.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.models.document import Document
    from backend.app.models.knowledge import DocumentChunk
    from backend.app.models.user import User


class DocumentVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Immutable version snapshot representing an uploaded physical file revision."""

    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "version_number", name="uq_doc_versions_doc_num"
        ),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    change_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default="{}", default=dict, nullable=False
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        foreign_keys=[document_id],
        back_populates="versions",
    )
    uploader: Mapped["User"] = relationship(
        "User",
        foreign_keys=[uploader_id],
    )
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document_version",
        cascade="all, delete-orphan",
    )
