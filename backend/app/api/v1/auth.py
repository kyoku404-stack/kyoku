"""KEEP Enterprise Platform — Authentication Endpoints (`/api/v1/auth`)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies.auth import AuthenticatedUser, get_current_user
from backend.app.api.dependencies.database import get_db
from backend.app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    TokenResponse,
)
from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.user import UserProfileResponse
from backend.app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate user & issue tokens",
    description="Authenticates corporate credentials and returns signed JWT access and refresh tokens.",
)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    """Authenticates credentials and returns standard response envelope."""
    token_resp = await auth_service.login(db=db, login_data=login_data)
    return ApiResponse(
        success=True,
        message="Login successful.",
        data=token_resp,
    )


@router.post(
    "/refresh",
    response_model=ApiResponse[RefreshTokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Refresh expired access token",
    description="Validates a refresh token and returns a fresh JWT access token.",
)
async def refresh_token(
    request: RefreshTokenRequest,
) -> ApiResponse[RefreshTokenResponse]:
    """Refreshes access token."""
    new_token = await auth_service.refresh_token(request.refresh_token)
    return ApiResponse(
        success=True,
        message="Token refreshed successfully.",
        data=new_token,
    )


@router.get(
    "/me",
    response_model=ApiResponse[UserProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Returns profile and tenant information for the active authenticated user.",
)
async def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ApiResponse[UserProfileResponse]:
    """Returns current user profile."""
    profile = await auth_service.get_current_user_profile(
        user_id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        org_id=current_user.organization_id,
    )
    return ApiResponse(
        success=True,
        message="User profile retrieved.",
        data=profile,
    )


@router.post(
    "/logout",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Logout user session",
    description="Terminates active session and invalidates client credentials.",
)
async def logout(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ApiResponse[dict]:
    """Logs out user."""
    return ApiResponse(
        success=True,
        message="Logout successful.",
        data={"user_id": str(current_user.id)},
    )
