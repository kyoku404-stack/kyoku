"""KEEP Enterprise Platform — Document Model (Phase 1.8).

Represents logical digital knowledge assets, metadata headers, and container
references for document version lineage.
Specification: devdocs/p1/p1.8.txt Chapter 9 & docs/database/database-schema.md Section 3.5
"""

import uuid
from typing import TYPE_CHECKING, Any

from backend.app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.models.document_version import DocumentVersion
    from backend.app.models.knowledge import DocumentChunk
    from backend.app.models.organization import Organization
    from backend.app.models.project import Project
    from backend.app.models.user import User


class Document(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Document container entity representing an enterprise knowledge asset."""

    __tablename__ = "documents"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    uploader_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), index=True, nullable=True
    )

    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "document_versions.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_documents_current_version_id",
        ),
        nullable=True,
    )
    current_version_number: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(
        String(255), default="", nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    mime_type: Mapped[str] = mapped_column(
        String(100), default="application/octet-stream", nullable=False
    )
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(
        String(64), default="", index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(
        String(50), default="REPORTS", index=True, nullable=False
    )
    tags: Mapped[list[str]] = mapped_column(
        JSONB, server_default="[]", default=list, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default="AWAITING_PROCESSING", index=True, nullable=False
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default="{}", default=dict, nullable=False
    )

    # Legacy fields preserved for backward compatibility
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="documents"
    )
    uploader: Mapped["User | None"] = relationship("User", back_populates="documents")
    project: Mapped["Project | None"] = relationship(
        "Project", back_populates="documents"
    )

    current_version: Mapped["DocumentVersion | None"] = relationship(
        "DocumentVersion",
        foreign_keys=[current_version_id],
        post_update=True,
    )
    versions: Mapped[list["DocumentVersion"]] = relationship(
        "DocumentVersion",
        foreign_keys="[DocumentVersion.document_id]",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.version_number.desc()",
    )
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )
