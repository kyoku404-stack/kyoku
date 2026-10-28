"""KEEP Enterprise Platform — Connector Framework & Enterprise Integrations Pydantic v2 Schemas.

Specification: devdocs/p3/p3.1.txt Section 15 & docs/api/api-contract.md Section 13
Author: Member 2 (Backend & Database Lead)
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConnectorRegisterRequest(BaseModel):
    """Payload to register a new external connector."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=255, description="Display name for connector")
    platform_type: str = Field(..., description="Platform identifier (e.g. GOOGLE_DRIVE, GITHUB, SLACK)")
    platform_category: str = Field(..., description="Category (CLOUD_STORAGE, DOCUMENTATION, COMMUNICATION, etc.)")
    auth_type: str = Field(..., description="Authentication method (OAUTH2, PERSONAL_ACCESS_TOKEN, API_KEY, etc.)")
    config: dict[str, Any] = Field(default_factory=dict, description="Platform sync settings")


class ConnectorRegisterResponse(BaseModel):
    """Response returned upon successful connector registration."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    platform_type: str
    platform_category: str
    auth_type: str
    status: str
    config: dict[str, Any]
    total_documents_synced: int
    created_at: datetime


class ConnectorAuthenticateRequest(BaseModel):
    """Payload to authenticate an external connector instance."""

    model_config = ConfigDict(from_attributes=True)

    connector_id: uuid.UUID
    auth_type: str
    credentials: dict[str, Any] = Field(..., description="Token, API key, or OAuth payload")


class ConnectorAuthenticateResponse(BaseModel):
    """Response returned upon successful connector authentication."""

    model_config = ConfigDict(from_attributes=True)

    connector_id: uuid.UUID
    status: str
    authenticated_at: datetime


class ConnectorListItem(BaseModel):
    """Summary item in connector listing."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    platform_type: str
    platform_category: str
    auth_type: str
    status: str
    total_documents_synced: int
    last_sync_at: datetime | None = None
    last_sync_status: str | None = None
    created_at: datetime


class ConnectorListResponse(BaseModel):
    """Response containing list of registered connectors."""

    model_config = ConfigDict(from_attributes=True)

    total_connectors: int
    connectors: list[ConnectorListItem]


class ConnectorSyncRequest(BaseModel):
    """Payload to trigger connector synchronization."""

    model_config = ConfigDict(from_attributes=True)

    connector_id: uuid.UUID
    sync_mode: str = Field(default="INCREMENTAL", description="FULL, INCREMENTAL, SCHEDULED, or REAL_TIME")


class ConnectorSyncResponse(BaseModel):
    """Response returned when a sync job is scheduled or started."""

    model_config = ConfigDict(from_attributes=True)

    sync_job_id: uuid.UUID
    connector_id: uuid.UUID
    sync_mode: str
    status: str
    started_at: datetime


class ConnectorHealthMetrics(BaseModel):
    """Real-time health telemetry for connector."""

    model_config = ConfigDict(from_attributes=True)

    api_latency_ms: float
    quota_used_pct: float
    success_rate_pct: float


class ConnectorStatusResponse(BaseModel):
    """Detailed operational health status for a specific connector."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    platform_type: str
    status: str
    last_sync_at: datetime | None = None
    last_sync_status: str | None = None
    total_documents_synced: int
    active_sync_job: dict[str, Any] | None = None
    health_metrics: ConnectorHealthMetrics


class ConnectorRemoveResponse(BaseModel):
    """Response returned when a connector is removed."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    status: str


class ConnectorSyncLogItem(BaseModel):
    """Individual synchronization audit record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    connector_id: uuid.UUID
    sync_job_id: uuid.UUID | None = None
    external_document_id: str
    document_title: str
    source_url: str | None = None
    action_taken: str
    status: str
    checksum: str | None = None
    created_at: datetime


class ConnectorLogsResponse(BaseModel):
    """Response containing sync execution logs."""

    model_config = ConfigDict(from_attributes=True)

    total_logs: int
    logs: list[ConnectorSyncLogItem]
