"""KEEP Enterprise Platform — Authentication Service.

Handles credential verification, token lifecycle management, and profile resolution.
"""

from datetime import UTC, datetime
from uuid import UUID

from backend.app.core.config import settings
from backend.app.core.constants import ErrorCode, UserRole
from backend.app.core.exceptions import UnauthorizedException, ConflictException, NotFoundException
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from backend.app.models.user import User
from backend.app.models.organization import Organization
from backend.app.repositories.user_repo import UserRepository
from backend.app.repositories.org_repo import OrganizationRepository
from backend.app.schemas.auth import (
    LoginRequest,
    RefreshTokenResponse,
    TokenResponse,
    UserSummaryResponse,
    RegisterRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest
)
from backend.app.schemas.user import UserProfileResponse
from backend.app.services.base import BaseService
from sqlalchemy.ext.asyncio import AsyncSession


class AuthService(BaseService[UserRepository]):
    """Service implementing user authentication and authorization logic."""

    def __init__(self, repository: UserRepository | None = None) -> None:
        super().__init__(repository or UserRepository())
        self.org_repo = OrganizationRepository()

    async def login(
        self,
        db: AsyncSession,
        login_data: LoginRequest,
    ) -> TokenResponse:
        """Authenticates a user and generates JWT access/refresh token pair."""
        user = await self.repository.get_by_email(db, login_data.email)
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise UnauthorizedException(
                message="Invalid email or password.",
                code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            )
        
        if not user.is_active:
            raise UnauthorizedException(
                message="Account suspended.",
                code=ErrorCode.AUTH_ACCOUNT_DISABLED,
            )
            
        user_summary = UserSummaryResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=UserRole(user.role),
            organization_id=user.organization_id,
        )

        claims = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "org_id": str(user.organization_id),
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

    async def register(
        self,
        db: AsyncSession,
        register_data: RegisterRequest,
    ) -> UserSummaryResponse:
        """Registers a new user and optionally a new organization."""
        existing_user = await self.repository.get_by_email(db, register_data.email)
        if existing_user:
            raise ConflictException(
                message="Email already registered.",
                code=ErrorCode.AUTH_EMAIL_EXISTS,
            )
            
        org_id = register_data.organization_id
        if not org_id:
            domain = register_data.email.split("@")[-1]
            org = await self.org_repo.get_by_domain(db, domain)
            if not org:
                org = Organization(
                    name=f"{domain.capitalize()} Org",
                    domain=domain,
                )
                db.add(org)
                await db.flush()
            org_id = org.id
        else:
            org = await self.org_repo.get(db, org_id)
            if not org:
                raise NotFoundException("Organization not found.")
                
        new_user = User(
            email=register_data.email,
            hashed_password=get_password_hash(register_data.password),
            full_name=register_data.full_name,
            role=UserRole.ORG_ADMIN if not register_data.organization_id else UserRole.MEMBER,
            organization_id=org_id,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        return UserSummaryResponse.model_validate(new_user)

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
        db: AsyncSession,
        user_id: UUID,
    ) -> UserProfileResponse:
        """Returns the complete profile of the authenticated user."""
        user = await self.repository.get(db, user_id)
        if not user:
            raise NotFoundException("User not found.")
            
        return UserProfileResponse.model_validate(user)

    async def forgot_password(self, db: AsyncSession, request: ForgotPasswordRequest) -> None:
        """Initiates password reset workflow."""
        user = await self.repository.get_by_email(db, request.email)
        if user:
            pass

    async def reset_password(self, db: AsyncSession, request: ResetPasswordRequest) -> None:
        """Resets password using token."""
        pass

    async def change_password(
        self, 
        db: AsyncSession, 
        user_id: UUID, 
        request: ChangePasswordRequest
    ) -> None:
        """Changes user password."""
        user = await self.repository.get(db, user_id)
        if not user:
            raise NotFoundException("User not found.")
            
        if not verify_password(request.current_password, user.hashed_password):
            raise UnauthorizedException(
                message="Invalid current password.",
                code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            )
            
        user.hashed_password = get_password_hash(request.new_password)
        db.add(user)
        await db.commit()
