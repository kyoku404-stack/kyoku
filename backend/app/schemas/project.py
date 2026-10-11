"""KEEP Enterprise Platform — Project Schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    """Payload to create a new project workspace."""

    name: str = Field(..., min_length=2, max_length=255, description="Project name")
    team_id: UUID | None = Field(default=None, description="Associated team ID")
    description: str | None = Field(default=None, max_length=2000, description="Project scope")
    priority: str = Field(default="MEDIUM", description="Priority level: LOW, MEDIUM, HIGH, CRITICAL")
    timeline: str | None = Field(default=None, max_length=255)


class ProjectUpdate(BaseModel):
    """Payload to update an existing project."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    team_id: UUID | None = Field(default=None)
    description: str | None = Field(default=None, max_length=2000)
    status: str | None = Field(default=None, description="Status: ACTIVE, ARCHIVED, COMPLETED")
    priority: str | None = Field(default=None)
    timeline: str | None = Field(default=None, max_length=255)


class ProjectResponse(BaseModel):
    """Project workspace entity representation."""

    id: UUID = Field(..., description="Project unique ID")
    organization_id: UUID = Field(..., description="Parent organization ID")
    team_id: UUID | None = Field(default=None, description="Associated team ID")
    owner_id: UUID | None = Field(default=None, description="Project owner user ID")
    name: str = Field(..., description="Project name")
    description: str | None = Field(default=None)
    department: str | None = Field(default=None)
    status: str = Field(default="ACTIVE")
    priority: str = Field(default="MEDIUM")
    timeline: str | None = Field(default=None)
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Update timestamp")

    model_config = ConfigDict(from_attributes=True)
