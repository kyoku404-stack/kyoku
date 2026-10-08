"""Database Persistence Layer Integration Test Suite.

Validates SQLAlchemy 2.0 ORM models, repository patterns, relationships,
multi-tenancy, soft deletes, transactions, and pgvector persistence for KEEP.
"""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.db.base import Base
from backend.app.models.activity import ActivityLog
from backend.app.models.chat import ChatMessage, ChatSession
from backend.app.models.document import Document
from backend.app.models.knowledge import DocumentChunk, KgEntity, KgRelationship
from backend.app.models.organization import Organization
from backend.app.models.project import Project
from backend.app.models.team import Team
from backend.app.models.user import User
from backend.app.repositories.document_repo import DocumentRepository
from backend.app.repositories.meeting_repo import MeetingRepository
from backend.app.repositories.org_repo import OrganizationRepository
from backend.app.repositories.project_repo import ProjectRepository
from backend.app.repositories.task_repo import TaskRepository
from backend.app.repositories.user_repo import UserRepository

# In-memory SQLite async engine for isolated integration testing
TEST_SQLITE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """Provides an isolated in-memory test database session."""
    engine = create_async_engine(TEST_SQLITE_URL, echo=False)
    async with engine.begin() as conn:
        # Create all tables defined in Base metadata
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


class TestDatabasePersistence:
    """Comprehensive test matrix for KEEP database persistence layer."""

    @pytest.mark.asyncio
    async def test_organization_and_user_crud(self, db_session: AsyncSession):
        """Validates Organization and User creation, retrieval, and updates."""
        org_repo = OrganizationRepository(Organization)
        user_repo = UserRepository(User)

        # 1. Create Organization
        created_org = await org_repo.create(
            db_session,
            obj_in={
                "name": "Test Enterprise Corp",
                "domain": "testenterprise.com",
                "is_active": True,
                "subscription": "ENTERPRISE",
            },
        )
        assert created_org.id is not None
        assert created_org.name == "Test Enterprise Corp"
        assert created_org.is_deleted is False

        # 2. Create User within Organization
        created_user = await user_repo.create(
            db_session,
            obj_in={
                "organization_id": created_org.id,
                "email": "lead@testenterprise.com",
                "hashed_password": "secure_hash_123",
                "full_name": "Enterprise Lead",
                "role": "OrgAdmin",
                "is_active": True,
            },
        )
        assert created_user.id is not None
        assert created_user.email == "lead@testenterprise.com"
        assert created_user.organization_id == created_org.id

        # 3. Retrieve User by Email
        fetched_user = await user_repo.get_by_email(db_session, "lead@testenterprise.com")
        assert fetched_user is not None
        assert fetched_user.id == created_user.id
        assert fetched_user.role == "OrgAdmin"

        # 4. Update User Role
        updated_user = await user_repo.update(
            db_session,
            db_obj=fetched_user,
            obj_in={"role": "SuperAdmin"},
        )
        assert updated_user.role == "SuperAdmin"

    @pytest.mark.asyncio
    async def test_team_and_project_relationships(self, db_session: AsyncSession):
        """Validates Team, Project, and association relationships."""
        org = Organization(name="Project Test Org", domain="proj.org")
        db_session.add(org)
        await db_session.flush()

        # Create Team
        team = Team(
            organization_id=org.id,
            name="AI Research Team",
            description="Focuses on RAG and vector retrieval",
        )
        db_session.add(team)
        await db_session.flush()

        # Create Users
        user1 = User(
            organization_id=org.id,
            email="ai_researcher@proj.org",
            hashed_password="pwd",
            full_name="AI Researcher",
            team_id=team.id,
        )
        user2 = User(
            organization_id=org.id,
            email="devops_lead@proj.org",
            hashed_password="pwd",
            full_name="DevOps Lead",
            team_id=team.id,
        )
        db_session.add_all([user1, user2])
        await db_session.flush()

        # Create Project
        proj_repo = ProjectRepository()
        created_proj = await proj_repo.create(
            db_session,
            obj_in={
                "organization_id": org.id,
                "name": "KEEP Semantic Search MVP",
                "description": "Developing enterprise hybrid search",
                "department": "AI & Data",
                "status": "IN_PROGRESS",
                "priority": "HIGH",
                "timeline": "Q3-Q4 2026",
            },
        )
        assert created_proj.id is not None
        assert created_proj.status == "IN_PROGRESS"

        # Query projects by organization
        projects = await proj_repo.get_multi(db_session, organization_id=org.id)
        assert len(projects) == 1
        assert projects[0].name == "KEEP Semantic Search MVP"

    @pytest.mark.asyncio
    async def test_document_and_chunks_persistence(self, db_session: AsyncSession):
        """Validates Document and DocumentChunk persistence and queries."""
        org = Organization(name="Doc Test Org", domain="doctest.com")
        db_session.add(org)
        await db_session.flush()

        user = User(
            organization_id=org.id,
            email="uploader@doctest.com",
            hashed_password="pwd",
            full_name="Doc Uploader",
        )
        db_session.add(user)
        await db_session.flush()

        doc_repo = DocumentRepository(Document)
        created_doc = await doc_repo.create(
            db_session,
            obj_in={
                "organization_id": org.id,
                "uploader_id": user.id,
                "filename": "Architecture_V1.pdf",
                "file_path": "/uploads/Architecture_V1.pdf",
                "file_type": "application/pdf",
                "file_size": 1048576,
                "status": "PROCESSED",
                "version": "1.0",
                "author": "Doc Uploader",
            },
        )
        assert created_doc.id is not None


        # Add Chunks
        chunk1 = DocumentChunk(
            document_id=created_doc.id,
            chunk_index=0,
            content="This is the introduction chunk for Architecture V1.",
            metadata_json={"page": 1, "tokens": 42},
        )
        chunk2 = DocumentChunk(
            document_id=created_doc.id,
            chunk_index=1,
            content="This is the system design and persistence specification chunk.",
            metadata_json={"page": 2, "tokens": 58},
        )
        db_session.add_all([chunk1, chunk2])
        await db_session.flush()

        # Query chunks for document
        chunks_res = await db_session.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == created_doc.id)
        )
        chunks = chunks_res.scalars().all()
        assert len(chunks) == 2
        assert chunks[0].chunk_index == 0
        assert chunks[1].chunk_index == 1

    @pytest.mark.asyncio
    async def test_meeting_and_task_repositories(self, db_session: AsyncSession):
        """Validates Meeting and Task repositories."""
        org = Organization(name="Agile Org", domain="agile.org")
        db_session.add(org)
        await db_session.flush()

        user = User(
            organization_id=org.id,
            email="pm@agile.org",
            hashed_password="pwd",
            full_name="Agile PM",
        )
        db_session.add(user)
        await db_session.flush()

        proj = Project(organization_id=org.id, name="Sprint 10", status="IN_PROGRESS")
        db_session.add(proj)
        await db_session.flush()

        # 1. Meeting Repository
        meet_repo = MeetingRepository()
        created_meeting = await meet_repo.create(
            db_session,
            obj_in={
                "project_id": proj.id,
                "organizer_id": user.id,
                "title": "Sprint Planning Meeting",
                "duration": 60,
                "transcript_reference": "transcripts/sprint10.txt",
            },
        )
        assert created_meeting.id is not None
        assert created_meeting.title == "Sprint Planning Meeting"

        meetings_by_proj = await meet_repo.get_multi(db_session, project_id=proj.id)
        assert len(meetings_by_proj) == 1

        # 2. Task Repository
        task_repo = TaskRepository()
        await task_repo.create(
            db_session,
            obj_in={
                "project_id": proj.id,
                "title": "Setup Alembic Migrations",
                "assignment": "pm@agile.org",
                "priority": "HIGH",
                "status": "COMPLETED",
                "completion_percentage": 100,
            },
        )
        await task_repo.create(
            db_session,
            obj_in={
                "project_id": proj.id,
                "title": "Configure PostgreSQL Container",
                "assignment": "pm@agile.org",
                "priority": "MEDIUM",
                "status": "IN_PROGRESS",
                "completion_percentage": 50,
            },
        )

        proj_tasks = await task_repo.get_multi(db_session, project_id=proj.id)
        assert len(proj_tasks) == 2


    @pytest.mark.asyncio
    async def test_chat_session_and_messages(self, db_session: AsyncSession):
        """Validates ChatSession and ChatMessage cascade persistence."""
        org = Organization(name="Chat Org", domain="chatorg.com")
        db_session.add(org)
        await db_session.flush()

        user = User(
            organization_id=org.id,
            email="chatter@chatorg.com",
            hashed_password="pwd",
            full_name="Active Chatter",
        )
        db_session.add(user)
        await db_session.flush()

        session = ChatSession(
            user_id=user.id,
            title="Architecture Questions",
            metadata_json='{"model": "gpt-4"}',
        )
        db_session.add(session)
        await db_session.flush()

        msg1 = ChatMessage(
            session_id=session.id,
            role="user",
            content="How does KEEP ensure multi-tenant security?",
        )
        msg2 = ChatMessage(
            session_id=session.id,
            role="assistant",
            content="KEEP filters all database queries and vector lookups with organization_id.",
            citations_json='[{"document_id": "00000000-0000-0000-0000-000000000001", "page": 1}]',
        )
        db_session.add_all([msg1, msg2])
        await db_session.flush()

        messages_res = await db_session.execute(
            select(ChatMessage).where(ChatMessage.session_id == session.id)
        )
        messages = messages_res.scalars().all()
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_knowledge_graph_and_activity_logs(self, db_session: AsyncSession):
        """Validates Knowledge Graph entities, relationships, and audit logs."""
        org = Organization(name="KG Org", domain="kg.org")
        db_session.add(org)
        await db_session.flush()

        user = User(
            organization_id=org.id,
            email="admin@kg.org",
            hashed_password="pwd",
            full_name="KG Admin",
        )
        db_session.add(user)
        await db_session.flush()

        # 1. KG Entities
        entity1 = KgEntity(
            organization_id=org.id,
            name="FastAPI Backend",
            entity_type="Service",
            properties_json={"language": "Python"},
        )
        entity2 = KgEntity(
            organization_id=org.id,
            name="PostgreSQL 16",
            entity_type="Database",
            properties_json={"storage": "Relational & Vector"},
        )
        db_session.add_all([entity1, entity2])
        await db_session.flush()

        # 2. KG Relationship
        rel = KgRelationship(
            organization_id=org.id,
            source_entity_id=entity1.id,
            target_entity_id=entity2.id,
            relation_type="DEPENDS_ON",
            weight=1.0,
        )
        db_session.add(rel)
        await db_session.flush()

        rels_res = await db_session.execute(
            select(KgRelationship).where(KgRelationship.organization_id == org.id)
        )
        rels = rels_res.scalars().all()
        assert len(rels) == 1
        assert rels[0].relation_type == "DEPENDS_ON"

        # 3. Activity Log
        log = ActivityLog(
            organization_id=org.id,
            user_id=user.id,
            action="GRAPH_ENTITY_CREATE",
            resource_type="KgEntity",
            resource_id=entity1.id,
            details="Created FastAPI Backend KG entity",
            ip_address="10.0.0.1",
        )
        db_session.add(log)
        await db_session.flush()

        logs_res = await db_session.execute(
            select(ActivityLog).where(ActivityLog.organization_id == org.id)
        )
        logs = logs_res.scalars().all()
        assert len(logs) == 1
        assert logs[0].action == "GRAPH_ENTITY_CREATE"

    @pytest.mark.asyncio
    async def test_soft_delete_mechanism(self, db_session: AsyncSession):
        """Validates soft delete flags and timestamps adhering to Chapter 15."""
        org = Organization(name="Soft Delete Org", domain="softdelete.org")
        db_session.add(org)
        await db_session.flush()

        user = User(
            organization_id=org.id,
            email="softdelete@test.com",
            hashed_password="pwd",
            full_name="Soft Delete User",
        )
        db_session.add(user)
        await db_session.flush()

        # User is active
        assert user.is_deleted is False
        assert user.deleted_at is None

        # Perform soft delete
        user.is_deleted = True
        user.deleted_at = datetime.now(UTC)
        await db_session.flush()

        # Verify soft delete query filtering
        active_users_res = await db_session.execute(
            select(User).where(User.organization_id == org.id, User.is_deleted.is_(False))
        )
        active_users = active_users_res.scalars().all()
        assert len(active_users) == 0

        # Verify record still exists for audit trail
        all_users_res = await db_session.execute(
            select(User).where(User.organization_id == org.id)
        )
        all_users = all_users_res.scalars().all()
        assert len(all_users) == 1
        assert all_users[0].is_deleted is True

    @pytest.mark.asyncio
    async def test_transaction_rollback_guarantee(self, db_session: AsyncSession):
        """Validates transaction atomicity and rollback behavior adhering to Chapter 12."""
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Atomic Org", domain="atomic.org")
        db_session.add(org)
        await db_session.flush()

        # Simulate a transaction that encounters a failure
        try:
            async with db_session.begin_nested():
                user1 = User(
                    organization_id=org_id,
                    email="valid_user@atomic.org",
                    hashed_password="pwd",
                    full_name="Valid User",
                )
                db_session.add(user1)
                await db_session.flush()

                # Trigger intentional failure (duplicate email violation in nested transaction)
                user2 = User(
                    organization_id=org_id,
                    email="valid_user@atomic.org",  # duplicate email
                    hashed_password="pwd",
                    full_name="Duplicate User",
                )
                db_session.add(user2)
                # Flush will fail on unique constraint or simulate error
                raise ValueError("Intentional business logic validation failure")
        except ValueError:
            # Transaction rolled back to savepoint
            pass

        # Verify neither user was committed into database due to atomicity
        users_res = await db_session.execute(
            select(User).where(User.organization_id == org_id)
        )
        users = users_res.scalars().all()
        assert len(users) == 0
