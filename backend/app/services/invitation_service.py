"""KEEP Enterprise Platform — User Invitation Service."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from backend.app.core.constants import ErrorCode
from backend.app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from backend.app.core.security import get_password_hash
from backend.app.models.invitation import Invitation
from backend.app.models.user import User
from backend.app.repositories.department_repo import DepartmentRepository
from backend.app.repositories.invitation_repo import InvitationRepository
from backend.app.repositories.team_repo import TeamRepository
from backend.app.repositories.user_repo import UserRepository
from backend.app.schemas.invitation import (
    InvitationAccept,
    InvitationCreate,
    InvitationResponse,
)
from backend.app.services.activity_service import ActivityService
from backend.app.services.base import BaseService
from sqlalchemy.ext.asyncio import AsyncSession


class InvitationService(BaseService[InvitationRepository]):
    """Service handling enterprise member invitations and onboarding activation."""

    def __init__(
        self,
        repository: InvitationRepository | None = None,
        user_repo: UserRepository | None = None,
        department_repo: DepartmentRepository | None = None,
        team_repo: TeamRepository | None = None,
    ) -> None:
        super().__init__(repository or InvitationRepository())
        self.user_repo = user_repo or UserRepository()
        self.department_repo = department_repo or DepartmentRepository()
        self.team_repo = team_repo or TeamRepository()

    def _to_response(self, inv: Invitation) -> InvitationResponse:
        return InvitationResponse(
            id=inv.id,
            organization_id=inv.organization_id,
            department_id=inv.department_id,
            team_id=inv.team_id,
            email=inv.email,
            role=inv.role,
            token=inv.token,
            status=inv.status,
            invited_by_id=inv.invited_by_id,
            expires_at=inv.expires_at,
            created_at=inv.created_at,
            updated_at=inv.updated_at,
        )

    async def create_invitation(
        self,
        db: AsyncSession,
        org_id: UUID,
        payload: InvitationCreate,
        caller_user_id: UUID,
    ) -> InvitationResponse:
        """Dispatches a secure invitation to a new enterprise member."""
        existing_user = await self.user_repo.get_by_email(db, str(payload.email))
        if existing_user and existing_user.organization_id == org_id and not existing_user.is_deleted:
            raise ConflictException(
                message=f"User with email '{payload.email}' is already an active member of this organization.",
                code=ErrorCode.AUTH_EMAIL_EXISTS,
            )

        existing_pending = await self.repository.get_pending_by_email(db, org_id, str(payload.email))
        if existing_pending:
            raise ConflictException(
                message=f"A pending invitation already exists for '{payload.email}'.",
                code=ErrorCode.CONFLICT,
            )

        if payload.department_id:
            dept = await self.department_repo.get_by_id_scoped(db, org_id, payload.department_id)
            if not dept:
                raise NotFoundException(
                    message=f"Department with ID '{payload.department_id}' not found.",
                    code=ErrorCode.DEPT_NOT_FOUND,
                )

        if payload.team_id:
            team = await self.team_repo.get_by_id_scoped(db, org_id, payload.team_id)
            if not team:
                raise NotFoundException(
                    message=f"Team with ID '{payload.team_id}' not found.",
                    code=ErrorCode.TEAM_NOT_FOUND,
                )

        token = f"inv_{secrets.token_urlsafe(32)}"
        expires_at = datetime.now(UTC) + timedelta(days=7)

        invitation = Invitation(
            organization_id=org_id,
            department_id=payload.department_id,
            team_id=payload.team_id,
            email=str(payload.email).lower(),
            role=payload.role,
            token=token,
            status="PENDING",
            invited_by_id=caller_user_id,
            expires_at=expires_at,
        )
        db.add(invitation)
        await db.flush()
        await db.refresh(invitation)

        await ActivityService.record_activity(
            db,
            organization_id=org_id,
            user_id=caller_user_id,
            action="INVITATION_SENT",
            resource_type="invitation",
            resource_id=invitation.id,
            details=f"Invited '{invitation.email}' as '{invitation.role}'",
        )
        await db.commit()
        await db.refresh(invitation)
        return self._to_response(invitation)

    async def list_invitations(
        self,
        db: AsyncSession,
        org_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[InvitationResponse]:
        """Lists pending invitations for the tenant."""
        invitations = await self.repository.list_for_organization(
            db, org_id, status="PENDING", skip=skip, limit=limit
        )
        return [self._to_response(inv) for inv in invitations]

    async def revoke_invitation(
        self,
        db: AsyncSession,
        org_id: UUID,
        invitation_id: UUID,
        caller_user_id: UUID,
    ) -> bool:
        """Revokes a pending invitation."""
        invitation = await self.repository.get_by_id_scoped(db, org_id, invitation_id)
        if not invitation:
            raise NotFoundException(
                message=f"Invitation with ID '{invitation_id}' not found.",
                code=ErrorCode.INVITATION_NOT_FOUND,
            )

        if invitation.status != "PENDING":
            raise BadRequestException(
                message=f"Cannot revoke invitation with status '{invitation.status}'.",
                code=ErrorCode.INVALID_REQUEST,
            )

        invitation.status = "REVOKED"
        db.add(invitation)
        await db.flush()

        await ActivityService.record_activity(
            db,
            organization_id=org_id,
            user_id=caller_user_id,
            action="INVITATION_REVOKED",
            resource_type="invitation",
            resource_id=invitation.id,
            details=f"Revoked invitation for '{invitation.email}'",
        )
        await db.commit()
        return True

    async def accept_invitation(
        self,
        db: AsyncSession,
        payload: InvitationAccept,
    ) -> dict[str, Any]:
        """Validates token and onboard/activates member account."""
        invitation = await self.repository.get_by_token(db, payload.token)
        if not invitation:
            raise NotFoundException(
                message="Invitation token is invalid or does not exist.",
                code=ErrorCode.INVITATION_NOT_FOUND,
            )

        if invitation.status == "ACCEPTED":
            raise ConflictException(
                message="This invitation has already been accepted.",
                code=ErrorCode.INVITATION_ALREADY_ACCEPTED,
            )

        if invitation.status == "REVOKED":
            raise ConflictException(
                message="This invitation has been revoked by an administrator.",
                code=ErrorCode.INVITATION_REVOKED,
            )

        expires_at = invitation.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        if expires_at < datetime.now(UTC):
            invitation.status = "EXPIRED"
            db.add(invitation)
            await db.commit()
            raise ConflictException(
                message="This invitation token has expired.",
                code=ErrorCode.INVITATION_EXPIRED,
            )

        hashed_password = get_password_hash(payload.password)
        existing_user = await self.user_repo.get_by_email(db, invitation.email)

        if existing_user:
            user = existing_user
            user.full_name = payload.full_name
            user.hashed_password = hashed_password
            user.organization_id = invitation.organization_id
            user.role = invitation.role
            user.department_id = invitation.department_id
            user.team_id = invitation.team_id
            user.is_active = True
            user.is_deleted = False
        else:
            user = User(
                organization_id=invitation.organization_id,
                email=invitation.email,
                hashed_password=hashed_password,
                full_name=payload.full_name,
                role=invitation.role,
                department_id=invitation.department_id,
                team_id=invitation.team_id,
                is_active=True,
            )
            db.add(user)

        invitation.status = "ACCEPTED"
        db.add(invitation)
        await db.flush()
        await db.refresh(user)

        await ActivityService.record_activity(
            db,
            organization_id=invitation.organization_id,
            user_id=user.id,
            action="INVITATION_ACCEPTED",
            resource_type="invitation",
            resource_id=invitation.id,
            details=f"User '{user.full_name}' ({user.email}) joined as '{user.role}'",
        )
        await db.commit()
        await db.refresh(user)

        return {
            "accepted": True,
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organization_id": user.organization_id,
        }
