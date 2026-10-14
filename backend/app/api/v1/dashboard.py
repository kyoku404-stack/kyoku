"""KEEP Enterprise Platform — Dashboard Summary Endpoints (`/api/v1/dashboard`).

Serves personalized user dashboard summary, organization profile, and KPI metrics.
Derived from devdocs/p1/p1.7.txt and docs/API/api-contract.md Section 5.1.
"""

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
)
from backend.app.api.dependencies.database import get_db
from backend.app.schemas.dashboard import DashboardSummaryResponse
from backend.app.schemas.envelope import ApiResponse
from backend.app.services.dashboard_service import DashboardService
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
dashboard_service = DashboardService()


@router.get(
    "",
    response_model=ApiResponse[DashboardSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get personalized dashboard summary",
    description="Returns authenticated user profile, organization metadata, greeting, and live KPI counters.",
)
async def get_dashboard(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DashboardSummaryResponse]:
    """Retrieves or computes dashboard summary with 60s Redis caching."""
    summary = await dashboard_service.get_dashboard_summary(
        db=db,
        current_user=current_user,
    )
    return ApiResponse(
        success=True,
        message="Dashboard summary retrieved successfully.",
        data=summary,
    )
