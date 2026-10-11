"""KEEP Enterprise Platform — User Invitation Endpoints (`/api/v1/invitations`)."""

from typing import Any
from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    require_roles,
)
from backend.app.api.dependencies.database import get_db
from backend.app.core.constants import UserRole
from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.invitation import (
    InvitationAccept,
    InvitationCreate,
    InvitationResponse,
)
from backend.app.services.invitation_service import InvitationService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/invitations", tags=["Invitations"])
invitation_service = InvitationService()


@router.post(
    "",
    response_model=ApiResponse[InvitationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Send invitation",
    description="Dispatches a secure invitation to a new enterprise member.",
)
async def create_invitation(
    payload: InvitationCreate,
    current_user: AuthenticatedUser = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.ORG_ADMIN,
            UserRole.MANAGER,
            UserRole.PROJECT_MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InvitationResponse]:
    """Issues an invitation."""
    invitation = await invitation_service.create_invitation(
        db=db,
        org_id=current_user.organization_id,
        payload=payload,
        caller_user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Invitation sent successfully.",
        data=invitation,
    )


@router.get(
    "",
    response_model=ApiResponse[list[InvitationResponse]],
    status_code=status.HTTP_200_OK,
    summary="List pending invitations",
    description="Returns all pending invitations for the caller's organization.",
)
async def list_invitations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.ORG_ADMIN,
            UserRole.MANAGER,
            UserRole.PROJECT_MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[InvitationResponse]]:
    """Lists pending invitations."""
    invitations = await invitation_service.list_invitations(
        db=db,
        org_id=current_user.organization_id,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        success=True,
        message="Invitations retrieved successfully.",
        data=invitations,
    )


@router.delete(
    "/{id}",
    response_model=ApiResponse[dict[str, bool]],
    status_code=status.HTTP_200_OK,
    summary="Revoke invitation",
    description="Revokes a pending member invitation.",
)
async def revoke_invitation(
    id: UUID,
    current_user: AuthenticatedUser = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.ORG_ADMIN,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict[str, bool]]:
    """Revokes an invitation."""
    await invitation_service.revoke_invitation(
        db=db,
        org_id=current_user.organization_id,
        invitation_id=id,
        caller_user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Invitation revoked successfully.",
        data={"revoked": True},
    )


@router.post(
    "/accept",
    response_model=ApiResponse[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Accept invitation & activate account",
    description="Validates onboarding token and provisions member credentials.",
)
async def accept_invitation(
    payload: InvitationAccept,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    """Accepts invitation publicly with token."""
    result = await invitation_service.accept_invitation(
        db=db,
        payload=payload,
    )
    return ApiResponse(
        success=True,
        message="Invitation accepted and account activated successfully.",
        data=result,
    )
