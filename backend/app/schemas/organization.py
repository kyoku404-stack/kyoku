"""KEEP Enterprise Platform — Organization & Tenant Schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    """Payload to create a new tenant organization."""

    name: str = Field(
        ..., min_length=2, max_length=100, description="Organization name"
    )
    domain: str = Field(
        ..., min_length=3, max_length=100, description="Organization primary domain"
    )


class OrganizationUpdate(BaseModel):
    """Payload to update an organization."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    domain: str | None = Field(default=None, min_length=3, max_length=100)
    is_active: bool | None = Field(default=None)


class OrganizationResponse(BaseModel):
    """Tenant organization representation."""

    id: UUID = Field(..., description="Organization unique ID")
    name: str = Field(..., description="Organization display name")
    domain: str = Field(..., description="Corporate domain")
    is_active: bool = Field(default=True, description="Tenant active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Update timestamp")

    model_config = ConfigDict(from_attributes=True)
