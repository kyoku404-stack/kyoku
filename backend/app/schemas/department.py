"""KEEP Enterprise Platform — Department Schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    """Payload to create a new department."""

    name: str = Field(..., min_length=2, max_length=255, description="Department name")
    description: str | None = Field(default=None, max_length=2000, description="Department description")
    manager_id: UUID | None = Field(default=None, description="Assigned manager user ID")


class DepartmentUpdate(BaseModel):
    """Payload to update an existing department."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    manager_id: UUID | None = Field(default=None)


class DepartmentResponse(BaseModel):
    """Department entity representation."""

    id: UUID = Field(..., description="Department unique ID")
    organization_id: UUID = Field(..., description="Parent organization ID")
    name: str = Field(..., description="Department name")
    description: str | None = Field(default=None)
    manager_id: UUID | None = Field(default=None)
    team_count: int = Field(default=0, description="Count of teams in department")
    member_count: int = Field(default=0, description="Count of members in department")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Update timestamp")

    model_config = ConfigDict(from_attributes=True)
