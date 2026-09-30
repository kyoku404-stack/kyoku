"""KEEP Enterprise Platform — Authentication & Authorization Dependencies."""

from collections.abc import Callable
from typing import Any
from uuid import UUID
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from backend.app.core.config import settings
from backend.app.core.constants import ErrorCode, UserRole
from backend.app.core.exceptions import ForbiddenException, UnauthorizedException
from backend.app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False,
)


class AuthenticatedUser:
    """Lightweight representation of the authenticated JWT principal."""

    def __init__(
        self,
        user_id: UUID,
        email: str,
        role: UserRole,
        organization_id: UUID,
        is_active: bool = True,
    ) -> None:
        self.id = user_id
        self.email = email
        self.role = role
        self.organization_id = organization_id
        self.is_active = is_active


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
) -> AuthenticatedUser:
    """Validates the Bearer JWT token and returns the current user identity."""
    if not token:
        raise UnauthorizedException(
            message="Missing authentication token in request headers.",
            code=ErrorCode.AUTH_UNAUTHORIZED,
        )

    payload = decode_token(token)
    user_id_str = payload.get("sub") or payload.get("user_id")
    email = payload.get("email")
    role_str = payload.get("role", UserRole.MEMBER)
    org_id_str = payload.get("org_id") or payload.get("organization_id")

    if not user_id_str or not email:
        raise UnauthorizedException(
            message="Token payload is missing required subject claims.",
            code=ErrorCode.AUTH_TOKEN_INVALID,
        )

    try:
        user_id = UUID(str(user_id_str))
        organization_id = UUID(str(org_id_str)) if org_id_str else UUID("00000000-0000-0000-0000-000000000000")
        role = UserRole(str(role_str))
    except (ValueError, TypeError) as exc:
        raise UnauthorizedException(
            message="Invalid identifier formats in token claims.",
            code=ErrorCode.AUTH_TOKEN_INVALID,
        ) from exc

    return AuthenticatedUser(
        user_id=user_id,
        email=email,
        role=role,
        organization_id=organization_id,
        is_active=payload.get("is_active", True),
    )


async def get_current_active_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Verifies that the current user account is active."""
    if not current_user.is_active:
        raise ForbiddenException(
            message="User account is deactivated.",
            code=ErrorCode.AUTH_FORBIDDEN,
        )
    return current_user


def require_roles(*allowed_roles: UserRole) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    """Dependency factory enforcing Role-Based Access Control (RBAC)."""

    async def role_checker(
        current_user: AuthenticatedUser = Depends(get_current_active_user),
    ) -> AuthenticatedUser:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(
                message=f"Operation requires one of the following roles: {[r.value for r in allowed_roles]}.",
                code=ErrorCode.AUTH_FORBIDDEN,
            )
        return current_user

    return role_checker
