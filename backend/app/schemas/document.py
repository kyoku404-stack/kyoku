"""KEEP Enterprise Platform — Document Schemas (Phase 1.8).

Defines Pydantic v2 schemas for document upload, listing, details, download,
preview, metadata patching, versioning, and archiving.
Specification: devdocs/p1/p1.8.txt & docs/api/api-contract.md Section 3.3
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentUploadResponse(BaseModel):
    """Payload returned immediately when document is accepted for ingestion."""

    document_id: UUID = Field(..., description="Document identifier")
    filename: str = Field(..., description="Sanitized storage filename")
    original_filename: str = Field(
        default="", description="Original filename uploaded by client"
    )
    file_type: str = Field(
        default="application/octet-stream", description="MIME content type"
    )
    file_size: int = Field(..., description="File size in bytes")
    checksum_sha256: str = Field(default="", description="SHA-256 cryptographic digest")
    category: str = Field(default="REPORTS", description="Document enterprise category")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    version_number: int = Field(default=1, description="Initial version number")
    status: str = Field(default="PROCESSING", description="Current ingestion state")
    ai_ready: bool = Field(
        default=False, description="Whether document is indexed and ready for AI"
    )
    project_id: UUID | None = Field(
        default=None, description="Associated project container"
    )
    uploader_id: UUID | None = Field(default=None, description="User who uploaded file")
    created_at: datetime = Field(..., description="Upload timestamp")

    model_config = ConfigDict(from_attributes=True)


class DocumentVersionItemResponse(BaseModel):
    """Single revision snapshot in a document's version history."""

    version_number: int = Field(..., description="Version sequence number")
    file_size: int = Field(..., description="Version file size in bytes")
    checksum_sha256: str = Field(..., description="Cryptographic SHA-256 digest")
    uploader_id: UUID = Field(..., description="Uploader user identifier")
    change_notes: str | None = Field(default=None, description="Summary of changes")
    created_at: datetime = Field(..., description="Version creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    """Document catalog item representation for paginated listings."""

    id: UUID = Field(..., description="Document identifier")
    filename: str = Field(..., description="File name")
    title: str | None = Field(default=None, description="Document display title")
    file_type: str = Field(..., description="MIME content type")
    file_size: int = Field(..., description="File size in bytes")
    category: str = Field(default="REPORTS", description="Document category")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    version_number: int = Field(
        default=1, description="Current sequential version number"
    )
    status: str = Field(..., description="Ingestion processing status")
    ai_ready: bool = Field(
        default=False, description="Whether document is ready for AI retrieval"
    )
    chunk_count: int = Field(
        default=0, description="Extracted chunks count in vector store"
    )
    project_id: UUID | None = Field(
        default=None, description="Associated project container"
    )
    uploader_id: UUID | None = Field(
        default=None, description="User who uploaded the document"
    )
    uploader_name: str | None = Field(default=None, description="Full name of uploader")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(
        default=None, description="Last update timestamp"
    )

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(BaseModel):
    """Comprehensive document representation including full metadata and version history."""

    id: UUID = Field(..., description="Document identifier")
    organization_id: UUID = Field(..., description="Organization tenant identifier")
    project_id: UUID | None = Field(
        default=None, description="Associated project container"
    )
    uploader_id: UUID | None = Field(default=None, description="User who uploaded file")
    filename: str = Field(..., description="Sanitized storage filename")
    original_filename: str = Field(
        default="", description="Original filename uploaded by client"
    )
    title: str | None = Field(default=None, description="Document display title")
    description: str | None = Field(
        default=None, description="Document abstract or description"
    )
    file_type: str = Field(..., description="MIME content type")
    file_size: int = Field(..., description="File size in bytes")
    checksum_sha256: str = Field(default="", description="SHA-256 cryptographic digest")
    category: str = Field(default="REPORTS", description="Document category")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    current_version_number: int = Field(
        default=1, description="Active version sequence number"
    )
    status: str = Field(..., description="Ingestion processing status")
    ai_ready: bool = Field(
        default=False, description="Whether document is ready for AI retrieval"
    )
    chunk_count: int = Field(
        default=0, description="Extracted chunks count in vector store"
    )
    metadata_json: dict[str, Any] = Field(
        default_factory=dict, description="Extracted technical and layout metadata"
    )
    versions: list[DocumentVersionItemResponse] = Field(
        default_factory=list, description="Chronological version history"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(
        default=None, description="Last update timestamp"
    )

    model_config = ConfigDict(from_attributes=True)


class DocumentUpdatePayload(BaseModel):
    """Request payload for updating document metadata."""

    title: str | None = Field(
        default=None, max_length=255, description="Updated display title"
    )
    description: str | None = Field(
        default=None, description="Updated document description"
    )
    category: str | None = Field(
        default=None, description="Updated enterprise category"
    )
    tags: list[str] | None = Field(
        default=None, description="Updated categorization tags"
    )
    project_id: UUID | None = Field(
        default=None, description="Updated associated project"
    )


class DocumentUpdateResponse(BaseModel):
    """Response payload returned when document metadata is successfully updated."""

    id: UUID = Field(..., description="Document identifier")
    title: str | None = Field(default=None, description="Updated display title")
    category: str = Field(..., description="Updated enterprise category")
    tags: list[str] = Field(default_factory=list, description="Updated tags")
    updated_at: datetime = Field(..., description="Timestamp of modification")

    model_config = ConfigDict(from_attributes=True)


class DocumentVersionUploadResponse(BaseModel):
    """Response payload returned when a new document version is uploaded."""

    document_id: UUID = Field(..., description="Parent document identifier")
    version_number: int = Field(..., description="New version sequence number")
    filename: str = Field(..., description="Sanitized filename of revision")
    file_size: int = Field(..., description="Revision file size in bytes")
    checksum_sha256: str = Field(..., description="SHA-256 digest of revision")
    change_notes: str | None = Field(
        default=None, description="Change notes for revision"
    )
    status: str = Field(
        default="AWAITING_PROCESSING", description="Processing state for new version"
    )
    created_at: datetime = Field(..., description="Revision creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class DocumentDeleteResponse(BaseModel):
    """Response payload for document deletion or archiving."""

    id: UUID = Field(..., description="Document identifier")
    deleted: bool = Field(default=True, description="Deletion status flag")
    is_deleted: bool = Field(default=True, description="Soft delete flag")
    deleted_at: datetime | None = Field(default=None, description="Deletion timestamp")
    status: str | None = Field(default=None, description="Updated status if archived")
