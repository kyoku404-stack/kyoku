"""KEEP Enterprise Platform — Team Schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeamCreate(BaseModel):
    """Payload to create a new team."""

    name: str = Field(..., min_length=2, max_length=255, description="Team name")
    department_id: UUID | None = Field(default=None, description="Parent department ID")
    lead_user_id: UUID | None = Field(default=None, description="Assigned team lead user ID")
    description: str | None = Field(default=None, max_length=2000, description="Team description")


class TeamUpdate(BaseModel):
    """Payload to update an existing team."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    department_id: UUID | None = Field(default=None)
    lead_user_id: UUID | None = Field(default=None)
    description: str | None = Field(default=None, max_length=2000)


class TeamResponse(BaseModel):
    """Team entity representation."""

    id: UUID = Field(..., description="Team unique ID")
    organization_id: UUID = Field(..., description="Parent organization ID")
    department_id: UUID | None = Field(default=None, description="Parent department ID")
    lead_user_id: UUID | None = Field(default=None, description="Team lead user ID")
    name: str = Field(..., description="Team name")
    description: str | None = Field(default=None)
    member_count: int = Field(default=0, description="Count of members in team")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Update timestamp")

    model_config = ConfigDict(from_attributes=True)
