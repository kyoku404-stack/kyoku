"""Database Seeding Integration Test Suite.

Validates seed data generation, completeness of default dataset including Phase 1.5
organizational hierarchy and user invitations, and idempotency when running multiple times.
"""

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.db.base import Base
from backend.app.db.seed import (
    DEPT_ENG_ID,
    INVITE_DEV_ID,
    ORG_ID,
    TEAM_ENG_ID,
    USER_ADMIN_ID,
    seed_database,
)
from backend.app.models.department import Department
from backend.app.models.document import Document
from backend.app.models.invitation import Invitation
from backend.app.models.knowledge import DocumentChunk, KgEntity, KgRelationship
from backend.app.models.organization import Organization
from backend.app.models.team import Team
from backend.app.models.user import User

TEST_SQLITE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def seed_session():
    """Provides an in-memory SQLite async test database for seeding tests."""
    engine = create_async_engine(TEST_SQLITE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


class TestDatabaseSeeding:
    """Validates KEEP development seed data generator."""

    @pytest.mark.asyncio
    async def test_initial_seed_creation(self, seed_session: AsyncSession):
        """Validates that seed_database populates all required entities including Phase 1.5 hierarchy."""
        counts = await seed_database(seed_session)

        # Verify reported creation counts
        assert counts["organizations"] == 1
        assert counts["departments"] == 4
        assert counts["teams"] == 3
        assert counts["users"] == 4
        assert counts["invitations"] == 3
        assert counts["projects"] == 3
        assert counts["documents"] == 3
        assert counts["chunks"] == 6
        assert counts["meetings"] == 2
        assert counts["tasks"] == 4
        assert counts["chat_sessions"] == 2
        assert counts["chat_messages"] == 4
        assert counts["kg_entities"] == 4
        assert counts["kg_relationships"] == 2
        assert counts["activity_logs"] == 7

        # Direct database queries verifying organization
        org_res = await seed_session.execute(select(Organization).where(Organization.id == ORG_ID))
        org = org_res.scalar_one_or_none()
        assert org is not None
        assert org.name == "Acme Enterprise"
        assert org.domain == "acme.corp"
        assert org.industry == "Information Technology"
        assert org.settings_json is not None

        # Direct database queries verifying departments
        dept_count_res = await seed_session.execute(select(func.count(Department.id)))
        assert dept_count_res.scalar_one() == 4

        eng_dept = (await seed_session.execute(select(Department).where(Department.id == DEPT_ENG_ID))).scalar_one_or_none()
        assert eng_dept is not None
        assert eng_dept.name == "Engineering"

        # Verify teams are linked to departments
        eng_team = (await seed_session.execute(select(Team).where(Team.id == TEAM_ENG_ID))).scalar_one_or_none()
        assert eng_team is not None
        assert eng_team.department_id == DEPT_ENG_ID

        # Verify invitations
        invite_count_res = await seed_session.execute(select(func.count(Invitation.id)))
        assert invite_count_res.scalar_one() == 3

        dev_invite = (await seed_session.execute(select(Invitation).where(Invitation.id == INVITE_DEV_ID))).scalar_one_or_none()
        assert dev_invite is not None
        assert dev_invite.email == "pending.dev@acme.corp"
        assert dev_invite.status == "PENDING"
        assert dev_invite.department_id == DEPT_ENG_ID

        # Verify SuperAdmin user
        admin_res = await seed_session.execute(select(User).where(User.id == USER_ADMIN_ID))
        admin = admin_res.scalar_one_or_none()
        assert admin is not None
        assert admin.email == "admin@keep.local"
        assert admin.role == "SuperAdmin"

        # Verify Documents & Chunks
        doc_count_res = await seed_session.execute(select(func.count(Document.id)))
        assert doc_count_res.scalar_one() == 3

        chunk_count_res = await seed_session.execute(select(func.count(DocumentChunk.id)))
        assert chunk_count_res.scalar_one() == 6

        # Verify Knowledge Graph
        kg_res = await seed_session.execute(select(KgEntity))
        assert len(kg_res.scalars().all()) == 4

        rel_res = await seed_session.execute(select(KgRelationship))
        assert len(rel_res.scalars().all()) == 2

    @pytest.mark.asyncio
    async def test_seed_idempotency(self, seed_session: AsyncSession):
        """Validates that executing seed_database twice does not duplicate records or fail."""
        # First execution
        first_counts = await seed_database(seed_session)
        assert first_counts["organizations"] == 1
        assert first_counts["departments"] == 4
        assert first_counts["invitations"] == 3

        # Second execution on same database
        second_counts = await seed_database(seed_session)
        assert second_counts["organizations"] == 0
        assert second_counts["departments"] == 0
        assert second_counts["teams"] == 0
        assert second_counts["users"] == 0
        assert second_counts["invitations"] == 0
        assert second_counts["projects"] == 0
        assert second_counts["documents"] == 0

        # Verify totals in database remain unchanged
        org_count = (await seed_session.execute(select(func.count(Organization.id)))).scalar_one()
        dept_count = (await seed_session.execute(select(func.count(Department.id)))).scalar_one()
        user_count = (await seed_session.execute(select(func.count(User.id)))).scalar_one()
        inv_count = (await seed_session.execute(select(func.count(Invitation.id)))).scalar_one()

        assert org_count == 1
        assert dept_count == 4
        assert user_count == 4
        assert inv_count == 3
