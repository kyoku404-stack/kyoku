"""KEEP Enterprise Platform — Organization & Tenant Schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    """Payload to create a new tenant organization."""

    name: str = Field(..., min_length=2, max_length=255, description="Organization name")
    domain: str = Field(..., min_length=3, max_length=255, description="Organization primary domain")
    industry: str | None = Field(default=None, max_length=100)
    company_size: str | None = Field(default=None, max_length=50)
    time_zone: str | None = Field(default="UTC", max_length=100)
    default_language: str | None = Field(default="en-US", max_length=20)
    logo_url: str | None = Field(default=None, max_length=512)
    description: str | None = Field(default=None, max_length=2000)


class OrganizationUpdate(BaseModel):
    """Payload to update organization settings."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    time_zone: str | None = Field(default=None, max_length=100)
    theme: str | None = Field(default=None, max_length=50)
    default_language: str | None = Field(default=None, max_length=20)
    logo_url: str | None = Field(default=None, max_length=512)
    description: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = Field(default=None)
    settings: dict[str, Any] | None = Field(default=None)


class OrganizationResponse(BaseModel):
    """Tenant organization representation."""

    id: UUID = Field(..., description="Organization unique ID")
    name: str = Field(..., description="Organization display name")
    domain: str | None = Field(default=None, description="Corporate domain")
    industry: str | None = Field(default=None)
    company_size: str | None = Field(default=None)
    time_zone: str | None = Field(default="UTC")
    default_language: str | None = Field(default="en-US")
    logo_url: str | None = Field(default=None)
    description: str | None = Field(default=None)
    is_active: bool = Field(default=True, description="Tenant active status")
    settings: dict[str, Any] | None = Field(default=None)
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Update timestamp")

    model_config = ConfigDict(from_attributes=True)
