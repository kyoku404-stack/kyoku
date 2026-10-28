"""KEEP Enterprise Platform — Notification Endpoints (`/api/v1/notifications`).

Serves user-scoped notification inbox, single read acknowledgement, and batch read updates.
Derived from devdocs/p1/p1.7.txt and docs/API/api-contract.md Section 5.5.
"""

from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
)
from backend.app.api.dependencies.database import get_db
from backend.app.schemas.dashboard import (
    NotificationReadAllResponse,
    NotificationResponse,
)
from backend.app.schemas.envelope import ApiResponse, PaginatedData
from backend.app.schemas.workflow import (
    NotificationPreferenceItem,
    NotificationPreferencesUpdateRequest,
)
from backend.app.services.notification_service import NotificationService
from backend.app.services.workflow.service import EnterpriseWorkflowService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/notifications", tags=["Notifications"])
notification_service = NotificationService()


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[NotificationResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get user notifications",
    description="Returns the authenticated user's notifications, ordered by created_at descending.",
)
async def get_notifications(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=50, description="Items per page (max 50)"),
    unread_only: bool = Query(default=False, description="When true, returns only unread notifications"),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedData[NotificationResponse]]:
    """Retrieves paginated notifications for current user."""
    data = await notification_service.list_notifications(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
    )
    return ApiResponse(
        success=True,
        message="Notifications retrieved successfully.",
        data=data,
    )


@router.patch(
    "/{id}/read",
    response_model=ApiResponse[NotificationResponse],
    status_code=status.HTTP_200_OK,
    summary="Mark notification as read",
    description="Marks a single notification as read for the authenticated user.",
)
async def mark_notification_read(
    id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[NotificationResponse]:
    """Marks a single notification as read."""
    notification = await notification_service.mark_as_read(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        notification_id=id,
    )
    return ApiResponse(
        success=True,
        message="Notification marked as read.",
        data=notification,
    )


@router.post(
    "/read-all",
    response_model=ApiResponse[NotificationReadAllResponse],
    status_code=status.HTTP_200_OK,
    summary="Mark all notifications as read",
    description="Marks all unread notifications as read for the authenticated user.",
)
async def mark_all_notifications_read(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[NotificationReadAllResponse]:
    """Marks all user notifications as read in bulk."""
    res = await notification_service.mark_all_as_read(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="All notifications marked as read.",
        data=res,
    )


@router.post(
    "/{id}/read",
    response_model=ApiResponse[NotificationResponse],
    status_code=status.HTTP_200_OK,
    summary="Mark notification as read (POST)",
    description="Marks a single notification as read for the authenticated user via POST.",
)
async def mark_notification_read_post(
    id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[NotificationResponse]:
    """Marks single notification as read via POST."""
    notification = await notification_service.mark_as_read(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        notification_id=id,
    )
    return ApiResponse(
        success=True,
        message="Notification marked as read.",
        data=notification,
    )


@router.get(
    "/preferences",
    response_model=ApiResponse[list[NotificationPreferenceItem]],
    status_code=status.HTTP_200_OK,
    summary="Get notification preferences",
    description="Retrieves the current user's multi-channel notification preferences.",
)
async def get_notification_preferences(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[NotificationPreferenceItem]]:
    """Retrieves user notification channel preferences."""
    prefs = await EnterpriseWorkflowService.get_notification_preferences(
        db=db,
        user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Notification preferences retrieved successfully.",
        data=prefs,
    )


@router.post(
    "/preferences",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Update notification preferences",
    description="Updates the user's multi-channel notification opt-in/opt-out preferences.",
)
async def update_notification_preferences(
    payload: NotificationPreferencesUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    """Updates user notification preferences."""
    await EnterpriseWorkflowService.update_notification_preferences(
        db=db,
        user_id=current_user.id,
        preferences=payload.preferences,
    )
    return ApiResponse(
        success=True,
        message="Notification preferences updated successfully.",
        data={"updated": True},
    )

