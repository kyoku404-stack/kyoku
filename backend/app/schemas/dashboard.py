"""KEEP Enterprise Platform — Dashboard & UX Data Schemas.

Authoritative Pydantic v2 data models for Phase 1.7 Dashboard APIs.
Conforms strictly to docs/Architecture/dashboard-architecture.md Section 3
and docs/API/api-contract.md Section 5.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# 1. Dashboard Summary Schemas
# =============================================================================


class DashboardUser(BaseModel):
    """User profile snippet in dashboard summary."""

    id: UUID
    full_name: str
    email: str
    role: str
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DashboardOrg(BaseModel):
    """Organization metadata in dashboard summary."""

    id: UUID
    name: str
    logo_url: str | None = None
    plan: str = "enterprise"

    model_config = ConfigDict(from_attributes=True)


class DashboardKPI(BaseModel):
    """Key Performance Indicator counters."""

    total_projects: int = Field(default=0, description="Active projects count")
    total_documents: int = Field(default=0, description="Uploaded knowledge assets")
    total_members: int = Field(default=0, description="Total active organization members")
    upcoming_meetings: int = Field(default=0, description="Scheduled upcoming meetings")
    storage_used_bytes: int = Field(default=0, description="Total storage consumed in bytes")
    storage_quota_bytes: int = Field(
        default=107374182400, description="Total storage quota (default 100 GB)"
    )
    ai_queries_today: int = Field(
        default=0, description="Daily AI interactions (ADMIN/ORG_ADMIN only)"
    )


class DashboardSummaryResponse(BaseModel):
    """Full personalized dashboard summary response."""

    user: DashboardUser
    organization: DashboardOrg
    kpi: DashboardKPI
    greeting_time_of_day: str = Field(
        default="morning", description="'morning' | 'afternoon' | 'evening'"
    )


# =============================================================================
# 2. Activity Feed Schemas
# =============================================================================


class ActivityActor(BaseModel):
    """Principal who performed the activity."""

    id: UUID
    full_name: str
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ActivityEventResponse(BaseModel):
    """Chronological organizational activity event item."""

    id: UUID
    actor: ActivityActor
    action: str
    resource_type: str
    resource_id: UUID | None = None
    resource_name: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 3. Recent Projects Schemas
# =============================================================================


class ProjectMemberSummary(BaseModel):
    """Project team member preview."""

    id: UUID
    full_name: str
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProjectSummaryResponse(BaseModel):
    """Recent project summary card."""

    id: UUID
    name: str
    description: str | None = None
    status: str = "active"
    priority: str = "medium"
    progress_percent: int = Field(default=0, ge=0, le=100)
    deadline: str | None = None
    team_members: list[ProjectMemberSummary] = Field(default_factory=list)
    document_count: int = 0
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 4. Recent Documents Schemas
# =============================================================================


class DocumentUploaderSummary(BaseModel):
    """Document uploader summary."""

    id: UUID
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class DocumentSummaryResponse(BaseModel):
    """Recent document summary item."""

    id: UUID
    title: str
    file_type: str = "pdf"
    file_size_bytes: int = 0
    project_id: UUID | None = None
    project_name: str | None = None
    uploaded_by: DocumentUploaderSummary
    uploaded_at: datetime
    last_accessed_at: datetime
    ai_summary_available: bool = False

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 5. Notifications Schemas
# =============================================================================


class NotificationCreate(BaseModel):
    """Payload to create an internal user notification."""

    type: str = Field(default="info", description="info, warning, success, reminder, security")
    title: str = Field(..., max_length=255)
    body: str
    action_url: str | None = Field(default=None, max_length=512)


class NotificationResponse(BaseModel):
    """Notification item delivered to user."""

    id: UUID
    type: str
    title: str
    body: str
    action_url: str | None = None
    is_read: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationReadAllResponse(BaseModel):
    """Response confirming mass read status."""

    updated_count: int = 0


# =============================================================================
# 6. Analytics Overview Schemas
# =============================================================================


class TimeSeriesPoint(BaseModel):
    """Single point in time-series chart data."""

    label: str
    value: int = 0


class ProjectDistributionItem(BaseModel):
    """Project count categorized by status."""

    status: str
    count: int = 0


class DashboardAnalyticsSummaryResponse(BaseModel):
    """Time-series analytics summary for dashboard charts."""

    period: str = "week"
    documents_uploaded: list[TimeSeriesPoint] = Field(default_factory=list)
    active_users: list[TimeSeriesPoint] = Field(default_factory=list)
    new_members: list[TimeSeriesPoint] = Field(default_factory=list)
    project_distribution: list[ProjectDistributionItem] = Field(default_factory=list)
    ai_usage_trend: list[TimeSeriesPoint] = Field(default_factory=list)
    search_trend: list[TimeSeriesPoint] = Field(default_factory=list)


# =============================================================================
# 7. AI Query Schemas (Phase 1.7 Stub)
# =============================================================================


class AIQueryContext(BaseModel):
    """Optional grounding context for AI assistant query."""

    project_id: UUID | None = None
    document_ids: list[UUID] = Field(default_factory=list)


class AIQueryRequest(BaseModel):
    """Payload for submitting an AI assistant query."""

    query: str = Field(..., min_length=1, max_length=4096)
    context: AIQueryContext | None = None
    stream: bool = True


class DocumentReference(BaseModel):
    """Retrieved reference document cited by AI assistant."""

    document_id: UUID
    title: str
    relevance_score: float = 0.0
    excerpt: str = ""


# =============================================================================
# 8. Global Search Schemas
# =============================================================================


class GlobalSearchResultItem(BaseModel):
    """Standardized search hit across organizational resources."""

    type: str = Field(..., description="'project' | 'document' | 'user' | 'team'")
    id: UUID
    title: str
    subtitle: str
    url: str
    icon: str
    relevance_score: float = 1.0


class GlobalSearchResponse(BaseModel):
    """Global search result set."""

    query: str
    total: int = 0
    items: list[GlobalSearchResultItem] = Field(default_factory=list)
