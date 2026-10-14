"""KEEP Enterprise Platform — Organizational Activity Feed Endpoints (`/api/v1/activity`).

Serves chronological tenant activity events with actor metadata and pagination.
Derived from devdocs/p1/p1.7.txt and docs/API/api-contract.md Section 5.2.
"""

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
)
from backend.app.api.dependencies.database import get_db
from backend.app.schemas.dashboard import ActivityEventResponse
from backend.app.schemas.envelope import ApiResponse, PaginatedData
from backend.app.services.dashboard_service import DashboardService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/activity", tags=["Activity"])
dashboard_service = DashboardService()


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[ActivityEventResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get recent organizational activity feed",
    description="Returns a paginated, chronological feed of organizational activity events visible to the authenticated user.",
)
async def get_activity_feed(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=50, description="Items per page (max 50)"),
    filter_type: str = Query(
        default="all",
        alias="filter",
        description="Filter by resource type: all, document, project, meeting, user, ai_summary",
    ),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedData[ActivityEventResponse]]:
    """Retrieves paginated organizational activity feed."""
    activity_data = await dashboard_service.get_activity_feed(
        db=db,
        current_user=current_user,
        filter_type=filter_type,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(
        success=True,
        message="Activity feed retrieved successfully.",
        data=activity_data,
    )
