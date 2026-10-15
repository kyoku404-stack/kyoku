"""KEEP Enterprise Platform — Document Management Router (Phase 1.8).

Exposes RESTful endpoints for enterprise document upload, listing, details,
download streaming, preview rendering, metadata updating, version revisions,
and deletion/archiving conforming strictly to docs/api/api-contract.md Section 3.3.
"""

from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
)
from backend.app.api.dependencies.authorization import (
    audit_authorization,
    get_user_project_ids,
    require_permission,
)
from backend.app.api.dependencies.database import get_db
from backend.app.api.dependencies.tenant import TenantContext, get_tenant_context
from backend.app.schemas.dashboard import DocumentSummaryResponse
from backend.app.schemas.document import (
    DocumentDeleteResponse,
    DocumentDetailResponse,
    DocumentResponse,
    DocumentUpdatePayload,
    DocumentUpdateResponse,
    DocumentUploadResponse,
    DocumentVersionUploadResponse,
)
from backend.app.schemas.envelope import ApiResponse, PaginatedData
from backend.app.services.ai.interfaces import AuthorizationDecision
from backend.app.services.dashboard_service import DashboardService
from backend.app.services.document_service import DocumentService
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/documents", tags=["Documents"])
doc_service = DocumentService()
dashboard_service = DashboardService()


@router.post(
    "/upload",
    response_model=ApiResponse[DocumentUploadResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload document for ingestion",
    description="Uploads a corporate digital asset (PDF, DOCX, TXT, MD, RTF, PPTX, XLSX, CSV, PNG, JPG, WEBP) to trigger asynchronous processing.",
)
async def upload_document(
    file: UploadFile = File(..., description="Binary document file"),
    title: str | None = Form(default=None, description="Document display title"),
    category: str | None = Form(
        default="REPORTS", description="Document enterprise category"
    ),
    tags: str | None = Form(
        default=None, description="Comma-separated categorization tags"
    ),
    project_id: UUID | None = Form(
        default=None, description="Associated project container"
    ),
    description: str | None = Form(
        default=None, description="Document description or abstract"
    ),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(require_permission("document.create")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DocumentUploadResponse]:
    """Receives multipart upload, validates attributes and magic bytes, saves file, and dispatches ingestion."""
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
        uploader_id=current_user.id,
        file_bytes=contents,
        title=title,
        category=category,
        tags=tags,
        project_id=project_id,
        description=description,
    )

    # Emit audit trail
    await audit_authorization(
        db=db,
        caller=current_user,
        action="document.create",
        decision=AuthorizationDecision.allow(
            "Document uploaded and queued for ingestion"
        ),
        resource_type="document",
        resource_id=upload_result.document_id,
    )

    return ApiResponse(
        success=True,
        message="Document uploaded successfully and queued for AI ingestion.",
        data=upload_result,
    )


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[DocumentResponse]],
    status_code=status.HTTP_200_OK,
    summary="List documents",
    description="Lists documents ingested into the tenant repository with optional status, category, project, and search filters.",
)
async def list_documents(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: str | None = Query(
        default=None, description="Filter by lifecycle processing status"
    ),
    category: str | None = Query(
        default=None, description="Filter by document category"
    ),
    file_type: str | None = Query(
        default=None, description="Filter by file extension or type"
    ),
    project_id: UUID | None = Query(
        default=None, description="Filter by project identifier"
    ),
    uploader_id: UUID | None = Query(
        default=None, description="Filter by uploader user ID"
    ),
    search: str | None = Query(
        default=None, description="Search term for title, filename, or original name"
    ),
    sort_by: str = Query(
        default="created_at",
        description="Sort column (created_at, filename, file_size)",
    ),
    sort_order: str = Query(default="desc", description="Sort direction (asc, desc)"),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(require_permission("document.read")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedData[DocumentResponse]]:
    """Retrieves paginated and filtered documents for tenant."""
    docs = await doc_service.list_documents(
        db=db,
        org_id=tenant.organization_id,
        page=page,
        page_size=page_size,
        status=status,
        category=category,
        file_type=file_type,
        project_id=project_id,
        uploader_id=uploader_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return ApiResponse(
        success=True,
        message="Documents retrieved successfully.",
        data=docs,
    )


@router.get(
    "/recent",
    response_model=ApiResponse[list[DocumentSummaryResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get recent documents",
    description="Returns recently accessed or uploaded documents visible to the authenticated user.",
)
async def get_recent_documents(
    limit: int = Query(
        default=8, ge=1, le=20, description="Maximum number of documents (max 20)"
    ),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[DocumentSummaryResponse]]:
    """Retrieves recent documents for user dashboard widget."""
    documents = await dashboard_service.get_recent_documents(
        db=db,
        current_user=current_user,
        limit=limit,
    )
    return ApiResponse(
        success=True,
        message="Recent documents retrieved successfully.",
        data=documents,
    )


@router.get(
    "/{id}",
    response_model=ApiResponse[DocumentDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve document metadata and version history",
    description="Retrieves comprehensive document metadata, technical properties, and chronological version history.",
)
async def get_document_details(
    id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("document.read")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DocumentDetailResponse]:
    """Retrieves document detail enforcing tenant and project scoping."""
    project_ids = await get_user_project_ids(current_user.id, db)
    detail = await doc_service.get_document_detail(
        db=db,
        document_id=id,
        caller=current_user,
        caller_project_ids=project_ids,
    )
    return ApiResponse(
        success=True,
        message="Document metadata retrieved successfully.",
        data=detail,
    )


@router.get(
    "/{id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download document binary stream",
    description="Downloads the binary file stream of the document or a specific version revision.",
)
async def download_document(
    id: UUID,
    version: int | None = Query(
        default=None, description="Optional version number to download"
    ),
    current_user: AuthenticatedUser = Depends(require_permission("document.download")),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Streams binary document file for download."""
    project_ids = await get_user_project_ids(current_user.id, db)
    (
        file_path,
        filename,
        mime_type,
        file_size,
    ) = await doc_service.get_document_for_download(
        db=db,
        document_id=id,
        caller=current_user,
        caller_project_ids=project_ids,
        version=version,
    )

    # Emit audit log
    await audit_authorization(
        db=db,
        caller=current_user,
        action="document.download",
        decision=AuthorizationDecision.allow(
            f"Downloaded document version {version or 'current'}"
        ),
        resource_type="document",
        resource_id=id,
    )

    return FileResponse(
        path=file_path,
        media_type=mime_type,
        filename=filename,
        headers={"Content-Length": str(file_size)},
    )


@router.get(
    "/{id}/preview",
    status_code=status.HTTP_200_OK,
    summary="Preview document",
    description="Streams preview artifact (PDF, image, text, or converted HTML) for inline client viewing.",
)
async def preview_document(
    id: UUID,
    version: int | None = Query(
        default=None, description="Optional version number to preview"
    ),
    format: str | None = Query(
        default=None, description="Optional format override (html, text, thumbnail)"
    ),
    current_user: AuthenticatedUser = Depends(require_permission("document.preview")),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Streams rendered preview content."""
    project_ids = await get_user_project_ids(current_user.id, db)
    content, content_type = await doc_service.get_document_for_preview(
        db=db,
        document_id=id,
        caller=current_user,
        caller_project_ids=project_ids,
        version=version,
        preview_format=format,
    )

    # Emit audit log
    await audit_authorization(
        db=db,
        caller=current_user,
        action="document.preview",
        decision=AuthorizationDecision.allow(f"Previewed document as {content_type}"),
        resource_type="document",
        resource_id=id,
    )

    return Response(content=content, media_type=content_type)


@router.patch(
    "/{id}",
    response_model=ApiResponse[DocumentUpdateResponse],
    status_code=status.HTTP_200_OK,
    summary="Update document metadata",
    description="Updates document display title, description, category, tags, or project association.",
)
async def update_document_metadata(
    id: UUID,
    payload: DocumentUpdatePayload,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DocumentUpdateResponse]:
    """Updates document metadata enforcing resource ownership override."""
    project_ids = await get_user_project_ids(current_user.id, db)
    updated = await doc_service.update_metadata(
        db=db,
        document_id=id,
        payload=payload,
        caller=current_user,
        caller_project_ids=project_ids,
    )

    await audit_authorization(
        db=db,
        caller=current_user,
        action="document.update",
        decision=AuthorizationDecision.allow("Document metadata updated"),
        resource_type="document",
        resource_id=id,
    )

    return ApiResponse(
        success=True,
        message="Document metadata updated successfully.",
        data=updated,
    )


@router.post(
    "/{id}/version",
    response_model=ApiResponse[DocumentVersionUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload new document version",
    description="Uploads a revised file version for an existing document, bumps the version number, and triggers re-indexing.",
)
async def upload_document_version(
    id: UUID,
    file: UploadFile = File(..., description="Revised binary document file"),
    change_notes: str = Form(..., description="Summary of changes in this revision"),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DocumentVersionUploadResponse]:
    """Uploads a new version snapshot enforcing resource ownership override."""
    contents = await file.read()
    file_size = len(contents)
    filename = file.filename or "revised_document"
    content_type = file.content_type or "application/octet-stream"

    project_ids = await get_user_project_ids(current_user.id, db)
    version_res = await doc_service.upload_new_version(
        db=db,
        document_id=id,
        filename=filename,
        content_type=content_type,
        file_size=file_size,
        file_bytes=contents,
        change_notes=change_notes,
        caller=current_user,
        caller_project_ids=project_ids,
    )

    await audit_authorization(
        db=db,
        caller=current_user,
        action="document.version",
        decision=AuthorizationDecision.allow(
            f"Uploaded revision v{version_res.version_number}"
        ),
        resource_type="document",
        resource_id=id,
    )

    return ApiResponse(
        success=True,
        message="New document version uploaded successfully and queued for AI re-indexing.",
        data=version_res,
    )


@router.delete(
    "/{id}",
    response_model=ApiResponse[DocumentDeleteResponse],
    status_code=status.HTTP_200_OK,
    summary="Delete or archive document",
    description="Soft-deletes or archives a document. Requires document.delete permission or document ownership (uploader).",
)
async def delete_document(
    id: UUID,
    action: str = Query(
        default="delete",
        description="Deletion action: 'delete' for soft-delete, 'archive' to archive",
    ),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DocumentDeleteResponse]:
    """Deletes or archives a document enforcing resource-level authorization."""
    project_ids = await get_user_project_ids(current_user.id, db)
    delete_res = await doc_service.delete_document(
        db=db,
        document_id=id,
        caller=current_user,
        caller_project_ids=project_ids,
        action=action,
    )

    # Emit audit log on success
    await audit_authorization(
        db=db,
        caller=current_user,
        action="document.delete",
        decision=AuthorizationDecision.allow(
            f"Document {action}d by authorized principal"
        ),
        resource_type="document",
        resource_id=id,
    )

    action_msg = (
        "Document archived successfully."
        if action.lower() == "archive"
        else "Document deleted successfully."
    )
    return ApiResponse(
        success=True,
        message=action_msg,
        data=delete_res,
    )
