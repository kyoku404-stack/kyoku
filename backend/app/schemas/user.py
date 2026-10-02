"""KEEP Enterprise Platform — User Schemas."""

from datetime import datetime
from uuid import UUID

from backend.app.core.constants import UserRole
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Payload to provision a new user."""

    email: EmailStr = Field(..., description="Corporate email address")
    password: str = Field(..., min_length=8, description="Initial password")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")
    role: UserRole = Field(default=UserRole.MEMBER, description="Assigned role")
    organization_id: UUID = Field(..., description="Organization identifier")


class UserUpdate(BaseModel):
    """Payload to modify an existing user."""

    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    role: UserRole | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class UserProfileResponse(BaseModel):
    """Detailed user profile response."""

    id: UUID = Field(..., description="Unique user ID")
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., description="User full display name")
    role: UserRole = Field(..., description="User organization role")
    organization_id: UUID = Field(..., description="Associated organization ID")
    is_active: bool = Field(default=True, description="Account active status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime | None = Field(
        default=None, description="Last update timestamp"
    )

    model_config = ConfigDict(from_attributes=True)
