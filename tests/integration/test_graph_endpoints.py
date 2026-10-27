"""Integration Tests for Knowledge Graph & Enterprise Intelligence REST APIs (Phase 2.4).

Verifies all endpoints defined in docs/API/api-contract.md Section 11:
1. POST /api/v1/graph/build
2. POST /api/v1/graph/update
3. GET  /api/v1/graph/entity/{id}
4. GET  /api/v1/graph/relationships/{id}
5. POST /api/v1/graph/query
6. GET  /api/v1/graph/explorer
7. GET  /api/v1/graph/expertise
8. GET  /api/v1/graph/impact/{entity_id}

Owner: Member 2 (Backend Lead)
Domain: /tests/integration
Specification: devdocs/p2/p2.4.txt & docs/API/api-contract.md Section 11
"""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.department import Department
from backend.app.models.knowledge import KgEntity
from backend.app.models.organization import Organization
from backend.app.models.project import Project
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestGraphEndpointsIntegration(unittest.TestCase):
    """Integration test suite for Phase 2.4 Knowledge Graph REST APIs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            # 1. Tenant organization
            cls.org = Organization(
                name="Graph REST Org",
                domain=f"graph-rest-{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            # 2. Test user (OrgAdmin to have full permissions)
            cls.user = User(
                email=f"graph-admin-{uuid4().hex[:6]}@graphtest.com",
                hashed_password=get_password_hash("SecretPass123!"),
                full_name="Dr. Graph Analyst",
                organization_id=cls.org_id,
                role="OrgAdmin",
            )
            session.add(cls.user)
            session.commit()
            session.refresh(cls.user)
            cls.user_id = cls.user.id

            # 3. Department & Project
            cls.dept = Department(
                name="Research & Development",
                organization_id=cls.org_id,
                manager_id=cls.user_id,
            )
            session.add(cls.dept)
            session.commit()
            session.refresh(cls.dept)

            cls.proj = Project(
                name="Quantum Computing Project",
                organization_id=cls.org_id,
                owner_id=cls.user_id,
                description="Advanced Quantum Algorithms",
                status="ACTIVE",
            )
            session.add(cls.proj)
            session.commit()
            session.refresh(cls.proj)

        # 4. Generate Auth Token
        token = create_access_token(
            data={
                "sub": str(cls.user_id),
                "email": cls.user.email,
                "organization_id": str(cls.org_id),
                "role": "OrgAdmin",
            }
        )
        cls.auth_headers = {"Authorization": f"Bearer {token}"}

    def test_01_build_graph(self):
        payload = {
            "rebuild_all": True,
            "confidence_threshold": 0.70,
            "include_documents": True,
            "include_organizational": True,
        }
        resp = self.client.post("/api/v1/graph/build", json=payload, headers=self.auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["entities_created"] >= 3
        assert data["data"]["total_entities"] >= 3

    def test_02_update_graph_incremental(self):
        payload = {
            "text_content": "The Cloud Security Standard is led by Alice Smith and applies to the Research & Development department.",
            "metadata": {"category": "SECURITY"},
        }
        resp = self.client.post("/api/v1/graph/update", json=payload, headers=self.auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["entities_extracted"] >= 1

    def test_03_get_entity_details_and_relationships(self):
        with Session(sync_test_engine) as session:
            entity = session.query(KgEntity).filter(
                KgEntity.organization_id == self.org_id,
                KgEntity.name == "Quantum Computing Project",
            ).first()
            assert entity is not None
            entity_id = entity.id

        # Details
        resp = self.client.get(f"/api/v1/graph/entity/{entity_id}", headers=self.auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Quantum Computing Project"

        # Relationships
        rel_resp = self.client.get(f"/api/v1/graph/relationships/{entity_id}", headers=self.auth_headers)
        assert rel_resp.status_code == 200, rel_resp.text
        rel_data = rel_resp.json()
        assert rel_data["success"] is True
        assert rel_data["data"]["entity_id"] == str(entity_id)

    def test_04_execute_query(self):
        with Session(sync_test_engine) as session:
            entity = session.query(KgEntity).filter(
                KgEntity.organization_id == self.org_id,
                KgEntity.name == "Quantum Computing Project",
            ).first()
            assert entity is not None
            entity_id = entity.id

        payload = {
            "start_entity_id": str(entity_id),
            "max_depth": 2,
        }
        resp = self.client.post("/api/v1/graph/query", json=payload, headers=self.auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]["nodes"]) >= 1

    def test_05_get_explorer_data(self):
        resp = self.client.get("/api/v1/graph/explorer?limit=50", headers=self.auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]["nodes"]) >= 1
        assert "density" in data["data"]["metrics"]

    def test_06_discover_expertise(self):
        resp = self.client.get("/api/v1/graph/expertise?topic=Quantum&limit=5", headers=self.auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["topic"] == "Quantum"
        assert len(data["data"]["experts"]) >= 1

    def test_07_analyze_impact(self):
        with Session(sync_test_engine) as session:
            entity = session.query(KgEntity).filter(
                KgEntity.organization_id == self.org_id,
                KgEntity.name == "Quantum Computing Project",
            ).first()
            assert entity is not None
            entity_id = entity.id

        resp = self.client.get(f"/api/v1/graph/impact/{entity_id}?max_depth=3", headers=self.auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["root_entity"]["name"] == "Quantum Computing Project"
        assert "severity_score" in data["data"]

    def test_08_unauthorized_access(self):
        resp = self.client.get("/api/v1/graph/explorer")
        # Should be 401 or 403 when no auth token provided
        assert resp.status_code in [401, 403], resp.text
