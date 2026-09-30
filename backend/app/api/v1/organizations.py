"""KEEP Enterprise Platform — Organization Endpoints (`/api/v1/organizations`)."""

from backend.app.api.dependencies.auth import AuthenticatedUser, get_current_user
from backend.app.api.dependencies.database import get_db
from backend.app.api.dependencies.tenant import TenantContext, get_tenant_context
from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.organization import OrganizationResponse
from backend.app.services.org_service import OrganizationService
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/organizations", tags=["Organizations"])
org_service = OrganizationService()


@router.get(
    "/current",
    response_model=ApiResponse[OrganizationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current organization details",
    description="Returns organization details for the active tenant boundary.",
)
async def get_current_organization(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[OrganizationResponse]:
    """Retrieves the organization matching the tenant JWT context."""
    org = await org_service.get_current_organization(
        db=db,
        org_id=tenant.organization_id,
    )
    return ApiResponse(
        success=True,
        message="Organization details retrieved.",
        data=org,
    )
