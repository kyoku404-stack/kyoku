"""KEEP Enterprise Platform — Audit & Activity Log Schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    """Schema representing an immutable audit log record."""

    id: UUID = Field(..., description="Unique audit event identifier")
    organization_id: UUID = Field(..., description="Organization tenant boundary ID")
    user_id: UUID | None = Field(default=None, description="Acting user ID if authenticated")
    action: str = Field(..., description="Audited event action (e.g. PERMISSION_GRANTED, PERMISSION_DENIED)")
    resource_type: str | None = Field(default=None, description="Resource domain type if applicable")
    resource_id: UUID | None = Field(default=None, description="Target resource ID if applicable")
    details: str | None = Field(default=None, description="Structured event context and evaluation details")
    ip_address: str | None = Field(default=None, description="Caller client IP address")
    created_at: datetime = Field(..., description="Audit event UTC creation timestamp")
    updated_at: datetime = Field(..., description="Record timestamp")

    model_config = ConfigDict(from_attributes=True)
