"""KEEP Enterprise Platform — Security Audit Trail Endpoints (`/api/v1/audit`)."""

import math
from uuid import UUID

from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.api.dependencies.authorization import require_permission
from backend.app.api.dependencies.database import get_db
from backend.app.api.dependencies.tenant import TenantContext, get_tenant_context
from backend.app.schemas.audit import AuditLogResponse
from backend.app.schemas.envelope import ApiResponse, PaginatedData
from backend.app.services.activity_service import ActivityService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/audit", tags=["Audit & Security"])


@router.get(
    "/logs",
    response_model=ApiResponse[PaginatedData[AuditLogResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get security audit log trail",
    description="Retrieves immutable authorization and access audit logs scoped to the active tenant (OrgAdmin only).",
)
async def get_audit_logs(
    user_id: UUID | None = Query(default=None, description="Filter by user ID"),
    action: str | None = Query(default=None, description="Filter by audit action (e.g. PERMISSION_GRANTED, PERMISSION_DENIED)"),
    resource_type: str | None = Query(default=None, description="Filter by resource type"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(require_permission("audit.read")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedData[AuditLogResponse]]:
    """Retrieves paginated audit log events."""
    logs, total = await ActivityService.get_audit_logs(
        db=db,
        organization_id=tenant.organization_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        page=page,
        page_size=page_size,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return ApiResponse(
        success=True,
        message="Audit logs retrieved successfully.",
        data=PaginatedData[AuditLogResponse](
            items=[AuditLogResponse.model_validate(log) for log in logs],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )
