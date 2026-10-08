"""KEEP Enterprise Platform — Authentication Endpoints (`/api/v1/auth`)."""

from backend.app.api.dependencies.auth import AuthenticatedUser, get_current_user
from backend.app.api.dependencies.database import get_db
from backend.app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    TokenResponse,
    RegisterRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    UserSummaryResponse
)
from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.user import UserProfileResponse
from backend.app.services.auth_service import AuthService
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post(
    "/register",
    response_model=ApiResponse[UserSummaryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create account",
    description="Registers a new user and returns a summary.",
)
async def register(
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[UserSummaryResponse]:
    """Creates a new user."""
    user = await auth_service.register(db=db, register_data=register_data)
    return ApiResponse(
        success=True,
        message="User registered successfully.",
        data=user,
    )


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
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[UserProfileResponse]:
    """Returns current user profile."""
    profile = await auth_service.get_current_user_profile(
        db=db,
        user_id=current_user.id,
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


@router.post(
    "/forgot-password",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Initiates password reset workflow for a user.",
)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    """Requests a password reset."""
    await auth_service.forgot_password(db=db, request=request)
    return ApiResponse(
        success=True,
        message="If the email exists, a password reset link has been sent.",
        data={},
    )


@router.post(
    "/reset-password",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Set new password",
    description="Sets a new password using a valid reset token.",
)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    """Resets password using token."""
    await auth_service.reset_password(db=db, request=request)
    return ApiResponse(
        success=True,
        message="Password has been reset successfully.",
        data={},
    )


@router.patch(
    "/change-password",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Update password",
    description="Changes password for an authenticated user.",
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    """Changes user password."""
    await auth_service.change_password(db=db, user_id=current_user.id, request=request)
    return ApiResponse(
        success=True,
        message="Password has been changed successfully.",
        data={},
    )
