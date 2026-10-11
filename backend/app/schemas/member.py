"""KEEP Enterprise Platform — Member Management Schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MemberResponse(BaseModel):
    """Organization member representation."""

    id: UUID = Field(..., description="User unique identifier")
    organization_id: UUID = Field(..., description="Organization tenant boundary")
    email: str = Field(..., description="User email")
    full_name: str = Field(..., description="Full name")
    role: str = Field(..., description="RBAC role")
    department_id: UUID | None = Field(default=None, description="Department assignment")
    team_id: UUID | None = Field(default=None, description="Team assignment")
    is_active: bool = Field(default=True, description="Account active status")
    created_at: datetime = Field(..., description="Join timestamp")

    model_config = ConfigDict(from_attributes=True)


class MemberUpdate(BaseModel):
    """Payload to update member role, assignment, or status."""

    role: str | None = Field(default=None, description="Updated RBAC role")
    department_id: UUID | None = Field(default=None, description="Updated department")
    team_id: UUID | None = Field(default=None, description="Updated team")
    is_active: bool | None = Field(default=None, description="Updated active status")
