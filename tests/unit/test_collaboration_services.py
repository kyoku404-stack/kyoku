"""Unit tests for Phase 3.2 EnterpriseCollaborationService.

Owner: Member 2 (Backend & Database Lead)
Domain: /backend/app/services/collaboration/
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.core.exceptions import ConflictException, NotFoundException
from backend.app.schemas.collaboration import (
    PresenceHeartbeatRequest,
    WorkspaceCreateRequest,
)
from backend.app.services.collaboration.contracts import (
    CommentStatus,
    PresenceStatus,
    WorkspaceRole,
)
from backend.app.services.collaboration.service import EnterpriseCollaborationService


@pytest.fixture
def service():
    """Create a collaboration service instance with mocked notification service."""
    notif_svc = MagicMock()
    notif_svc.send_notification = AsyncMock(return_value=MagicMock(id=uuid.uuid4()))
    return EnterpriseCollaborationService(notification_service=notif_svc)


class TestCollaborationServiceUnit:
    """Test unit business logic of EnterpriseCollaborationService."""

    @pytest.mark.asyncio
    async def test_presence_heartbeat_and_roster(self, service):
        """Verify presence heartbeat updates in-memory cache and returns active collaborators."""
        org_id = uuid.uuid4()
        user_1 = uuid.uuid4()
        user_2 = uuid.uuid4()
        workspace_id = uuid.uuid4()

        # Mock db user lookup
        db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = user_1
        mock_user.full_name = "Alice Collaborator"
        mock_user.email = "alice@example.com"
        mock_exec_res = MagicMock()
        mock_exec_res.scalar_one_or_none.return_value = mock_user
        db.execute.return_value = mock_exec_res

        # Heartbeat 1: Alice online
        await service.update_presence(
            db=db,
            org_id=org_id,
            user_id=user_1,
            payload=PresenceHeartbeatRequest(
                workspace_id=workspace_id,
                status=PresenceStatus.EDITING.value,
            ),
        )

        # Heartbeat 2: Bob offline
        mock_user_bob = MagicMock()
        mock_user_bob.id = user_2
        mock_user_bob.full_name = "Bob Inactive"
        mock_user_bob.email = "bob@example.com"
        mock_bob_res = MagicMock()
        mock_bob_res.scalar_one_or_none.return_value = mock_user_bob
        db.execute.return_value = mock_bob_res

        await service.update_presence(
            db=db,
            org_id=org_id,
            user_id=user_2,
            payload=PresenceHeartbeatRequest(
                workspace_id=workspace_id,
                status=PresenceStatus.OFFLINE.value,
            ),
        )

        roster = await service.get_workspace_presence(workspace_id=workspace_id)
        assert roster.workspace_id == workspace_id
        # Bob is OFFLINE so only Alice should be in active roster
        assert len(roster.collaborators) == 1
        assert roster.collaborators[0].user_id == user_1
        assert roster.collaborators[0].status == PresenceStatus.EDITING.value

    @pytest.mark.asyncio
    async def test_create_workspace_slug_conflict(self, service):
        """Verify conflict exception on duplicate workspace slug."""
        db = AsyncMock()
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = MagicMock()
        db.execute.return_value = mock_res

        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        req = WorkspaceCreateRequest(
            name="Engineering",
            slug="engineering-core",
            description="Tech team",
            avatar_color="#4F46E5",
        )

        with pytest.raises(ConflictException):
            await service.create_workspace(db=db, org_id=org_id, user_id=user_id, payload=req)

    @pytest.mark.asyncio
    async def test_create_workspace_success(self, service):
        """Verify workspace creation and admin member binding."""
        db = AsyncMock()
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = None
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.email = "hr_lead@example.com"
        mock_user.full_name = "HR Leader"
        mock_res.scalar_one.return_value = mock_user
        db.execute.return_value = mock_res

        org_id = uuid.uuid4()
        user_id = mock_user.id
        req = WorkspaceCreateRequest(
            name="Human Resources",
            slug="human-resources",
            description="HR workspace",
            avatar_color="#EC4899",
            is_private=True,
        )

        resp = await service.create_workspace(db=db, org_id=org_id, user_id=user_id, payload=req)
        assert resp.name == "Human Resources"
        assert resp.slug == "human-resources"
        assert resp.current_user_role == WorkspaceRole.ADMIN.value
        assert resp.member_count == 1
        assert len(resp.members) == 1
        assert resp.members[0].role == WorkspaceRole.ADMIN.value
        assert db.commit.called

    @pytest.mark.asyncio
    async def test_resolve_comment_not_found(self, service):
        """Verify 404 when attempting to resolve a non-existent comment."""
        db = AsyncMock()
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_res

        with pytest.raises(NotFoundException):
            await service.resolve_comment(
                db=db,
                org_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                comment_id=uuid.uuid4(),
            )

    @pytest.mark.asyncio
    async def test_resolve_comment_success(self, service):
        """Verify resolution timestamp and status update."""
        db = AsyncMock()
        comment = MagicMock()
        comment.id = uuid.uuid4()
        comment.status = CommentStatus.OPEN.value
        comment.workspace_id = uuid.uuid4()
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = comment
        db.execute.return_value = mock_res

        user_id = uuid.uuid4()
        res = await service.resolve_comment(
            db=db,
            org_id=uuid.uuid4(),
            user_id=user_id,
            comment_id=comment.id,
        )
        assert res.status == CommentStatus.RESOLVED.value
        assert res.resolved_by_id == user_id
        assert res.resolved_at is not None
        assert db.commit.called
