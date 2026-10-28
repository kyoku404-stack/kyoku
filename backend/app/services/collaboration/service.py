"""Enterprise Collaboration Service orchestrator.

Phase: 3.2
Owner: Member 2 (Backend & Database Lead)
Domain: /backend/app/services/collaboration/
Specification: devdocs/p3/p3.2.txt & docs/api/api-contract.md Section 14
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta

from backend.app.core.constants import ErrorCode
from backend.app.core.exceptions import (
    ConflictException,
    NotFoundException,
)
from backend.app.models.collaboration import (
    CollaborationActivity,
    DocumentComment,
    DocumentVersionHistory,
    Workspace,
    WorkspaceMember,
)
from backend.app.models.document import Document
from backend.app.models.project import Project
from backend.app.models.user import User
from backend.app.schemas.collaboration import (
    ActivityFeedResponse,
    ActivityItemResponse,
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
    PresenceCollaboratorResponse,
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
    WorkspaceSummaryItem,
)
from backend.app.schemas.dashboard import NotificationCreate
from backend.app.services.collaboration.contracts import (
    ActivityType,
    CommentStatus,
    DefaultActionItemExtractor,
    DefaultDiscussionSummarizer,
    DefaultKnowledgeSharingRecommender,
    DefaultMentionParser,
    PresenceStatus,
    WorkspaceRole,
)
from backend.app.services.notification_service import NotificationService
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class EnterpriseCollaborationService:
    """Orchestrates team workspaces, discussions, mentions, version history, and AI assistance."""

    def __init__(
        self,
        notification_service: NotificationService | None = None,
        discussion_summarizer: DefaultDiscussionSummarizer | None = None,
        knowledge_recommender: DefaultKnowledgeSharingRecommender | None = None,
        mention_parser: DefaultMentionParser | None = None,
    ) -> None:
        self.notification_service = notification_service or NotificationService()
        self.mention_parser = mention_parser or DefaultMentionParser()
        self.discussion_summarizer = discussion_summarizer or DefaultDiscussionSummarizer(
            mention_parser=self.mention_parser,
            action_extractor=DefaultActionItemExtractor(),
        )
        self.knowledge_recommender = knowledge_recommender or DefaultKnowledgeSharingRecommender()
        # In-memory ephemeral presence cache keyed by (workspace_id_str, user_id_str)
        self._presence_cache: dict[tuple[str, str], PresenceCollaboratorResponse] = {}

    # =========================================================================
    # Workspace Operations
    # =========================================================================

    async def create_workspace(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: WorkspaceCreateRequest,
    ) -> WorkspaceDetailResponse:
        """Create a new team workspace and bind the creator as ADMIN."""
        # 1. Verify unique slug per organization
        existing = await db.execute(
            select(Workspace).where(
                Workspace.organization_id == org_id,
                Workspace.slug == payload.slug,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException(
                message=f"Workspace with slug '{payload.slug}' already exists in this organization.",
                code=ErrorCode.CONFLICT,
            )

        # 2. Persist Workspace record
        workspace = Workspace(
            organization_id=org_id,
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            avatar_color=payload.avatar_color,
            is_private=payload.is_private,
            created_by_id=user_id,
        )
        db.add(workspace)
        await db.flush()

        # 3. Bind Creator as ADMIN member
        admin_member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user_id,
            role=WorkspaceRole.ADMIN.value,
        )
        db.add(admin_member)

        # 4. Record Activity
        activity = CollaborationActivity(
            organization_id=org_id,
            workspace_id=workspace.id,
            actor_id=user_id,
            activity_type=ActivityType.MEMBER_JOINED.value,
            entity_id=workspace.id,
            entity_type="workspace",
            entity_title=workspace.name,
            description=f"Workspace '{workspace.name}' created by admin.",
            metadata_json={"role": WorkspaceRole.ADMIN.value},
        )
        db.add(activity)
        await db.commit()
        await db.refresh(workspace)

        # Fetch creator user details
        user_res = await db.execute(select(User).where(User.id == user_id))
        user_obj = user_res.scalar_one()

        member_item = WorkspaceMemberResponse(
            id=admin_member.id or uuid.uuid4(),
            user_id=user_id,
            email=user_obj.email,
            full_name=user_obj.full_name or user_obj.email,
            role=WorkspaceRole.ADMIN.value,
            joined_at=admin_member.created_at or datetime.now(UTC),
        )

        return WorkspaceDetailResponse(
            id=workspace.id or uuid.uuid4(),
            name=workspace.name,
            slug=workspace.slug,
            description=workspace.description,
            avatar_color=workspace.avatar_color,
            is_private=bool(workspace.is_private),
            is_archived=bool(workspace.is_archived) if workspace.is_archived is not None else False,
            member_count=1,
            current_user_role=WorkspaceRole.ADMIN.value,
            members=[member_item],
            created_at=workspace.created_at or datetime.now(UTC),
        )

    async def get_workspace(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceDetailResponse:
        """Retrieve workspace metadata and members list."""
        stmt = (
            select(Workspace)
            .where(
                Workspace.id == workspace_id,
                Workspace.organization_id == org_id,
            )
            .options(
                selectinload(Workspace.members).selectinload(WorkspaceMember.user),
            )
        )
        res = await db.execute(stmt)
        workspace = res.scalar_one_or_none()
        if not workspace:
            raise NotFoundException(message="Workspace not found.", code=ErrorCode.NOT_FOUND)

        # Determine user role
        user_role = "VIEWER"
        members_list: list[WorkspaceMemberResponse] = []
        for m in workspace.members:
            if m.user_id == user_id:
                user_role = m.role
            u = m.user
            members_list.append(
                WorkspaceMemberResponse(
                    id=m.id,
                    user_id=m.user_id,
                    email=u.email if u else "",
                    full_name=(u.full_name or u.email) if u else "Member",
                    role=m.role,
                    joined_at=m.created_at,
                )
            )

        return WorkspaceDetailResponse(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            description=workspace.description,
            avatar_color=workspace.avatar_color,
            is_private=workspace.is_private,
            is_archived=workspace.is_archived,
            member_count=len(members_list),
            current_user_role=user_role,
            members=members_list,
            created_at=workspace.created_at,
        )

    async def list_workspaces(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceListResponse:
        """List all accessible workspaces within the organization."""
        # Query workspaces in organization
        stmt = (
            select(Workspace)
            .where(
                Workspace.organization_id == org_id,
                Workspace.is_archived.is_(False),
            )
            .options(selectinload(Workspace.members))
            .order_by(desc(Workspace.created_at))
        )
        res = await db.execute(stmt)
        workspaces = res.scalars().all()

        items: list[WorkspaceSummaryItem] = []
        for w in workspaces:
            # Find user role in workspace if bound
            user_role = "GUEST"
            for m in w.members:
                if m.user_id == user_id:
                    user_role = m.role
                    break

            items.append(
                WorkspaceSummaryItem(
                    id=w.id,
                    name=w.name,
                    slug=w.slug,
                    description=w.description,
                    avatar_color=w.avatar_color,
                    is_private=w.is_private,
                    member_count=len(w.members),
                    current_user_role=user_role,
                    created_at=w.created_at,
                )
            )

        return WorkspaceListResponse(total=len(items), workspaces=items)

    async def add_workspace_member(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        workspace_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: WorkspaceAddMemberRequest,
    ) -> WorkspaceMemberResponse:
        """Bind or update a user membership in a team workspace."""
        # 1. Verify workspace exists
        w_res = await db.execute(
            select(Workspace).where(Workspace.id == workspace_id, Workspace.organization_id == org_id)
        )
        workspace = w_res.scalar_one_or_none()
        if not workspace:
            raise NotFoundException(message="Workspace not found.", code=ErrorCode.NOT_FOUND)

        # 2. Check if membership exists
        m_res = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == payload.user_id,
            )
        )
        existing_m = m_res.scalar_one_or_none()
        if existing_m:
            existing_m.role = payload.role
            member_obj = existing_m
        else:
            member_obj = WorkspaceMember(
                workspace_id=workspace_id,
                user_id=payload.user_id,
                role=payload.role,
            )
            db.add(member_obj)

        # Record activity
        activity = CollaborationActivity(
            organization_id=org_id,
            workspace_id=workspace_id,
            actor_id=actor_id,
            activity_type=ActivityType.MEMBER_JOINED.value,
            entity_id=payload.user_id,
            entity_type="user",
            entity_title=workspace.name,
            description=f"User joined workspace '{workspace.name}' as {payload.role}.",
            metadata_json={"role": payload.role},
        )
        db.add(activity)
        await db.commit()
        await db.refresh(member_obj)

        u_res = await db.execute(select(User).where(User.id == payload.user_id))
        user_obj = u_res.scalar_one()

        return WorkspaceMemberResponse(
            id=member_obj.id,
            user_id=user_obj.id,
            email=user_obj.email,
            full_name=user_obj.full_name or user_obj.email,
            role=member_obj.role,
            joined_at=member_obj.created_at,
        )

    async def get_workspace_dashboard(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceDashboardResponse:
        """Compile live dashboard metrics and feeds for a workspace."""
        # Verify workspace
        w_res = await db.execute(
            select(Workspace).where(Workspace.id == workspace_id, Workspace.organization_id == org_id)
        )
        workspace = w_res.scalar_one_or_none()
        if not workspace:
            raise NotFoundException(message="Workspace not found.", code=ErrorCode.NOT_FOUND)

        # Member count
        m_count = await db.scalar(
            select(func.count(WorkspaceMember.id)).where(WorkspaceMember.workspace_id == workspace_id)
        )
        # Project count
        p_count = await db.scalar(
            select(func.count(Project.id)).where(
                Project.organization_id == org_id,
                Project.status == "ACTIVE",
            )
        )
        # Document count
        d_count = await db.scalar(
            select(func.count(Document.id)).where(Document.organization_id == org_id)
        )
        # Open discussions
        open_comments_count = await db.scalar(
            select(func.count(DocumentComment.id)).where(
                DocumentComment.workspace_id == workspace_id,
                DocumentComment.status == CommentStatus.OPEN.value,
            )
        )
        # Pending approvals
        pending_approvals = await db.scalar(
            select(func.count(DocumentVersionHistory.id)).where(
                DocumentVersionHistory.organization_id == org_id,
                DocumentVersionHistory.approval_status == "PENDING_REVIEW",
            )
        )

        # Recent activities
        act_res = await db.execute(
            select(CollaborationActivity)
            .where(CollaborationActivity.workspace_id == workspace_id)
            .order_by(desc(CollaborationActivity.created_at))
            .limit(10)
        )
        activities = [
            {
                "id": str(a.id),
                "activity_type": a.activity_type,
                "actor_id": str(a.actor_id),
                "description": a.description,
                "created_at": a.created_at.isoformat(),
            }
            for a in act_res.scalars().all()
        ]

        # Recent discussions
        comm_res = await db.execute(
            select(DocumentComment)
            .where(DocumentComment.workspace_id == workspace_id)
            .order_by(desc(DocumentComment.created_at))
            .limit(5)
        )
        discussions = [
            {
                "id": str(c.id),
                "document_id": str(c.document_id),
                "content": c.content,
                "status": c.status,
                "created_at": c.created_at.isoformat(),
            }
            for c in comm_res.scalars().all()
        ]

        return WorkspaceDashboardResponse(
            workspace_id=workspace_id,
            active_members_count=m_count or 0,
            active_projects_count=p_count or 0,
            recent_documents_count=d_count or 0,
            open_discussions_count=open_comments_count or 0,
            pending_approvals_count=pending_approvals or 0,
            recent_activities=activities,
            recent_discussions=discussions,
        )

    # =========================================================================
    # Shared Projects
    # =========================================================================

    async def create_shared_project(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: ProjectCreateRequest,
    ) -> ProjectResponse:
        """Create a collaborative project associated with a workspace."""
        # Verify workspace
        w_res = await db.execute(
            select(Workspace).where(Workspace.id == payload.workspace_id, Workspace.organization_id == org_id)
        )
        workspace = w_res.scalar_one_or_none()
        if not workspace:
            raise NotFoundException(message="Workspace not found.", code=ErrorCode.NOT_FOUND)

        project = Project(
            organization_id=org_id,
            owner_id=user_id,
            name=payload.name,
            description=payload.description,
            department=workspace.name,
            status="ACTIVE",
            priority="MEDIUM",
        )
        db.add(project)
        await db.flush()

        activity = CollaborationActivity(
            organization_id=org_id,
            workspace_id=payload.workspace_id,
            actor_id=user_id,
            activity_type=ActivityType.PROJECT_CREATED.value,
            entity_id=project.id,
            entity_type="project",
            entity_title=project.name,
            description=f"Project '{project.name}' created in workspace '{workspace.name}'.",
            metadata_json={"workspace_id": str(payload.workspace_id)},
        )
        db.add(activity)
        await db.commit()
        await db.refresh(project)

        return ProjectResponse(
            id=project.id,
            workspace_id=payload.workspace_id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
        )

    # =========================================================================
    # Document Discussions, Comments & Mentions
    # =========================================================================

    async def create_comment(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: CommentCreateRequest,
    ) -> CommentResponse:
        """Add a root comment on a document with mention parsing and notification dispatch."""
        # 1. Verify document exists
        d_res = await db.execute(
            select(Document).where(Document.id == payload.document_id, Document.organization_id == org_id)
        )
        doc = d_res.scalar_one_or_none()
        if not doc:
            raise NotFoundException(message="Document not found.", code=ErrorCode.NOT_FOUND)

        # 2. Extract mentions
        mentions = self.mention_parser.extract_mentions(payload.content)

        # 3. Persist comment
        comment = DocumentComment(
            organization_id=org_id,
            workspace_id=payload.workspace_id,
            document_id=payload.document_id,
            author_id=user_id,
            content=payload.content,
            page_number=payload.page_number,
            highlight_text=payload.highlight_text,
            status=CommentStatus.OPEN.value,
            mentions_json=mentions,
        )
        db.add(comment)
        await db.flush()

        # 4. Record Activity
        activity = CollaborationActivity(
            organization_id=org_id,
            workspace_id=payload.workspace_id,
            actor_id=user_id,
            activity_type=ActivityType.COMMENT_ADDED.value,
            entity_id=comment.id,
            entity_type="comment",
            entity_title=doc.title,
            description=f"Comment posted on '{doc.title}'.",
            metadata_json={"document_id": str(doc.id), "mentions": mentions},
        )
        db.add(activity)

        # 5. Dispatch notifications for mentions
        for m in mentions:
            # Query user by username/email candidate
            u_res = await db.execute(
                select(User).where(
                    User.organization_id == org_id,
                    User.email.ilike(f"{m}%"),
                )
            )
            mentioned_user = u_res.scalars().first()
            if mentioned_user and mentioned_user.id != user_id:
                try:
                    await self.notification_service.send_notification(
                        db=db,
                        org_id=org_id,
                        user_id=mentioned_user.id,
                        payload=NotificationCreate(
                            type="MENTION",
                            title=f"Mentioned in '{doc.title}'",
                            body=payload.content[:150],
                            action_url=f"/documents/{doc.id}?comment_id={comment.id}",
                        ),
                    )
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Failed to deliver mention notification: {e}")

        await db.commit()
        await db.refresh(comment)

        u_res = await db.execute(select(User).where(User.id == user_id))
        author = u_res.scalar_one()

        return CommentResponse(
            id=comment.id,
            document_id=comment.document_id,
            workspace_id=comment.workspace_id,
            parent_comment_id=None,
            author_id=author.id,
            author_name=author.full_name or author.email,
            content=comment.content,
            page_number=comment.page_number,
            highlight_text=comment.highlight_text,
            status=comment.status,
            resolved_by_id=None,
            resolved_at=None,
            mentions=mentions,
            replies=[],
            created_at=comment.created_at,
        )

    async def reply_comment(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: CommentReplyRequest,
    ) -> CommentResponse:
        """Post a reply to an existing comment thread."""
        p_res = await db.execute(
            select(DocumentComment).where(
                DocumentComment.id == payload.parent_comment_id,
                DocumentComment.organization_id == org_id,
            )
        )
        parent = p_res.scalar_one_or_none()
        if not parent:
            raise NotFoundException(message="Parent comment not found.", code=ErrorCode.NOT_FOUND)

        mentions = self.mention_parser.extract_mentions(payload.content)

        reply = DocumentComment(
            organization_id=org_id,
            workspace_id=parent.workspace_id,
            document_id=parent.document_id,
            parent_comment_id=parent.id,
            author_id=user_id,
            content=payload.content,
            status=CommentStatus.OPEN.value,
            mentions_json=mentions,
        )
        db.add(reply)
        await db.flush()

        activity = CollaborationActivity(
            organization_id=org_id,
            workspace_id=parent.workspace_id,
            actor_id=user_id,
            activity_type=ActivityType.REPLY_ADDED.value,
            entity_id=reply.id,
            entity_type="reply",
            entity_title="Comment Reply",
            description="Reply posted in document discussion thread.",
            metadata_json={"parent_comment_id": str(parent.id)},
        )
        db.add(activity)
        await db.commit()
        await db.refresh(reply)

        u_res = await db.execute(select(User).where(User.id == user_id))
        author = u_res.scalar_one()

        return CommentResponse(
            id=reply.id,
            document_id=reply.document_id,
            workspace_id=reply.workspace_id,
            parent_comment_id=parent.id,
            author_id=author.id,
            author_name=author.full_name or author.email,
            content=reply.content,
            page_number=None,
            highlight_text=None,
            status=reply.status,
            resolved_by_id=None,
            resolved_at=None,
            mentions=mentions,
            replies=[],
            created_at=reply.created_at,
        )

    async def resolve_comment(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        comment_id: uuid.UUID,
    ) -> CommentResolveResponse:
        """Mark a discussion thread as resolved."""
        c_res = await db.execute(
            select(DocumentComment).where(
                DocumentComment.id == comment_id,
                DocumentComment.organization_id == org_id,
            )
        )
        comment = c_res.scalar_one_or_none()
        if not comment:
            raise NotFoundException(message="Comment not found.", code=ErrorCode.NOT_FOUND)

        now = datetime.now(UTC)
        comment.status = CommentStatus.RESOLVED.value
        comment.resolved_by_id = user_id
        comment.resolved_at = now

        activity = CollaborationActivity(
            organization_id=org_id,
            workspace_id=comment.workspace_id,
            actor_id=user_id,
            activity_type=ActivityType.DISCUSSION_RESOLVED.value,
            entity_id=comment.id,
            entity_type="comment",
            entity_title="Resolved Comment",
            description="Discussion thread resolved.",
            metadata_json={"comment_id": str(comment.id)},
        )
        db.add(activity)
        await db.commit()
        await db.refresh(comment)

        return CommentResolveResponse(
            id=comment.id,
            status=comment.status,
            resolved_by_id=comment.resolved_by_id,
            resolved_at=comment.resolved_at,
        )

    async def get_document_comments(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> DocumentCommentsListResponse:
        """Fetch all threaded comments and replies associated with a document."""
        # 1. Fetch all comments for document
        stmt = (
            select(DocumentComment)
            .where(
                DocumentComment.document_id == document_id,
                DocumentComment.organization_id == org_id,
            )
            .options(
                selectinload(DocumentComment.author),
                selectinload(DocumentComment.resolved_by),
            )
            .order_by(DocumentComment.created_at.asc())
        )
        res = await db.execute(stmt)
        all_comments = res.scalars().all()

        # 2. Build recursive tree (root comments with nested replies)
        comment_dict: dict[uuid.UUID, CommentResponse] = {}
        roots: list[CommentResponse] = []

        for c in all_comments:
            author_name = (c.author.full_name or c.author.email) if c.author else "Contributor"
            c_resp = CommentResponse(
                id=c.id,
                document_id=c.document_id,
                workspace_id=c.workspace_id,
                parent_comment_id=c.parent_comment_id,
                author_id=c.author_id,
                author_name=author_name,
                content=c.content,
                page_number=c.page_number,
                highlight_text=c.highlight_text,
                status=c.status,
                resolved_by_id=c.resolved_by_id,
                resolved_at=c.resolved_at,
                mentions=list(c.mentions_json or []),
                replies=[],
                created_at=c.created_at,
            )
            comment_dict[c.id] = c_resp

        for c in all_comments:
            if c.parent_comment_id and c.parent_comment_id in comment_dict:
                comment_dict[c.parent_comment_id].replies.append(comment_dict[c.id])
            else:
                roots.append(comment_dict[c.id])

        return DocumentCommentsListResponse(
            document_id=document_id,
            total_comments=len(all_comments),
            comments=roots,
        )

    async def send_mention(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: MentionSendRequest,
    ) -> MentionSendResponse:
        """Dispatch a direct mention notification to a specific colleague."""
        d_res = await db.execute(
            select(Document).where(Document.id == payload.document_id, Document.organization_id == org_id)
        )
        doc = d_res.scalar_one_or_none()
        title = doc.title if doc else "Enterprise Document"

        notif = await self.notification_service.send_notification(
            db=db,
            org_id=org_id,
            user_id=payload.mentioned_user_id,
            payload=NotificationCreate(
                type="MENTION",
                title=f"Mentioned in '{title}'",
                body=payload.context_text,
                action_url=f"/documents/{payload.document_id}",
            ),
        )

        activity = CollaborationActivity(
            organization_id=org_id,
            workspace_id=payload.workspace_id,
            actor_id=actor_id,
            activity_type=ActivityType.USER_MENTION.value,
            entity_id=payload.mentioned_user_id,
            entity_type="mention",
            entity_title=title,
            description=f"Direct mention sent in '{title}'.",
            metadata_json={"document_id": str(payload.document_id)},
        )
        db.add(activity)
        await db.commit()

        return MentionSendResponse(
            notification_id=notif.id,
            delivered=True,
        )

    # =========================================================================
    # Live Presence Engine
    # =========================================================================

    async def update_presence(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: PresenceHeartbeatRequest,
    ) -> None:
        """Record live heartbeat in cache."""
        u_res = await db.execute(select(User).where(User.id == user_id))
        user_obj = u_res.scalar_one_or_none()
        name = (user_obj.full_name or user_obj.email) if user_obj else "Collaborator"
        email = user_obj.email if user_obj else ""

        key = (str(payload.workspace_id), str(user_id))
        self._presence_cache[key] = PresenceCollaboratorResponse(
            user_id=user_id,
            full_name=name,
            email=email,
            status=payload.status,
            document_id=payload.document_id,
            last_seen_at=datetime.now(UTC),
        )

    async def get_workspace_presence(
        self,
        workspace_id: uuid.UUID,
    ) -> WorkspacePresenceResponse:
        """Fetch all active collaborators seen in the last 120 seconds."""
        cutoff = datetime.now(UTC) - timedelta(seconds=120)
        active: list[PresenceCollaboratorResponse] = []
        w_id_str = str(workspace_id)

        for (w_key, _), presence in list(self._presence_cache.items()):
            if (
                w_key == w_id_str
                and presence.last_seen_at >= cutoff
                and presence.status != PresenceStatus.OFFLINE.value
            ):
                active.append(presence)

        return WorkspacePresenceResponse(
            workspace_id=workspace_id,
            collaborators=active,
        )

    # =========================================================================
    # Activity Feed Timeline
    # =========================================================================

    async def get_activity_feed(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        workspace_id: uuid.UUID,
        activity_type: str | None = None,
        limit: int = 30,
    ) -> ActivityFeedResponse:
        """Fetch workspace activity timeline events with actor associations."""
        stmt = (
            select(CollaborationActivity)
            .where(
                CollaborationActivity.organization_id == org_id,
                CollaborationActivity.workspace_id == workspace_id,
            )
            .options(selectinload(CollaborationActivity.actor))
            .order_by(desc(CollaborationActivity.created_at))
            .limit(limit)
        )
        if activity_type:
            stmt = stmt.where(CollaborationActivity.activity_type == activity_type)

        res = await db.execute(stmt)
        activities = res.scalars().all()

        items = [
            ActivityItemResponse(
                id=a.id,
                activity_type=a.activity_type,
                actor_id=a.actor_id,
                actor_name=(a.actor.full_name or a.actor.email) if a.actor else "System",
                entity_id=a.entity_id,
                entity_type=a.entity_type,
                entity_title=a.entity_title,
                description=a.description,
                metadata=dict(a.metadata_json or {}),
                created_at=a.created_at,
            )
            for a in activities
        ]

        return ActivityFeedResponse(
            workspace_id=workspace_id,
            activities=items,
        )

    # =========================================================================
    # Version History & Rollback
    # =========================================================================

    async def get_version_history(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> DocumentVersionHistoryResponse:
        """Retrieve complete version checkpoint records for a document."""
        stmt = (
            select(DocumentVersionHistory)
            .where(
                DocumentVersionHistory.document_id == document_id,
                DocumentVersionHistory.organization_id == org_id,
            )
            .options(selectinload(DocumentVersionHistory.editor))
            .order_by(desc(DocumentVersionHistory.version_number))
        )
        res = await db.execute(stmt)
        versions = res.scalars().all()

        items = [
            DocumentVersionItemResponse(
                version_id=v.id,
                version_number=v.version_number,
                editor_id=v.editor_id,
                editor_name=(v.editor.full_name or v.editor.email) if v.editor else "Editor",
                change_summary=v.change_summary,
                file_size_bytes=v.file_size_bytes,
                checksum=v.checksum,
                approval_status=v.approval_status,
                created_at=v.created_at,
            )
            for v in versions
        ]

        return DocumentVersionHistoryResponse(
            document_id=document_id,
            total_versions=len(items),
            versions=items,
        )

    async def create_version_checkpoint(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: VersionCreateRequest,
    ) -> DocumentVersionItemResponse:
        """Create a new version checkpoint for a document."""
        # Find latest version number
        latest_v = await db.scalar(
            select(func.max(DocumentVersionHistory.version_number)).where(
                DocumentVersionHistory.document_id == payload.document_id,
                DocumentVersionHistory.organization_id == org_id,
            )
        )
        next_v = (latest_v or 0) + 1

        version_record = DocumentVersionHistory(
            organization_id=org_id,
            document_id=payload.document_id,
            version_number=next_v,
            editor_id=user_id,
            change_summary=payload.change_summary,
            file_path=payload.file_path,
            file_size_bytes=payload.file_size_bytes,
            checksum=payload.checksum,
            approval_status=payload.approval_status,
        )
        db.add(version_record)
        await db.flush()

        activity = CollaborationActivity(
            organization_id=org_id,
            workspace_id=None,
            actor_id=user_id,
            activity_type=ActivityType.VERSION_CHECKPOINT.value,
            entity_id=payload.document_id,
            entity_type="document_version",
            entity_title=f"Version {next_v}",
            description=f"Document version {next_v} created: {payload.change_summary}",
            metadata_json={"version_number": next_v},
        )
        db.add(activity)
        await db.commit()
        await db.refresh(version_record)

        u_res = await db.execute(select(User).where(User.id == user_id))
        user_obj = u_res.scalar_one()

        return DocumentVersionItemResponse(
            version_id=version_record.id,
            version_number=version_record.version_number,
            editor_id=user_id,
            editor_name=user_obj.full_name or user_obj.email,
            change_summary=version_record.change_summary,
            file_size_bytes=version_record.file_size_bytes,
            checksum=version_record.checksum,
            approval_status=version_record.approval_status,
            created_at=version_record.created_at,
        )

    async def rollback_version(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: VersionRollbackRequest,
    ) -> DocumentVersionItemResponse:
        """Revert a document state to a previous version checkpoint by forward increment."""
        # Find target version
        t_res = await db.execute(
            select(DocumentVersionHistory).where(
                DocumentVersionHistory.document_id == payload.document_id,
                DocumentVersionHistory.organization_id == org_id,
                DocumentVersionHistory.version_number == payload.target_version_number,
            )
        )
        target = t_res.scalar_one_or_none()
        if not target:
            raise NotFoundException(
                message=f"Version {payload.target_version_number} not found.",
                code=ErrorCode.NOT_FOUND,
            )

        # Create new version with summary indicating rollback
        summary = f"Rolled back to Version {target.version_number}: {target.change_summary}"
        return await self.create_version_checkpoint(
            db=db,
            org_id=org_id,
            user_id=user_id,
            payload=VersionCreateRequest(
                document_id=payload.document_id,
                change_summary=summary,
                file_path=target.file_path,
                file_size_bytes=target.file_size_bytes,
                checksum=target.checksum,
                approval_status="APPROVED",
            ),
        )

    # =========================================================================
    # AI Collaboration Assistant
    # =========================================================================

    async def summarize_discussion(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> AIDiscussionSummaryResponse:
        """Synthesize document discussion into an executive summary, decisions, and action items."""
        # 1. Fetch document
        d_res = await db.execute(
            select(Document).where(Document.id == document_id, Document.organization_id == org_id)
        )
        doc = d_res.scalar_one_or_none()
        title = doc.title if doc else "Enterprise Document"

        # 2. Fetch comments
        comments_resp = await self.get_document_comments(db=db, org_id=org_id, document_id=document_id)
        comments_list = [
            {
                "author_name": c.author_name,
                "content": c.content,
                "status": c.status,
                "created_at": c.created_at.isoformat(),
            }
            for c in comments_resp.comments
        ]

        # 3. Invoke summarizer engine
        summary_result = self.discussion_summarizer.summarize(
            document_id=str(document_id),
            document_title=title,
            comments=comments_list,
        )

        # 4. Generate cross-department recommendations
        other_docs_res = await db.execute(
            select(Document).where(Document.organization_id == org_id).limit(10)
        )
        candidates = [
            {
                "id": str(d.id),
                "title": d.title,
                "department": "General",
                "views_count": 25,
            }
            for d in other_docs_res.scalars().all()
        ]
        recs = self.knowledge_recommender.recommend_related(
            document_id=str(document_id),
            department="Engineering",
            candidate_pool=candidates,
        )
        rec_dicts = [
            {
                "document_id": r.document_id,
                "title": r.title,
                "department": r.department,
                "relevance_score": r.relevance_score,
                "reason": r.reason,
            }
            for r in recs
        ]

        return AIDiscussionSummaryResponse(
            document_id=document_id,
            executive_summary=summary_result.executive_summary,
            key_decisions=[
                {"decision": d.decision, "agreed_by": d.agreed_by, "timestamp": d.timestamp}
                for d in summary_result.key_decisions
            ],
            action_items=[
                {"action": a.action, "assignee": a.assignee, "deadline": a.deadline, "confidence": a.confidence}
                for a in summary_result.action_items
            ],
            unresolved_questions=summary_result.unresolved_questions,
            suggested_documents=rec_dicts,
            processing_time_ms=summary_result.processing_time_ms,
        )
