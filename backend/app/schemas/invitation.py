"""KEEP Enterprise Platform — User Invitation Schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class InvitationCreate(BaseModel):
    """Payload to dispatch an invitation."""

    email: EmailStr = Field(..., description="Invitee destination email")
    role: str = Field(default="Member", description="Assigned role: OrgAdmin, ProjectManager, Member, Viewer")
    department_id: UUID | None = Field(default=None, description="Pre-assigned department")
    team_id: UUID | None = Field(default=None, description="Pre-assigned team")


class InvitationAccept(BaseModel):
    """Payload to accept an invitation and activate account."""

    token: str = Field(..., min_length=10, description="One-time invitation token")
    full_name: str = Field(..., min_length=2, max_length=255, description="User full legal name")
    password: str = Field(..., min_length=8, max_length=128, description="Account password")


class InvitationResponse(BaseModel):
    """Invitation record representation."""

    id: UUID = Field(..., description="Invitation unique ID")
    organization_id: UUID = Field(..., description="Organization tenant boundary")
    department_id: UUID | None = Field(default=None)
    team_id: UUID | None = Field(default=None)
    email: str = Field(..., description="Invitee email")
    role: str = Field(..., description="Assigned role")
    token: str = Field(..., description="Invitation token")
    status: str = Field(..., description="Invitation status: PENDING, ACCEPTED, REVOKED, EXPIRED")
    invited_by_id: UUID = Field(..., description="Inviting user ID")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    created_at: datetime = Field(..., description="Dispatched timestamp")
    updated_at: datetime | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)
