"""KEEP Enterprise Platform — Organization & Hierarchy Management Unit Tests.

Validates Pydantic schemas, domain services, business logic, RBAC, and multi-tenant isolation.
"""

import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.constants import ErrorCode
from backend.app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from backend.app.schemas.department import DepartmentCreate
from backend.app.schemas.invitation import InvitationAccept, InvitationCreate
from backend.app.schemas.member import MemberUpdate
from backend.app.schemas.organization import OrganizationCreate, OrganizationUpdate
from backend.app.schemas.project import ProjectCreate
from backend.app.schemas.team import TeamCreate
from backend.app.services.department_service import DepartmentService
from backend.app.services.invitation_service import InvitationService
from backend.app.services.member_service import MemberService
from backend.app.services.org_service import OrganizationService
from backend.app.services.team_service import TeamService


@pytest.fixture
async def async_test_db():
    """Provides an isolated in-memory SQLite async session for unit testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    from backend.app.db.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


class TestOrganizationHierarchySchemas:
    """Validates Phase 1.5 Pydantic schema validation rules."""

    def test_organization_create_valid(self):
        payload = OrganizationCreate(
            name="Acme Corp",
            domain="acme.com",
            industry="Technology",
            company_size="100-500",
            time_zone="UTC",
            default_language="en-US",
        )
        assert payload.name == "Acme Corp"
        assert payload.domain == "acme.com"

    def test_organization_create_invalid_name(self):
        with pytest.raises(ValidationError):
            OrganizationCreate(name="A", domain="acme.com")

    def test_department_create_valid(self):
        payload = DepartmentCreate(name="Engineering", description="Core engineering")
        assert payload.name == "Engineering"

    def test_team_create_valid(self):
        dept_id = uuid.uuid4()
        payload = TeamCreate(name="Backend Team", department_id=dept_id)
        assert payload.name == "Backend Team"
        assert payload.department_id == dept_id

    def test_project_create_valid(self):
        payload = ProjectCreate(name="Project Helios", priority="HIGH")
        assert payload.name == "Project Helios"
        assert payload.priority == "HIGH"

    def test_invitation_create_valid(self):
        payload = InvitationCreate(email="user@example.com", role="Member")
        assert payload.email == "user@example.com"
        assert payload.role == "Member"

    def test_invitation_create_invalid_email(self):
        with pytest.raises(ValidationError):
            InvitationCreate(email="not-an-email", role="Member")

    def test_invitation_accept_valid(self):
        payload = InvitationAccept(
            token="inv_1234567890abcdef",
            full_name="Jane Doe",
            password="SecurePassword123!",
        )
        assert payload.full_name == "Jane Doe"


class TestOrganizationServiceUnit:
    """Tests OrganizationService logic and multi-tenant barrier."""

    @pytest.mark.asyncio
    async def test_create_organization_success(self, async_test_db: AsyncSession):
        service = OrganizationService()
        payload = OrganizationCreate(
            name="Wayne Enterprises",
            domain="wayne.com",
            industry="Defense",
            company_size="1000+",
        )
        org = await service.create_organization(async_test_db, payload)
        assert org.name == "Wayne Enterprises"
        assert org.domain == "wayne.com"
        assert org.is_active is True

    @pytest.mark.asyncio
    async def test_create_organization_duplicate_domain(self, async_test_db: AsyncSession):
        service = OrganizationService()
        payload = OrganizationCreate(name="Org One", domain="dup.com")
        await service.create_organization(async_test_db, payload)

        payload2 = OrganizationCreate(name="Org Two", domain="dup.com")
        with pytest.raises(ConflictException) as exc:
            await service.create_organization(async_test_db, payload2)
        assert exc.value.code == ErrorCode.ORG_DOMAIN_EXISTS

    @pytest.mark.asyncio
    async def test_cross_tenant_isolation_barrier(self, async_test_db: AsyncSession):
        service = OrganizationService()
        org_a = await service.create_organization(
            async_test_db, OrganizationCreate(name="Tenant A", domain="tenant-a.com")
        )
        org_b = await service.create_organization(
            async_test_db, OrganizationCreate(name="Tenant B", domain="tenant-b.com")
        )

        with pytest.raises(ForbiddenException) as exc:
            await service.get_organization_by_id(
                async_test_db,
                org_id=org_b.id,
                caller_org_id=org_a.id,
                is_super_admin=False,
            )
        assert exc.value.code == ErrorCode.TENANT_ACCESS_DENIED

    @pytest.mark.asyncio
    async def test_update_and_archive_organization(self, async_test_db: AsyncSession):
        service = OrganizationService()
        org = await service.create_organization(
            async_test_db, OrganizationCreate(name="Stark Industries", domain="stark.com")
        )

        updated = await service.update_organization(
            async_test_db,
            org.id,
            OrganizationUpdate(name="Stark Global", settings={"max_upload_size_mb": 100}),
            caller_user_id=uuid.uuid4(),
        )
        assert updated.name == "Stark Global"
        assert updated.settings["max_upload_size_mb"] == 100

        archived = await service.delete_organization(
            async_test_db, org.id, caller_user_id=uuid.uuid4()
        )
        assert archived is True


class TestDepartmentAndTeamServicesUnit:
    """Tests DepartmentService and TeamService operations."""

    @pytest.mark.asyncio
    async def test_department_lifecycle_and_uniqueness(self, async_test_db: AsyncSession):
        org_service = OrganizationService()
        dept_service = DepartmentService()

        org = await org_service.create_organization(
            async_test_db, OrganizationCreate(name="Umbrella Corp", domain="umbrella.com")
        )

        dept = await dept_service.create_department(
            async_test_db,
            org.id,
            DepartmentCreate(name="Research & Development", description="Bio research"),
            caller_user_id=uuid.uuid4(),
        )
        assert dept.name == "Research & Development"

        # Unique name per org check
        with pytest.raises(ConflictException) as exc:
            await dept_service.create_department(
                async_test_db,
                org.id,
                DepartmentCreate(name="Research & Development"),
                caller_user_id=uuid.uuid4(),
            )
        assert exc.value.code == ErrorCode.DEPT_NAME_EXISTS

        # List departments
        depts = await dept_service.list_departments(async_test_db, org.id)
        assert len(depts) == 1

        # Delete department
        deleted = await dept_service.delete_department(
            async_test_db, org.id, dept.id, caller_user_id=uuid.uuid4()
        )
        assert deleted is True

    @pytest.mark.asyncio
    async def test_team_lifecycle_and_department_scoping(self, async_test_db: AsyncSession):
        org_service = OrganizationService()
        dept_service = DepartmentService()
        team_service = TeamService()

        org = await org_service.create_organization(
            async_test_db, OrganizationCreate(name="Cyberdyne", domain="cyberdyne.com")
        )
        dept = await dept_service.create_department(
            async_test_db,
            org.id,
            DepartmentCreate(name="Engineering"),
            caller_user_id=uuid.uuid4(),
        )

        team = await team_service.create_team(
            async_test_db,
            org.id,
            TeamCreate(name="AI Systems", department_id=dept.id),
            caller_user_id=uuid.uuid4(),
        )
        assert team.name == "AI Systems"
        assert team.department_id == dept.id

        teams = await team_service.list_teams(async_test_db, org.id, department_id=dept.id)
        assert len(teams) == 1

        # Invalid department rejection
        fake_dept_id = uuid.uuid4()
        with pytest.raises(NotFoundException) as exc:
            await team_service.create_team(
                async_test_db,
                org.id,
                TeamCreate(name="Robotics", department_id=fake_dept_id),
                caller_user_id=uuid.uuid4(),
            )
        assert exc.value.code == ErrorCode.DEPT_NOT_FOUND


class TestInvitationAndMemberServicesUnit:
    """Tests InvitationService and MemberService onboarding workflows."""

    @pytest.mark.asyncio
    async def test_invitation_lifecycle_and_account_acceptance(self, async_test_db: AsyncSession):
        org_service = OrganizationService()
        inv_service = InvitationService()
        member_service = MemberService()

        org = await org_service.create_organization(
            async_test_db, OrganizationCreate(name="Initech", domain="initech.com")
        )
        inviter_id = uuid.uuid4()

        # Send invitation
        inv = await inv_service.create_invitation(
            async_test_db,
            org.id,
            InvitationCreate(email="peter.gibbons@initech.com", role="Member"),
            caller_user_id=inviter_id,
        )
        assert inv.status == "PENDING"
        assert inv.email == "peter.gibbons@initech.com"

        # List invitations
        pending = await inv_service.list_invitations(async_test_db, org.id)
        assert len(pending) == 1

        # Accept invitation
        accepted = await inv_service.accept_invitation(
            async_test_db,
            InvitationAccept(
                token=inv.token,
                full_name="Peter Gibbons",
                password="TPSReportsPassword123!",
            ),
        )
        assert accepted["accepted"] is True
        assert accepted["email"] == "peter.gibbons@initech.com"

        # Verify member directory
        members = await member_service.list_members(async_test_db, org.id)
        assert members.total == 1
        assert members.items[0].full_name == "Peter Gibbons"
        assert members.items[0].role == "Member"

        # Update member
        user_id = members.items[0].id
        updated_member = await member_service.update_member(
            async_test_db,
            org.id,
            user_id,
            MemberUpdate(role="ProjectManager"),
            caller_user_id=inviter_id,
        )
        assert updated_member.role == "ProjectManager"

        # Second accept of same token must be rejected
        with pytest.raises(ConflictException) as exc:
            await inv_service.accept_invitation(
                async_test_db,
                InvitationAccept(
                    token=inv.token,
                    full_name="Peter Gibbons",
                    password="TPSReportsPassword123!",
                ),
            )
        assert exc.value.code == ErrorCode.INVITATION_ALREADY_ACCEPTED
