"""KEEP Enterprise Platform — Ingestion API Router (Phase 2.1).

Exposes RESTful endpoints for starting document ingestion, polling progress,
listing historical jobs, retrying failures, and querying pipeline metrics.
Specification: docs/api/api-contract.md Section 8 & devdocs/p2/p2.1.txt Chapters 15 & 16
Owner: Member 2 (Backend Lead)
"""

from datetime import UTC, datetime
from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
)
from backend.app.api.dependencies.database import get_db
from backend.app.api.dependencies.tenant import TenantContext, get_tenant_context
from backend.app.core.constants import ErrorCode
from backend.app.core.exceptions import (
    NotFoundException,
    PermissionDeniedException,
)
from backend.app.schemas.envelope import ApiResponse, PaginatedData
from backend.app.schemas.ingestion import (
    IngestionJobListItem,
    IngestionJobStatusResponseData,
    IngestionRetryResponseData,
    IngestionStatisticsResponseData,
    StartIngestionRequest,
    StartIngestionResponseData,
)
from backend.app.services.ai.ingestion import (
    IngestionJobConfig,
)
from backend.app.services.ingestion.service import IngestionService
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])
ingestion_service = IngestionService()


def _verify_ingest_permission(user: AuthenticatedUser) -> None:
    """Validates that user possesses document ingestion authorization."""
    allowed_perms = {
        "document.ingest",
        "document.create",
        "doc:create",
        "document.update",
        "doc:update",
    }
    if not (user.permissions & allowed_perms):
        raise PermissionDeniedException(
            message="User lacks required permission 'document.ingest'.",
            code=ErrorCode.PERMISSION_DENIED,
        )


def _verify_read_permission(user: AuthenticatedUser) -> None:
    """Validates that user possesses document read authorization."""
    allowed_perms = {"document.read", "doc:read", "document.create", "doc:create"}
    if not (user.permissions & allowed_perms):
        raise PermissionDeniedException(
            message="User lacks required permission 'document.read'.",
            code=ErrorCode.PERMISSION_DENIED,
        )


def _verify_analytics_permission(user: AuthenticatedUser) -> None:
    """Validates that user possesses analytics read authorization."""
    allowed_perms = {
        "analytics.read",
        "analytics.view",
        "analytics:read",
        "document.read",
        "doc:read",
    }
    if not (user.permissions & allowed_perms):
        raise PermissionDeniedException(
            message="User lacks required permission 'analytics.read'.",
            code=ErrorCode.PERMISSION_DENIED,
        )


@router.post(
    "/start",
    response_model=ApiResponse[StartIngestionResponseData],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start Document Ingestion",
    description="Initiates asynchronous ingestion pipeline for an uploaded document.",
)
async def start_ingestion(
    payload: StartIngestionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
) -> ApiResponse[StartIngestionResponseData]:
    """Enqueues document ingestion for background text extraction, chunking, and embedding."""
    _verify_ingest_permission(current_user)

    config = IngestionJobConfig(
        document_id=payload.document_id,
        document_version_id=payload.document_version_id or payload.document_id,
        organization_id=tenant_context.organization_id,
        force_ocr=payload.force_ocr,
        chunking_strategy=payload.chunking_strategy,
        target_chunk_size=payload.target_chunk_size,
        chunk_overlap=payload.chunk_overlap,
        embedding_provider=payload.embedding_provider,
        embedding_model=payload.embedding_model,
    )

    progress = await ingestion_service.start_ingestion(
        config, db=db, background_tasks=background_tasks
    )

    data = StartIngestionResponseData(
        job_id=progress.job_id,
        document_id=progress.document_id,
        status=progress.status.value,
        queue_name="ai_ingestion_queue",
        enqueued_at=progress.started_at or datetime.now(UTC),
    )
    return ApiResponse[StartIngestionResponseData](
        success=True,
        message="Document ingestion job enqueued successfully.",
        data=data,
    )


@router.get(
    "/status/{id}",
    response_model=ApiResponse[IngestionJobStatusResponseData],
    status_code=status.HTTP_200_OK,
    summary="Get Ingestion Job Status",
    description="Retrieves real-time pipeline status, active stage, and chunk progress.",
)
async def get_ingestion_status(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
) -> ApiResponse[IngestionJobStatusResponseData]:
    """Queries current progress of an active or finished ingestion run."""
    _verify_read_permission(current_user)

    progress = await ingestion_service.get_status(id, db=db)
    if not progress:
        raise NotFoundException(
            message=f"Ingestion job or document with ID {id} was not found.",
            code="NOT_FOUND",
        )

    data = IngestionJobStatusResponseData(
        job_id=progress.job_id,
        document_id=progress.document_id,
        status=progress.status.value,
        progress_percent=progress.progress_percent,
        current_stage=progress.current_stage,
        total_pages=progress.total_pages,
        processed_pages=progress.processed_pages,
        chunks_generated=progress.chunks_generated,
        embeddings_generated=progress.embeddings_generated,
        ocr_applied=progress.ocr_applied,
        retry_count=progress.retry_count,
        error_message=progress.error_message,
        started_at=progress.started_at,
        completed_at=progress.completed_at,
        duration_seconds=progress.duration_seconds,
    )
    return ApiResponse[IngestionJobStatusResponseData](
        success=True,
        message="Ingestion job status retrieved successfully.",
        data=data,
    )


@router.get(
    "/jobs",
    response_model=ApiResponse[PaginatedData[IngestionJobListItem]],
    status_code=status.HTTP_200_OK,
    summary="List Ingestion Jobs",
    description="Returns a paginated list of ingestion jobs for the tenant.",
)
async def list_ingestion_jobs(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: str | None = Query(default=None, description="Optional status filter"),
    document_id: UUID | None = Query(default=None, description="Optional document filter"),
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
) -> ApiResponse[PaginatedData[IngestionJobListItem]]:
    """Lists historical and active ingestion jobs."""
    _verify_read_permission(current_user)

    raw_items, total = await ingestion_service.list_jobs(
        organization_id=tenant_context.organization_id,
        page=page,
        page_size=page_size,
        status_filter=status,
        document_id=document_id,
        db=db,
    )

    items = [IngestionJobListItem(**item) for item in raw_items]
    total_pages = (total + page_size - 1) // page_size if total else 0

    paginated_data = PaginatedData[IngestionJobListItem](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
    return ApiResponse[PaginatedData[IngestionJobListItem]](
        success=True,
        message="Ingestion jobs retrieved successfully.",
        data=paginated_data,
    )


@router.post(
    "/retry/{id}",
    response_model=ApiResponse[IngestionRetryResponseData],
    status_code=status.HTTP_200_OK,
    summary="Retry Failed Ingestion Job",
    description="Retries a previously failed or dead-lettered ingestion job.",
)
async def retry_ingestion_job(
    id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
) -> ApiResponse[IngestionRetryResponseData]:
    """Re-enqueues a failed job for execution."""
    _verify_ingest_permission(current_user)

    progress = await ingestion_service.retry_job(
        id, db=db, background_tasks=background_tasks
    )

    data = IngestionRetryResponseData(
        job_id=progress.job_id,
        status=progress.status.value,
        retry_count=progress.retry_count,
        enqueued_at=progress.started_at or datetime.now(UTC),
    )
    return ApiResponse[IngestionRetryResponseData](
        success=True,
        message="Ingestion job re-enqueued for retry.",
        data=data,
    )


@router.get(
    "/statistics",
    response_model=ApiResponse[IngestionStatisticsResponseData],
    status_code=status.HTTP_200_OK,
    summary="Get Ingestion Pipeline Statistics",
    description="Returns tenant-wide ingestion throughput, chunk counts, and error rates.",
)
async def get_ingestion_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
) -> ApiResponse[IngestionStatisticsResponseData]:
    """Calculates operational metrics across all ingestion jobs for the tenant."""
    _verify_analytics_permission(current_user)

    stats = await ingestion_service.get_statistics(
        organization_id=tenant_context.organization_id, db=db
    )

    data = IngestionStatisticsResponseData(
        organization_id=stats.organization_id,
        total_jobs=stats.total_jobs,
        completed_jobs=stats.completed_jobs,
        failed_jobs=stats.failed_jobs,
        pending_jobs=stats.pending_jobs,
        total_chunks_indexed=stats.total_chunks_indexed,
        average_duration_seconds=stats.average_duration_seconds,
        average_throughput_pages_per_minute=stats.average_throughput_pages_per_minute,
        ocr_utilization_percent=stats.ocr_utilization_percent,
        retry_success_rate_percent=stats.retry_success_rate_percent,
    )
    return ApiResponse[IngestionStatisticsResponseData](
        success=True,
        message="Ingestion statistics retrieved successfully.",
        data=data,
    )
