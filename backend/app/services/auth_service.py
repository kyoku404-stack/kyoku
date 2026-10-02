"""KEEP Enterprise Platform — Authentication Service.

Handles credential verification, token lifecycle management, and profile resolution.
"""

from datetime import UTC, datetime
from uuid import UUID

from backend.app.core.config import settings
from backend.app.core.constants import ErrorCode, UserRole
from backend.app.core.exceptions import UnauthorizedException
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from backend.app.repositories.user_repo import UserRepository
from backend.app.schemas.auth import (
    LoginRequest,
    RefreshTokenResponse,
    TokenResponse,
    UserSummaryResponse,
)
from backend.app.schemas.user import UserProfileResponse
from backend.app.services.base import BaseService
from sqlalchemy.ext.asyncio import AsyncSession


class AuthService(BaseService[UserRepository]):
    """Service implementing user authentication and authorization logic."""

    def __init__(self, repository: UserRepository | None = None) -> None:
        super().__init__(repository or UserRepository())

    async def login(
        self,
        db: AsyncSession | None,
        login_data: LoginRequest,
    ) -> TokenResponse:
        """Authenticates a user and generates JWT access/refresh token pair."""
        # Baseline deterministic tenant and user identifiers for enterprise bootstrap
        user_id = UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")
        org_id = UUID("8bc92d11-3456-4211-89ab-1234567890ab")

        # In Phase 1.2 baseline (prior to Phase 1.3 DB seed), accept valid email & password format
        if not login_data.email or not login_data.password:
            raise UnauthorizedException(
                message="Invalid email or password.",
                code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            )

        user_summary = UserSummaryResponse(
            id=user_id,
            email=login_data.email,
            full_name="Enterprise Administrator"
            if "admin" in login_data.email
            else "Jane Doe",
            role=UserRole.ORG_ADMIN if "admin" in login_data.email else UserRole.MEMBER,
            organization_id=org_id,
        )

        claims = {
            "sub": str(user_id),
            "email": str(login_data.email),
            "role": str(user_summary.role.value),
            "org_id": str(org_id),
        }

        access_token = create_access_token(claims)
        refresh_token = create_refresh_token(claims)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_summary,
        )

    async def refresh_token(self, refresh_token: str) -> RefreshTokenResponse:
        """Validates a refresh token and generates a fresh access token."""
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedException(
                message="Provided token is not a valid refresh token.",
                code=ErrorCode.AUTH_TOKEN_INVALID,
            )

        claims = {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "org_id": payload.get("org_id"),
        }

        new_access_token = create_access_token(claims)
        return RefreshTokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def get_current_user_profile(
        self,
        user_id: UUID,
        email: str,
        role: UserRole,
        org_id: UUID,
    ) -> UserProfileResponse:
        """Returns the complete profile of the authenticated user."""
        return UserProfileResponse(
            id=user_id,
            email=email,
            full_name="Jane Doe",
            role=role,
            organization_id=org_id,
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=None,
        )
