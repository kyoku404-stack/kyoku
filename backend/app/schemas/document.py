"""KEEP Enterprise Platform — Document Schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from backend.app.core.constants import DocumentStatus


class DocumentUploadResponse(BaseModel):
    """Payload returned immediately when document is accepted for ingestion."""

    document_id: UUID = Field(..., description="Document identifier")
    filename: str = Field(..., description="Original filename")
    status: DocumentStatus = Field(default=DocumentStatus.PROCESSING, description="Current ingestion state")
    file_size: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(..., description="Upload timestamp")


class DocumentResponse(BaseModel):
    """Document metadata item representation."""

    id: UUID = Field(..., description="Document ID")
    filename: str = Field(..., description="File name")
    file_type: str = Field(..., description="MIME content type")
    file_size: int = Field(..., description="File size in bytes")
    status: DocumentStatus = Field(..., description="Ingestion processing status")
    chunk_count: int = Field(default=0, description="Extracted chunks count")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)
