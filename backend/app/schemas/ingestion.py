"""KEEP Enterprise Platform — Ingestion API Schemas (Phase 2.1).

Defines Pydantic request and response models for document ingestion endpoints.
Specification: docs/api/api-contract.md Section 8 & devdocs/p2/p2.1.txt Chapter 16
Owner: Member 2 (Backend Lead)
"""

from datetime import datetime
from uuid import UUID

from backend.app.services.ai.ingestion import (
    ChunkingStrategy,
    EmbeddingModelProvider,
)
from pydantic import BaseModel, ConfigDict, Field


class StartIngestionRequest(BaseModel):
    """Payload to trigger asynchronous document ingestion."""

    document_id: UUID = Field(..., description="Target document UUID")
    document_version_id: UUID | None = Field(
        default=None, description="Specific document version to process"
    )
    force_ocr: bool = Field(
        default=False, description="Force optical character recognition on text pages"
    )
    chunking_strategy: ChunkingStrategy = Field(
        default=ChunkingStrategy.SEMANTIC_HEADING_AWARE,
        description="Chunking segmentation strategy",
    )
    target_chunk_size: int = Field(
        default=512, ge=64, le=4096, description="Target chunk size in tokens"
    )
    chunk_overlap: int = Field(
        default=50, ge=0, le=512, description="Sliding window token overlap"
    )
    embedding_provider: EmbeddingModelProvider = Field(
        default=EmbeddingModelProvider.OPENAI,
        description="Embedding model provider",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Model identifier for vector representation",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "document_version_id": "4fa85f64-5717-4562-b3fc-2c963f66afa7",
                "force_ocr": False,
                "chunking_strategy": "SEMANTIC_HEADING_AWARE",
                "target_chunk_size": 512,
                "chunk_overlap": 50,
                "embedding_provider": "OPENAI",
                "embedding_model": "text-embedding-3-small",
            }
        }
    )


class StartIngestionResponseData(BaseModel):
    """Payload returned when an ingestion job is enqueued."""

    job_id: UUID = Field(..., description="Unique ingestion job identifier")
    document_id: UUID = Field(..., description="Target document identifier")
    status: str = Field(..., description="Initial ingestion state (PENDING)")
    queue_name: str = Field(
        default="ai_ingestion_queue", description="Target background processing queue"
    )
    enqueued_at: datetime = Field(..., description="Timestamp job was enqueued")


class IngestionJobStatusResponseData(BaseModel):
    """Real-time pipeline monitoring and metric payload."""

    job_id: UUID = Field(..., description="Ingestion job identifier")
    document_id: UUID = Field(..., description="Target document identifier")
    status: str = Field(..., description="Active pipeline status")
    progress_percent: float = Field(..., description="Execution completion percentage (0-100)")
    current_stage: str = Field(..., description="Current executing pipeline stage")
    total_pages: int = Field(default=0, description="Total document pages")
    processed_pages: int = Field(default=0, description="Pages parsed and processed")
    chunks_generated: int = Field(default=0, description="Number of semantic chunks produced")
    embeddings_generated: int = Field(default=0, description="Number of vector embeddings created")
    ocr_applied: bool = Field(default=False, description="Indicates if OCR processing occurred")
    retry_count: int = Field(default=0, description="Number of retry attempts executed")
    error_message: str | None = Field(default=None, description="Diagnostic error explanation")
    started_at: datetime | None = Field(default=None, description="Timestamp processing began")
    completed_at: datetime | None = Field(default=None, description="Timestamp processing finished")
    duration_seconds: float = Field(default=0.0, description="Total processing wall-clock time in seconds")


class IngestionJobListItem(BaseModel):
    """Summary item for paginated ingestion jobs listing."""

    job_id: UUID = Field(..., description="Ingestion job identifier")
    document_id: UUID = Field(..., description="Associated document identifier")
    document_title: str = Field(..., description="Document display title or filename")
    status: str = Field(..., description="Job lifecycle status")
    chunks_generated: int = Field(default=0, description="Total chunks indexed")
    duration_seconds: float = Field(default=0.0, description="Processing duration in seconds")
    created_at: datetime = Field(..., description="Timestamp job was created")
    completed_at: datetime | None = Field(default=None, description="Timestamp job completed")


class IngestionRetryResponseData(BaseModel):
    """Payload returned when retrying a failed job."""

    job_id: UUID = Field(..., description="Retried job identifier")
    status: str = Field(..., description="New job status (RETRYING)")
    retry_count: int = Field(..., description="Incremented retry attempt count")
    enqueued_at: datetime = Field(..., description="Timestamp re-enqueued")


class IngestionStatisticsResponseData(BaseModel):
    """Tenant-wide operational ingestion metrics."""

    organization_id: UUID = Field(..., description="Tenant organization UUID")
    total_jobs: int = Field(default=0, description="Total jobs recorded for tenant")
    completed_jobs: int = Field(default=0, description="Successfully completed jobs")
    failed_jobs: int = Field(default=0, description="Failed jobs requiring intervention")
    pending_jobs: int = Field(default=0, description="Active or waiting jobs in queue")
    total_chunks_indexed: int = Field(default=0, description="Total vector chunks in database")
    average_duration_seconds: float = Field(default=0.0, description="Mean job completion duration")
    average_throughput_pages_per_minute: float = Field(
        default=0.0, description="Throughput velocity in pages per minute"
    )
    ocr_utilization_percent: float = Field(
        default=0.0, description="Percentage of jobs that leveraged OCR"
    )
    retry_success_rate_percent: float = Field(
        default=100.0, description="Successful recovery rate for retried jobs"
    )
