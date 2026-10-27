"""Unit tests for Phase 2.4 Knowledge Graph and Enterprise Intelligence Services.

Owner: Member 2 (Backend & Database Lead)
Domain: /tests/unit
Specification: devdocs/p2/p2.4.txt & docs/API/api-contract.md Section 11
"""

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from backend.app.core.exceptions import BadRequestException, NotFoundException
from backend.app.models.department import Department
from backend.app.models.document import Document
from backend.app.models.knowledge import DocumentChunk, KgEntity
from backend.app.models.organization import Organization
from backend.app.models.project import Project
from backend.app.models.task import Task
from backend.app.models.team import Team
from backend.app.models.user import User
from backend.app.services.graph.contracts import EntityType
from backend.app.services.graph.service import KnowledgeGraphService
from tests.conftest import sync_test_engine


class TestKnowledgeGraphService:
    """Unit tests for KnowledgeGraphService business logic."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        self.service = KnowledgeGraphService()
        self.org_id = uuid4()
        with Session(sync_test_engine) as session:
            # Create Org
            org = Organization(id=self.org_id, name="Graph Corp", domain=f"graph-{uuid4().hex[:6]}.com")
            session.add(org)

            # Create User
            self.user_id = uuid4()
            user = User(
                id=self.user_id,
                organization_id=self.org_id,
                email=f"alice-{uuid4().hex[:6]}@graphcorp.com",
                full_name="Alice Smith",
                hashed_password="pw",
                role="Member",
            )
            session.add(user)

            # Create Department
            self.dept_id = uuid4()
            dept = Department(
                id=self.dept_id,
                organization_id=self.org_id,
                name="Engineering",
                manager_id=self.user_id,
            )
            session.add(dept)

            # Update User dept
            user.department_id = self.dept_id

            # Create Team
            self.team_id = uuid4()
            team = Team(
                id=self.team_id,
                organization_id=self.org_id,
                department_id=self.dept_id,
                name="Core AI",
            )
            session.add(team)

            # Create Project
            self.project_id = uuid4()
            proj = Project(
                id=self.project_id,
                organization_id=self.org_id,
                team_id=self.team_id,
                owner_id=self.user_id,
                name="NextGen Intelligence",
                description="Enterprise Graph and AI initiative",
                status="ACTIVE",
            )
            session.add(proj)

            # Create Task
            self.task_id = uuid4()
            task = Task(
                id=self.task_id,
                project_id=self.project_id,
                title="Implement Knowledge Graph Schema",
                status="IN_PROGRESS",
            )
            session.add(task)

            # Create Document & Chunk
            self.doc_id = uuid4()
            doc = Document(
                id=self.doc_id,
                organization_id=self.org_id,
                project_id=self.project_id,
                uploader_id=self.user_id,
                filename="Architecture_Spec.pdf",
                title="Enterprise Architecture Specification",
                category="ARCHITECTURE",
                file_path="/storage/docs/Architecture_Spec.pdf",
                file_type="application/pdf",
                file_size=10240,
            )
            session.add(doc)

            chunk = DocumentChunk(
                id=uuid4(),
                document_id=self.doc_id,
                chunk_index=0,
                content="The NextGen Intelligence platform is led by Alice Smith and applies to the Engineering department.",
            )
            session.add(chunk)

            session.commit()

    def test_build_graph_success(self):
        with Session(sync_test_engine) as session:
            resp = self.service.build_graph(
                db=session,
                organization_id=self.org_id,
                rebuild_all=True,
                include_organizational=True,
                include_documents=True,
            )

            assert resp.organization_id == self.org_id
            assert resp.entities_created > 0
            assert resp.relationships_created > 0
            assert resp.total_entities >= 5
            assert resp.total_relationships >= 4
            assert resp.duration_seconds >= 0.0

            # Verify entities in DB
            entities = session.query(KgEntity).filter(KgEntity.organization_id == self.org_id).all()
            entity_names = {e.name for e in entities}
            assert "Graph Corp" in entity_names
            assert "Engineering" in entity_names
            assert "NextGen Intelligence" in entity_names
            assert "Alice Smith" in entity_names

    def test_update_graph_incremental(self):
        with Session(sync_test_engine) as session:
            text = "The Cyber Security Taskforce is led by Bob Vance and applies to Operations."
            resp = self.service.update_graph_incremental(
                db=session,
                organization_id=self.org_id,
                text_content=text,
                metadata={"category": "SECURITY"},
            )

            assert resp.entities_extracted >= 1
            assert resp.relationships_extracted >= 1
            extracted_names = [e.name for e in resp.extracted_entities]
            assert any("Bob Vance" in n or "Cyber Security" in n for n in extracted_names)

    def test_get_entity_and_relationships(self):
        with Session(sync_test_engine) as session:
            # Build graph first
            self.service.build_graph(db=session, organization_id=self.org_id, rebuild_all=True)

            # Retrieve Engineering dept entity
            dept_entity = session.query(KgEntity).filter(
                KgEntity.organization_id == self.org_id,
                KgEntity.name == "Engineering",
            ).first()
            assert dept_entity is not None

            e_resp = self.service.get_entity(db=session, organization_id=self.org_id, entity_id=dept_entity.id)
            assert e_resp.name == "Engineering"
            assert e_resp.entity_type == EntityType.DEPARTMENT.value
            assert e_resp.in_degree >= 1

            rel_resp = self.service.get_entity_relationships(db=session, organization_id=self.org_id, entity_id=dept_entity.id)
            assert rel_resp.entity_id == str(dept_entity.id)
            # Should have incoming LEADS from Alice or incoming BELONGS_TO from team
            assert len(rel_resp.incoming_relationships) + len(rel_resp.outgoing_relationships) >= 1

    def test_get_entity_not_found(self):
        with Session(sync_test_engine) as session:
            random_id = uuid4()
            with pytest.raises(NotFoundException):
                self.service.get_entity(db=session, organization_id=self.org_id, entity_id=random_id)

    def test_execute_query_traversal(self):
        with Session(sync_test_engine) as session:
            self.service.build_graph(db=session, organization_id=self.org_id, rebuild_all=True)

            proj_entity = session.query(KgEntity).filter(
                KgEntity.organization_id == self.org_id,
                KgEntity.name == "NextGen Intelligence",
            ).first()
            assert proj_entity is not None

            q_resp = self.service.execute_query(
                db=session,
                organization_id=self.org_id,
                start_entity_id=str(proj_entity.id),
                max_depth=2,
            )

            assert len(q_resp.nodes) >= 2
            assert q_resp.total_paths >= 1
            assert q_resp.max_depth_reached >= 1

    def test_get_explorer_data(self):
        with Session(sync_test_engine) as session:
            self.service.build_graph(db=session, organization_id=self.org_id, rebuild_all=True)

            exp_resp = self.service.get_explorer_data(db=session, organization_id=self.org_id, limit=50)

            assert len(exp_resp.nodes) >= 4
            assert len(exp_resp.links) >= 3
            assert exp_resp.metrics.total_entities >= 4
            assert exp_resp.metrics.top_hub is not None

    def test_discover_expertise(self):
        with Session(sync_test_engine) as session:
            self.service.build_graph(db=session, organization_id=self.org_id, rebuild_all=True)

            exp_resp = self.service.discover_expertise(
                db=session,
                organization_id=self.org_id,
                topic="Intelligence",
                limit=3,
            )

            assert exp_resp.topic == "Intelligence"
            assert len(exp_resp.experts) >= 1
            expert = exp_resp.experts[0]
            assert expert.full_name == "Alice Smith"
            assert expert.score > 0.0

    def test_analyze_impact(self):
        with Session(sync_test_engine) as session:
            self.service.build_graph(db=session, organization_id=self.org_id, rebuild_all=True)

            proj_entity = session.query(KgEntity).filter(
                KgEntity.organization_id == self.org_id,
                KgEntity.name == "NextGen Intelligence",
            ).first()
            assert proj_entity is not None

            imp_resp = self.service.analyze_impact(
                db=session,
                organization_id=self.org_id,
                entity_id=proj_entity.id,
                max_depth=3,
            )

            assert imp_resp.root_entity.name == "NextGen Intelligence"
            assert imp_resp.severity_score >= 0.2
            assert len(imp_resp.dependency_tree) >= 1

    def test_invalid_uuid_handling(self):
        with Session(sync_test_engine) as session:
            with pytest.raises(BadRequestException):
                self.service.get_entity(db=session, organization_id=self.org_id, entity_id="not-a-uuid")
