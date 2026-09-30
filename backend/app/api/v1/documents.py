"""KEEP Enterprise Platform — Document Endpoints (`/api/v1/documents`)."""

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_user,
    require_roles,
)
from backend.app.api.dependencies.database import get_db
from backend.app.api.dependencies.tenant import TenantContext, get_tenant_context
from backend.app.core.constants import DocumentStatus, UserRole
from backend.app.schemas.document import DocumentResponse, DocumentUploadResponse
from backend.app.schemas.envelope import ApiResponse, PaginatedData
from backend.app.services.document_service import DocumentService
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/documents", tags=["Documents"])
doc_service = DocumentService()


@router.post(
    "/upload",
    response_model=ApiResponse[DocumentUploadResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload document for ingestion",
    description="Uploads a corporate document (PDF, DOCX, TXT, PNG, JPG) to trigger asynchronous extraction.",
)
async def upload_document(
    file: UploadFile = File(..., description="Binary document file"),
    title: str | None = Form(default=None, description="Document display title"),
    tags: str | None = Form(default=None, description="Comma-separated categorization tags"),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER, UserRole.MEMBER)
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DocumentUploadResponse]:
    """Receives multipart upload and dispatches ingestion."""
    # Read file size
    contents = await file.read()
    file_size = len(contents)
    filename = file.filename or "uploaded_document"
    content_type = file.content_type or "application/octet-stream"

    upload_result = await doc_service.upload_document(
        db=db,
        filename=filename,
        content_type=content_type,
        file_size=file_size,
        org_id=tenant.organization_id,
        title=title,
        tags=tags,
    )

    return ApiResponse(
        success=True,
        message="Document accepted for asynchronous processing.",
        data=upload_result,
    )


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[DocumentResponse]],
    status_code=status.HTTP_200_OK,
    summary="List tenant documents",
    description="Lists documents ingested into the tenant repository with optional status filter.",
)
async def list_documents(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
    doc_status: DocumentStatus | None = Query(default=None, alias="status", description="Filter by status"),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedData[DocumentResponse]]:
    """Retrieves paginated documents."""
    docs = await doc_service.list_documents(
        db=db,
        org_id=tenant.organization_id,
        page=page,
        page_size=page_size,
        status=doc_status,
    )
    return ApiResponse(
        success=True,
        message="Documents retrieved.",
        data=docs,
    )
