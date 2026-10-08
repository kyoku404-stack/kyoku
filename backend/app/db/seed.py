"""Database Seed Data Generator.

Provides idempotent initial development and testing dataset for KEEP adhering
to Chapter 16 of devdocs/p1/p1.3.txt.
"""

import asyncio
import logging
import uuid

from backend.app.core.security import get_password_hash
from backend.app.db.session import async_session_factory
from backend.app.models.activity import ActivityLog
from backend.app.models.chat import ChatMessage, ChatSession
from backend.app.models.document import Document
from backend.app.models.knowledge import DocumentChunk, KgEntity, KgRelationship
from backend.app.models.meeting import Meeting
from backend.app.models.organization import Organization
from backend.app.models.project import Project
from backend.app.models.task import Task
from backend.app.models.team import Team
from backend.app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("keep.seed")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Deterministic Seed UUIDs for consistent testing and references
ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TEAM_ENG_ID = uuid.UUID("00000000-0000-0000-0000-000000000011")
TEAM_AI_ID = uuid.UUID("00000000-0000-0000-0000-000000000012")
TEAM_OPS_ID = uuid.UUID("00000000-0000-0000-0000-000000000013")

USER_ADMIN_ID = uuid.UUID("00000000-0000-0000-0000-000000000021")
USER_MANAGER_ID = uuid.UUID("00000000-0000-0000-0000-000000000022")
USER_DEV_ID = uuid.UUID("00000000-0000-0000-0000-000000000023")
USER_GUEST_ID = uuid.UUID("00000000-0000-0000-0000-000000000024")

PROJ_MVP_ID = uuid.UUID("00000000-0000-0000-0000-000000000031")
PROJ_SEARCH_ID = uuid.UUID("00000000-0000-0000-0000-000000000032")
PROJ_INSIGHTS_ID = uuid.UUID("00000000-0000-0000-0000-000000000033")

DOC_ROADMAP_ID = uuid.UUID("00000000-0000-0000-0000-000000000041")
DOC_ARCH_ID = uuid.UUID("00000000-0000-0000-0000-000000000042")
DOC_POLICY_ID = uuid.UUID("00000000-0000-0000-0000-000000000043")


def generate_dummy_embedding(dim: int = 1536, seed_val: float = 0.05) -> list[float]:
    """Generates a normalized dummy embedding vector for seeding."""
    vec = [seed_val] * dim
    return vec


async def seed_database(session: AsyncSession) -> dict[str, int]:
    """Seed the database with default enterprise records.
    
    Idempotent: skips existing records to avoid unique constraint violations.
    """
    counts = {
        "organizations": 0,
        "teams": 0,
        "users": 0,
        "projects": 0,
        "documents": 0,
        "chunks": 0,
        "meetings": 0,
        "tasks": 0,
        "chat_sessions": 0,
        "chat_messages": 0,
        "kg_entities": 0,
        "kg_relationships": 0,
        "activity_logs": 0,
    }

    # 1. Default Organization
    org_res = await session.execute(select(Organization).where(Organization.id == ORG_ID))
    org = org_res.scalar_one_or_none()
    if not org:
        org = Organization(
            id=ORG_ID,
            name="Acme Enterprise",
            domain="acme.corp",
            is_active=True,
            subscription="ENTERPRISE",
        )
        session.add(org)
        await session.flush()
        counts["organizations"] += 1
        logger.info("Seeded default organization: %s", org.name)

    # 2. Teams
    teams_data = [
        (TEAM_ENG_ID, "Engineering", "Core platform and infrastructure engineering team"),
        (TEAM_AI_ID, "Product & AI", "AI research, RAG pipeline, and intelligence team"),
        (TEAM_OPS_ID, "Operations", "DevOps, SRE, security, and enterprise compliance team"),
    ]
    for team_id, name, desc in teams_data:
        team_res = await session.execute(select(Team).where(Team.id == team_id))
        if not team_res.scalar_one_or_none():
            team = Team(id=team_id, organization_id=ORG_ID, name=name, description=desc)
            session.add(team)
            counts["teams"] += 1
    await session.flush()

    # 3. Users
    default_password_hash = get_password_hash("Password123!")
    users_data = [
        (USER_ADMIN_ID, "admin@keep.local", "Admin User", "SuperAdmin", TEAM_OPS_ID),
        (USER_MANAGER_ID, "manager@keep.local", "Project Manager", "Manager", TEAM_AI_ID),
        (USER_DEV_ID, "engineer@keep.local", "Senior Engineer", "Member", TEAM_ENG_ID),
        (USER_GUEST_ID, "guest@keep.local", "Guest Contributor", "Guest", None),
    ]
    for user_id, email, name, role, team_id in users_data:
        user_res = await session.execute(select(User).where(User.email == email))
        if not user_res.scalar_one_or_none():
            user = User(
                id=user_id,
                organization_id=ORG_ID,
                email=email,
                hashed_password=default_password_hash,
                full_name=name,
                role=role,
                is_active=True,
                team_id=team_id,
            )
            session.add(user)
            counts["users"] += 1
    await session.flush()

    # 4. Projects
    projects_data = [
        (
            PROJ_MVP_ID,
            "Knowledge Discovery MVP",
            "Core semantic search and enterprise RAG question answering prototype",
            "AI & Data",
            "IN_PROGRESS",
            "HIGH",
            "Q3 2026 - Q4 2026",
        ),
        (
            PROJ_SEARCH_ID,
            "Enterprise Search & Retrieval",
            "Hybrid vector + BM25 full text search across multi-tenant documents",
            "Engineering",
            "PLANNED",
            "MEDIUM",
            "Q4 2026",
        ),
        (
            PROJ_INSIGHTS_ID,
            "Executive Insights Engine",
            "Predictive analytics and automated summary dashboards for leadership",
            "Executive",
            "IN_PROGRESS",
            "HIGH",
            "Q1 2027",
        ),
    ]
    for proj_id, name, desc, dept, status, priority, timeline in projects_data:
        proj_res = await session.execute(select(Project).where(Project.id == proj_id))
        if not proj_res.scalar_one_or_none():
            proj = Project(
                id=proj_id,
                organization_id=ORG_ID,
                name=name,
                description=desc,
                department=dept,
                status=status,
                priority=priority,
                timeline=timeline,
            )
            session.add(proj)
            counts["projects"] += 1
    await session.flush()

    # 5. Documents & Document Chunks
    docs_data = [
        (
            DOC_ROADMAP_ID,
            "Q3_Strategic_Roadmap.pdf",
            "/app/uploads/Q3_Strategic_Roadmap.pdf",
            "application/pdf",
            1048576,
            "PROCESSED",
            "1.0",
            "Admin User",
            USER_ADMIN_ID,
            PROJ_MVP_ID,
        ),
        (
            DOC_ARCH_ID,
            "KEEP_System_Architecture.pdf",
            "/app/uploads/KEEP_System_Architecture.pdf",
            "application/pdf",
            2097152,
            "PROCESSED",
            "1.2",
            "Lead Architect",
            USER_DEV_ID,
            PROJ_MVP_ID,
        ),
        (
            DOC_POLICY_ID,
            "HR_Compliance_Policy.docx",
            "/app/uploads/HR_Compliance_Policy.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            524288,
            "PROCESSED",
            "2.0",
            "HR Department",
            USER_ADMIN_ID,
            None,
        ),
    ]
    for doc_id, fname, fpath, ftype, fsize, status, ver, author, uploader_id, proj_id in docs_data:
        doc_res = await session.execute(select(Document).where(Document.id == doc_id))
        if not doc_res.scalar_one_or_none():
            doc = Document(
                id=doc_id,
                organization_id=ORG_ID,
                uploader_id=uploader_id,
                project_id=proj_id,
                filename=fname,
                file_path=fpath,
                file_type=ftype,
                file_size=fsize,
                status=status,
                version=ver,
                author=author,
            )
            session.add(doc)
            counts["documents"] += 1

            # Seed 2 chunks for each document
            chunk1 = DocumentChunk(
                id=uuid.uuid4(),
                document_id=doc_id,
                chunk_index=0,
                content=f"Executive overview of {fname}. Details core milestones, strategic imperatives, and timelines.",
                embedding=generate_dummy_embedding(1536, seed_val=0.01),
                metadata_json={"page": 1, "section": "Executive Summary", "confidence": 0.98},
            )
            chunk2 = DocumentChunk(
                id=uuid.uuid4(),
                document_id=doc_id,
                chunk_index=1,
                content=f"Technical architectural specifications and requirements for {fname}.",
                embedding=generate_dummy_embedding(1536, seed_val=0.02),
                metadata_json={"page": 2, "section": "Technical Specifications", "confidence": 0.95},
            )
            session.add_all([chunk1, chunk2])
            counts["chunks"] += 2
    await session.flush()

    # 6. Meetings
    meetings_data = [
        (
            PROJ_MVP_ID,
            USER_ADMIN_ID,
            "Weekly AI Knowledge Sync",
            "Discuss hybrid retrieval accuracy, BM25 tuning, and pgvector HNSW indexing performance.",
            "rec_sync_2026_09_28",
            45,
        ),
        (
            PROJ_MVP_ID,
            USER_MANAGER_ID,
            "Architecture Review Board",
            "Approval of Phase 1.3 database persistence schemas and migration rollout strategy.",
            "rec_arb_2026_10_01",
            60,
        ),
    ]
    for proj_id, org_user_id, title, desc, rec, duration in meetings_data:
        meet_res = await session.execute(
            select(Meeting).where(Meeting.title == title, Meeting.project_id == proj_id)
        )
        if not meet_res.scalar_one_or_none():
            meeting = Meeting(
                id=uuid.uuid4(),
                project_id=proj_id,
                organizer_id=org_user_id,
                title=title,
                metadata_json=desc,
                transcript_reference=f"transcripts/{rec}.txt",
                recording=f"recordings/{rec}.mp4",
                duration=duration,
            )
            session.add(meeting)
            counts["meetings"] += 1
    await session.flush()

    # 7. Tasks
    tasks_data = [
        (PROJ_MVP_ID, "Implement pgvector HNSW Indexing", "engineer@keep.local", "HIGH", "COMPLETED", 100),
        (PROJ_MVP_ID, "Validate Multi-Tenant RBAC & Tenancy Barriers", "admin@keep.local", "HIGH", "IN_PROGRESS", 75),
        (PROJ_MVP_ID, "Complete Seed Data Automation & CI Checks", "engineer@keep.local", "MEDIUM", "COMPLETED", 100),
        (PROJ_SEARCH_ID, "Evaluate BM25 vs Reciprocal Rank Fusion", "manager@keep.local", "MEDIUM", "PENDING", 0),
    ]
    for proj_id, title, assign, priority, status, comp in tasks_data:
        task_res = await session.execute(
            select(Task).where(Task.title == title, Task.project_id == proj_id)
        )
        if not task_res.scalar_one_or_none():
            task = Task(
                id=uuid.uuid4(),
                project_id=proj_id,
                title=title,
                assignment=assign,
                priority=priority,
                status=status,
                completion_percentage=comp,
            )
            session.add(task)
            counts["tasks"] += 1
    await session.flush()

    # 8. Chat Sessions & Messages
    chat_sessions_data = [
        (
            USER_ADMIN_ID,
            "Strategic Milestones Overview",
            "Session inquiring about Q3 and Q4 strategic deliverables.",
            [
                ("user", "What are the primary deliverables for the Knowledge Discovery MVP?"),
                ("assistant", "The Knowledge Discovery MVP deliverables include hybrid vector search, citation provenance tracking, and multi-tenant security isolation [Doc 1, Page 1]."),
            ],
        ),
        (
            USER_DEV_ID,
            "Database Schema Inquiries",
            "Session regarding PostgreSQL 16 pgvector indexing.",
            [
                ("user", "How does KEEP manage vector embeddings in the relational store?"),
                ("assistant", "KEEP utilizes PostgreSQL 16 with the pgvector extension, storing 1536-dimensional embeddings with cosine distance indexing for hybrid search [Doc 2, Page 2]."),
            ],
        ),
    ]
    for user_id, title, meta, msgs in chat_sessions_data:
        sess_res = await session.execute(
            select(ChatSession).where(ChatSession.title == title, ChatSession.user_id == user_id)
        )
        session_obj = sess_res.scalar_one_or_none()
        if not session_obj:
            session_obj = ChatSession(
                id=uuid.uuid4(),
                user_id=user_id,
                title=title,
                metadata_json=meta,
            )
            session.add(session_obj)
            await session.flush()
            counts["chat_sessions"] += 1

            for role, content in msgs:
                msg = ChatMessage(
                    id=uuid.uuid4(),
                    session_id=session_obj.id,
                    role=role,
                    content=content,
                    citations_json='[{"document_id": "00000000-0000-0000-0000-000000000041", "page": 1}]',
                )
                session.add(msg)
                counts["chat_messages"] += 1
    await session.flush()

    # 9. Knowledge Graph Entities & Relationships
    kg_entities_data = [
        ("Knowledge Discovery MVP", "Project", {"department": "AI & Data", "priority": "HIGH"}),
        ("Acme Enterprise", "Organization", {"domain": "acme.corp"}),
        ("KEEP System Architecture", "Document", {"type": "Architecture Blueprint"}),
        ("Admin User", "Person", {"role": "SuperAdmin"}),
    ]
    created_entities: dict[str, KgEntity] = {}
    for name, etype, props in kg_entities_data:
        ent_res = await session.execute(
            select(KgEntity).where(KgEntity.name == name, KgEntity.organization_id == ORG_ID)
        )
        entity = ent_res.scalar_one_or_none()
        if not entity:
            entity = KgEntity(
                id=uuid.uuid4(),
                organization_id=ORG_ID,
                name=name,
                entity_type=etype,
                properties_json=props,
            )
            session.add(entity)
            counts["kg_entities"] += 1
        created_entities[name] = entity
    await session.flush()

    # Knowledge Graph Relationships
    if (
        "Admin User" in created_entities
        and "KEEP System Architecture" in created_entities
        and "Knowledge Discovery MVP" in created_entities
    ):
        rel_data = [
            (created_entities["Admin User"].id, created_entities["KEEP System Architecture"].id, "AUTHOR_OF", 1.0),
            (created_entities["KEEP System Architecture"].id, created_entities["Knowledge Discovery MVP"].id, "DEPENDS_ON", 1.0),
        ]
        for src_id, tgt_id, rel_type, weight in rel_data:
            rel_res = await session.execute(
                select(KgRelationship).where(
                    KgRelationship.source_entity_id == src_id,
                    KgRelationship.target_entity_id == tgt_id,
                    KgRelationship.relation_type == rel_type,
                )
            )
            if not rel_res.scalar_one_or_none():
                rel = KgRelationship(
                    id=uuid.uuid4(),
                    organization_id=ORG_ID,
                    source_entity_id=src_id,
                    target_entity_id=tgt_id,
                    relation_type=rel_type,
                    weight=weight,
                )
                session.add(rel)
                counts["kg_relationships"] += 1
    await session.flush()

    # 10. Activity Logs
    activity_data = [
        (USER_ADMIN_ID, "AUTH_LOGIN", "User", USER_ADMIN_ID, "SuperAdmin logged into management dashboard", "127.0.0.1"),
        (USER_ADMIN_ID, "DOCUMENT_UPLOAD", "Document", DOC_ROADMAP_ID, "Uploaded Q3_Strategic_Roadmap.pdf", "127.0.0.1"),
        (USER_DEV_ID, "DOCUMENT_UPLOAD", "Document", DOC_ARCH_ID, "Uploaded KEEP_System_Architecture.pdf", "192.168.1.50"),
    ]
    for user_id, action, rtype, rid, details, ip in activity_data:
        log = ActivityLog(
            id=uuid.uuid4(),
            organization_id=ORG_ID,
            user_id=user_id,
            action=action,
            resource_type=rtype,
            resource_id=rid,
            details=details,
            ip_address=ip,
        )
        session.add(log)
        counts["activity_logs"] += 1

    await session.commit()
    logger.info("Database seeding completed successfully. Created entities: %s", counts)
    return counts


async def main() -> None:
    """CLI Entrypoint for seeding database."""
    logger.info("Starting KEEP database seeding...")
    async with async_session_factory() as session:
        counts = await seed_database(session)
    logger.info("Seeding summary: %s", counts)


if __name__ == "__main__":
    asyncio.run(main())
