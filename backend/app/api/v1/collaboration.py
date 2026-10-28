"""KEEP Enterprise Platform — Real-Time Collaboration Endpoints.

Serves team workspaces, shared projects, document discussions, threaded comments,
mentions, live presence, version history, activity feeds, and AI assistance.

Specification: devdocs/p3/p3.2.txt (Chapters 1-19) & docs/api/api-contract.md Section 14
Author: Member 2 (Backend & Database Lead)
"""

from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
)
from backend.app.api.dependencies.database import get_db
from backend.app.schemas.collaboration import (
    ActivityFeedResponse,
    AIDiscussionSummaryResponse,
    CommentCreateRequest,
    CommentReplyRequest,
    CommentResolveResponse,
    CommentResponse,
    DocumentCommentsListResponse,
    DocumentVersionHistoryResponse,
    DocumentVersionItemResponse,
    MentionSendRequest,
    MentionSendResponse,
    PresenceHeartbeatRequest,
    ProjectCreateRequest,
    ProjectResponse,
    VersionCreateRequest,
    VersionRollbackRequest,
    WorkspaceAddMemberRequest,
    WorkspaceCreateRequest,
    WorkspaceDashboardResponse,
    WorkspaceDetailResponse,
    WorkspaceListResponse,
    WorkspaceMemberResponse,
    WorkspacePresenceResponse,
)
from backend.app.schemas.envelope import ApiResponse
from backend.app.services.collaboration.service import EnterpriseCollaborationService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Collaboration"])
collaboration_service = EnterpriseCollaborationService()


# ============================================================================
# Workspace Endpoints
# ============================================================================


@router.post(
    "/workspaces/create",
    response_model=ApiResponse[WorkspaceDetailResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create team workspace",
)
async def create_workspace(
    req: WorkspaceCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[WorkspaceDetailResponse]:
    """Creates a team workspace and binds the creator as admin."""
    data = await collaboration_service.create_workspace(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        payload=req,
    )
    return ApiResponse(
        success=True,
        message="Workspace created successfully.",
        data=data,
    )


@router.get(
    "/workspaces/list",
    response_model=ApiResponse[WorkspaceListResponse],
    summary="List team workspaces",
)
async def list_workspaces(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[WorkspaceListResponse]:
    """Lists team workspaces accessible in the current organization."""
    data = await collaboration_service.list_workspaces(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
    )
    return ApiResponse(success=True, data=data)


@router.get(
    "/workspaces/{workspace_id}",
    response_model=ApiResponse[WorkspaceDetailResponse],
    summary="Retrieve workspace by ID",
)
async def get_workspace(
    workspace_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[WorkspaceDetailResponse]:
    """Fetches details, status, and members for a team workspace."""
    data = await collaboration_service.get_workspace(
        db=db,
        org_id=current_user.organization_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
    )
    return ApiResponse(success=True, data=data)


@router.post(
    "/workspaces/{workspace_id}/members",
    response_model=ApiResponse[WorkspaceMemberResponse],
    status_code=status.HTTP_200_OK,
    summary="Add or update workspace member",
)
async def add_workspace_member(
    workspace_id: UUID,
    req: WorkspaceAddMemberRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[WorkspaceMemberResponse]:
    """Binds a user to the workspace with the specified role."""
    data = await collaboration_service.add_workspace_member(
        db=db,
        org_id=current_user.organization_id,
        workspace_id=workspace_id,
        actor_id=current_user.id,
        payload=req,
    )
    return ApiResponse(
        success=True,
        message="Workspace member added/updated successfully.",
        data=data,
    )


@router.get(
    "/workspaces/{workspace_id}/dashboard",
    response_model=ApiResponse[WorkspaceDashboardResponse],
    summary="Retrieve workspace collaboration dashboard",
)
async def get_workspace_dashboard(
    workspace_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[WorkspaceDashboardResponse]:
    """Retrieves live KPIs, open discussions, and timeline activity for a workspace."""
    data = await collaboration_service.get_workspace_dashboard(
        db=db,
        org_id=current_user.organization_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
    )
    return ApiResponse(success=True, data=data)


# ============================================================================
# Shared Project Endpoints
# ============================================================================


@router.post(
    "/projects/create",
    response_model=ApiResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create shared project",
)
async def create_shared_project(
    req: ProjectCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ProjectResponse]:
    """Creates a shared project associated with a workspace."""
    data = await collaboration_service.create_shared_project(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        payload=req,
    )
    return ApiResponse(
        success=True,
        message="Project created successfully.",
        data=data,
    )


# ============================================================================
# Document Discussion & Comment Endpoints
# ============================================================================


@router.post(
    "/comments/create",
    response_model=ApiResponse[CommentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add document comment",
)
async def create_comment(
    req: CommentCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CommentResponse]:
    """Posts a root comment on an enterprise document with mention notification support."""
    data = await collaboration_service.create_comment(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        payload=req,
    )
    return ApiResponse(
        success=True,
        message="Comment posted successfully.",
        data=data,
    )


@router.post(
    "/comments/reply",
    response_model=ApiResponse[CommentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Reply to comment",
)
async def reply_comment(
    req: CommentReplyRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CommentResponse]:
    """Posts a nested reply to an existing comment thread."""
    data = await collaboration_service.reply_comment(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        payload=req,
    )
    return ApiResponse(
        success=True,
        message="Reply posted successfully.",
        data=data,
    )


@router.get(
    "/comments/document/{document_id}",
    response_model=ApiResponse[DocumentCommentsListResponse],
    summary="Get document comments",
)
async def get_document_comments(
    document_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DocumentCommentsListResponse]:
    """Retrieves all threaded comments and replies anchored to a document."""
    data = await collaboration_service.get_document_comments(
        db=db,
        org_id=current_user.organization_id,
        document_id=document_id,
    )
    return ApiResponse(success=True, data=data)


@router.post(
    "/comments/{comment_id}/resolve",
    response_model=ApiResponse[CommentResolveResponse],
    summary="Resolve comment discussion thread",
)
async def resolve_comment(
    comment_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CommentResolveResponse]:
    """Resolves an open comment thread."""
    data = await collaboration_service.resolve_comment(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        comment_id=comment_id,
    )
    return ApiResponse(
        success=True,
        message="Discussion thread resolved successfully.",
        data=data,
    )


# ============================================================================
# Mentions & Presence Endpoints
# ============================================================================


@router.post(
    "/mentions/send",
    response_model=ApiResponse[MentionSendResponse],
    summary="Send direct mention",
)
async def send_mention(
    req: MentionSendRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[MentionSendResponse]:
    """Sends a direct notification to a mentioned user."""
    data = await collaboration_service.send_mention(
        db=db,
        org_id=current_user.organization_id,
        actor_id=current_user.id,
        payload=req,
    )
    return ApiResponse(
        success=True,
        message="Mention notification dispatched successfully.",
        data=data,
    )


@router.post(
    "/presence/heartbeat",
    response_model=ApiResponse[dict[str, bool]],
    summary="Send presence heartbeat",
)
async def presence_heartbeat(
    req: PresenceHeartbeatRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict[str, bool]]:
    """Updates collaborator live presence in a workspace."""
    await collaboration_service.update_presence(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        payload=req,
    )
    return ApiResponse(success=True, data={"received": True})


@router.get(
    "/presence/{workspace_id}",
    response_model=ApiResponse[WorkspacePresenceResponse],
    summary="Get active collaborators presence",
)
async def get_workspace_presence(
    workspace_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> ApiResponse[WorkspacePresenceResponse]:
    """Lists collaborators actively present in the workspace."""
    data = await collaboration_service.get_workspace_presence(workspace_id=workspace_id)
    return ApiResponse(success=True, data=data)


# ============================================================================
# Activity Feed & Version History Endpoints
# ============================================================================


@router.get(
    "/activity/feed",
    response_model=ApiResponse[ActivityFeedResponse],
    summary="Retrieve workspace activity feed",
)
async def get_activity_feed(
    workspace_id: UUID = Query(..., description="Workspace ID"),
    activity_type: str | None = Query(None, description="Optional activity filter"),
    limit: int = Query(30, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActivityFeedResponse]:
    """Retrieves chronological activity timeline events for a workspace."""
    data = await collaboration_service.get_activity_feed(
        db=db,
        org_id=current_user.organization_id,
        workspace_id=workspace_id,
        activity_type=activity_type,
        limit=limit,
    )
    return ApiResponse(success=True, data=data)


@router.get(
    "/version/history/{document_id}",
    response_model=ApiResponse[DocumentVersionHistoryResponse],
    summary="Get document version history",
)
async def get_document_version_history(
    document_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DocumentVersionHistoryResponse]:
    """Retrieves immutable version checkpoints for an enterprise document."""
    data = await collaboration_service.get_version_history(
        db=db,
        org_id=current_user.organization_id,
        document_id=document_id,
    )
    return ApiResponse(success=True, data=data)


@router.post(
    "/version/create",
    response_model=ApiResponse[DocumentVersionItemResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create document version checkpoint",
)
async def create_version_checkpoint(
    req: VersionCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DocumentVersionItemResponse]:
    """Creates a historical version record for a document."""
    data = await collaboration_service.create_version_checkpoint(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        payload=req,
    )
    return ApiResponse(
        success=True,
        message="Version checkpoint created successfully.",
        data=data,
    )


@router.post(
    "/version/rollback",
    response_model=ApiResponse[DocumentVersionItemResponse],
    summary="Roll back document version",
)
async def rollback_document_version(
    req: VersionRollbackRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DocumentVersionItemResponse]:
    """Rolls back a document to a historical version snapshot."""
    data = await collaboration_service.rollback_version(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        payload=req,
    )
    return ApiResponse(
        success=True,
        message="Document rolled back successfully.",
        data=data,
    )


# ============================================================================
# AI Collaboration Assistant Endpoints
# ============================================================================


@router.post(
    "/collaboration/discussions/{document_id}/summary",
    response_model=ApiResponse[AIDiscussionSummaryResponse],
    summary="Summarize document discussion",
)
async def summarize_discussion(
    document_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AIDiscussionSummaryResponse]:
    """Uses the AI Assistant to synthesize discussion threads into key decisions and action items."""
    data = await collaboration_service.summarize_discussion(
        db=db,
        org_id=current_user.organization_id,
        document_id=document_id,
    )
    return ApiResponse(
        success=True,
        message="Discussion summarized successfully.",
        data=data,
    )
