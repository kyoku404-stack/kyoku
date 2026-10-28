"""KEEP Enterprise Platform — Real-Time Collaboration & Team Workspaces Pydantic v2 Schemas.

Specification: devdocs/p3/p3.2.txt & docs/api/api-contract.md Section 14
Author: Member 2 (Backend & Database Lead)
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Workspace Schemas
# ============================================================================


class WorkspaceCreateRequest(BaseModel):
    """Payload to create a new team workspace."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=120, description="Display name of the team workspace")
    slug: str = Field(..., min_length=1, max_length=120, description="URL-safe unique identifier slug")
    description: str | None = Field(None, description="Detailed workspace purpose")
    avatar_color: str = Field("#4F46E5", description="Hexadecimal or RGB theme color")
    is_private: bool = Field(False, description="Private workspace restricted to explicit members")


class WorkspaceMemberResponse(BaseModel):
    """Member association details in a workspace."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    full_name: str
    role: str
    joined_at: datetime


class WorkspaceDetailResponse(BaseModel):
    """Complete workspace metadata including members and status."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    avatar_color: str = "#4F46E5"
    is_private: bool = False
    is_archived: bool = False
    member_count: int = 0
    current_user_role: str = "MEMBER"
    members: list[WorkspaceMemberResponse] = Field(default_factory=list)
    created_at: datetime


class WorkspaceSummaryItem(BaseModel):
    """Summarized workspace item for listing."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    avatar_color: str = "#4F46E5"
    is_private: bool = False
    member_count: int = 0
    current_user_role: str = "MEMBER"
    created_at: datetime


class WorkspaceListResponse(BaseModel):
    """List of accessible team workspaces."""

    model_config = ConfigDict(from_attributes=True)

    total: int
    workspaces: list[WorkspaceSummaryItem]


class WorkspaceAddMemberRequest(BaseModel):
    """Payload to invite/bind a user to a team workspace."""

    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    role: str = Field("MEMBER", description="ADMIN, MEMBER, VIEWER, or GUEST")


class WorkspaceDashboardResponse(BaseModel):
    """Live analytics and activity dashboard summary for a workspace."""

    model_config = ConfigDict(from_attributes=True)

    workspace_id: uuid.UUID
    active_members_count: int = 0
    active_projects_count: int = 0
    recent_documents_count: int = 0
    open_discussions_count: int = 0
    pending_approvals_count: int = 0
    recent_activities: list[dict[str, Any]] = Field(default_factory=list)
    recent_discussions: list[dict[str, Any]] = Field(default_factory=list)


# ============================================================================
# Shared Project Schemas
# ============================================================================


class ProjectCreateRequest(BaseModel):
    """Payload to create a shared project within a workspace."""

    model_config = ConfigDict(from_attributes=True)

    workspace_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ProjectResponse(BaseModel):
    """Response returned upon shared project creation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None = None
    created_at: datetime


# ============================================================================
# Document Discussion & Comment Schemas
# ============================================================================


class CommentCreateRequest(BaseModel):
    """Payload to post a root comment on an enterprise document."""

    model_config = ConfigDict(from_attributes=True)

    document_id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    content: str = Field(..., min_length=1, description="Comment body containing potential @mentions")
    page_number: int | None = Field(None, ge=1)
    highlight_text: str | None = None


class CommentReplyRequest(BaseModel):
    """Payload to reply to an existing comment thread."""

    model_config = ConfigDict(from_attributes=True)

    parent_comment_id: uuid.UUID
    content: str = Field(..., min_length=1, description="Reply body containing potential @mentions")


class CommentResponse(BaseModel):
    """Serialized comment record with threaded replies."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    parent_comment_id: uuid.UUID | None = None
    author_id: uuid.UUID
    author_name: str
    content: str
    page_number: int | None = None
    highlight_text: str | None = None
    status: str = "OPEN"
    resolved_by_id: uuid.UUID | None = None
    resolved_at: datetime | None = None
    mentions: list[str] = Field(default_factory=list)
    replies: list["CommentResponse"] = Field(default_factory=list)
    created_at: datetime


class CommentResolveResponse(BaseModel):
    """Confirmation payload for resolved discussion."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    resolved_by_id: uuid.UUID | None = None
    resolved_at: datetime | None = None


class DocumentCommentsListResponse(BaseModel):
    """Collection of threaded comments for a document."""

    model_config = ConfigDict(from_attributes=True)

    document_id: uuid.UUID
    total_comments: int
    comments: list[CommentResponse]


# ============================================================================
# Mentions & Presence Schemas
# ============================================================================


class MentionSendRequest(BaseModel):
    """Payload to explicitly send a user mention notification."""

    model_config = ConfigDict(from_attributes=True)

    mentioned_user_id: uuid.UUID
    document_id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    context_text: str = Field(..., min_length=1)


class MentionSendResponse(BaseModel):
    """Response confirming mention dispatch."""

    model_config = ConfigDict(from_attributes=True)

    notification_id: uuid.UUID
    delivered: bool


class PresenceHeartbeatRequest(BaseModel):
    """Collaborator heartbeat updating active status."""

    model_config = ConfigDict(from_attributes=True)

    workspace_id: uuid.UUID
    status: str = Field("ONLINE", description="ONLINE, OFFLINE, AWAY, EDITING, VIEWING")
    document_id: uuid.UUID | None = None


class PresenceCollaboratorResponse(BaseModel):
    """Collaborator active presence state."""

    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    full_name: str
    email: str
    status: str
    document_id: uuid.UUID | None = None
    last_seen_at: datetime


class WorkspacePresenceResponse(BaseModel):
    """Active presence roster for a workspace."""

    model_config = ConfigDict(from_attributes=True)

    workspace_id: uuid.UUID
    collaborators: list[PresenceCollaboratorResponse]


# ============================================================================
# Activity Feed & Version History Schemas
# ============================================================================


class ActivityItemResponse(BaseModel):
    """Individual collaborative timeline event."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    activity_type: str
    actor_id: uuid.UUID
    actor_name: str
    entity_id: uuid.UUID
    entity_type: str
    entity_title: str | None = None
    description: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ActivityFeedResponse(BaseModel):
    """Workspace activity stream response."""

    model_config = ConfigDict(from_attributes=True)

    workspace_id: uuid.UUID
    activities: list[ActivityItemResponse]


class DocumentVersionItemResponse(BaseModel):
    """Historical version checkpoint."""

    model_config = ConfigDict(from_attributes=True)

    version_id: uuid.UUID
    version_number: int
    editor_id: uuid.UUID
    editor_name: str
    change_summary: str
    file_size_bytes: int | None = None
    checksum: str | None = None
    approval_status: str
    created_at: datetime


class DocumentVersionHistoryResponse(BaseModel):
    """Complete document version history."""

    model_config = ConfigDict(from_attributes=True)

    document_id: uuid.UUID
    total_versions: int
    versions: list[DocumentVersionItemResponse]


class VersionCreateRequest(BaseModel):
    """Payload to record a new document version checkpoint."""

    model_config = ConfigDict(from_attributes=True)

    document_id: uuid.UUID
    change_summary: str = Field(..., min_length=1)
    file_path: str | None = None
    file_size_bytes: int | None = None
    checksum: str | None = None
    approval_status: str = "APPROVED"


class VersionRollbackRequest(BaseModel):
    """Payload to roll back a document to a historical version."""

    model_config = ConfigDict(from_attributes=True)

    document_id: uuid.UUID
    target_version_number: int = Field(..., ge=1)


# ============================================================================
# AI Collaboration Schemas
# ============================================================================


class AIDiscussionSummaryResponse(BaseModel):
    """AI briefing for a document discussion thread."""

    model_config = ConfigDict(from_attributes=True)

    document_id: uuid.UUID
    executive_summary: str
    key_decisions: list[dict[str, Any]] = Field(default_factory=list)
    action_items: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    suggested_documents: list[dict[str, Any]] = Field(default_factory=list)
    processing_time_ms: float = 0.0


class KnowledgeRecommendationResponse(BaseModel):
    """Knowledge sharing cross-department recommendation response."""

    model_config = ConfigDict(from_attributes=True)

    document_id: uuid.UUID
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
