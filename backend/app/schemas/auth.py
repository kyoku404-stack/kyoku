"""KEEP Enterprise Platform — Authentication Schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from backend.app.core.constants import UserRole


class LoginRequest(BaseModel):
    """Payload for user login authentication."""

    email: EmailStr = Field(..., description="User corporate email address")
    password: str = Field(..., min_length=8, description="User secret password")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@enterprise.com",
                "password": "SecurePassword123!",
            }
        }
    )


class RefreshTokenRequest(BaseModel):
    """Payload for refreshing an expired access token."""

    refresh_token: str = Field(..., description="Valid JWT refresh token")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOi...",
            }
        }
    )


class UserSummaryResponse(BaseModel):
    """User representation inside auth payloads."""

    id: UUID = Field(..., description="Unique user ID")
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., description="User full display name")
    role: UserRole = Field(..., description="User organization role")
    organization_id: UUID = Field(..., description="Associated organization ID")

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Token payload returned upon successful login."""

    access_token: str = Field(..., description="JWT Bearer access token")
    refresh_token: str | None = Field(default=None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token authorization type")
    expires_in: int = Field(default=3600, description="Access token expiration window in seconds")
    user: UserSummaryResponse = Field(..., description="Authenticated user summary")


class RefreshTokenResponse(BaseModel):
    """Token payload returned upon token refresh."""

    access_token: str = Field(..., description="New JWT Bearer access token")
    token_type: str = Field(default="bearer", description="Token authorization type")
    expires_in: int = Field(default=3600, description="Access token expiration window in seconds")
