"""Integration, Security Boundary, and Performance Benchmark Test Suite for KEEP Knowledge Graph (Phase 2.4).

Verifies the end-to-end Knowledge Graph architecture across:
1. Multi-tenant boundary isolation and entity/relationship quarantine
2. Full organizational hierarchy relational construction pipeline
3. Incremental text triple extraction and graph updating
4. Multi-hop topological traversal with cycle prevention and depth capping
5. Downstream blast radius impact analysis and recursive dependency tree calculation
6. Subject-matter expertise discovery and specialist ranking
7. Knowledge explorer topology metrics and force visualization payloads
8. Query latency benchmark verifying < 2000ms SLA

Specification: devdocs/p2/p2.4.txt & docs/Architecture/knowledge-graph-enterprise-intelligence.md
Author: Member 4 (Integration & DevOps Lead)
"""

import time
import unittest
from datetime import timedelta
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


class TestKnowledgeGraphPipelineIntegration(unittest.TestCase):
    """End-to-end integration and security benchmark suite for Phase 2.4 Knowledge Graph."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            # 1. Primary Tenant Organization Alpha
            cls.org_alpha = Organization(
                name="Graph Alpha Tenant",
                domain=f"graph-alpha-{uuid4().hex[:6]}.com",
            )
            # 2. Secondary Tenant Organization Beta (Cross-tenant quarantine testing)
            cls.org_beta = Organization(
                name="Graph Beta Tenant",
                domain=f"graph-beta-{uuid4().hex[:6]}.com",
            )
            session.add_all([cls.org_alpha, cls.org_beta])
            session.commit()
            session.refresh(cls.org_alpha)
            session.refresh(cls.org_beta)

            cls.org_alpha_id = cls.org_alpha.id
            cls.org_beta_id = cls.org_beta.id

            # 3. Alpha Users (Admin and Member)
            cls.user_alpha = User(
                organization_id=cls.org_alpha_id,
                email=f"alpha.lead.{uuid4().hex[:6]}@example.com",
                hashed_password=get_password_hash("AlphaLeadSecret123!"),
                full_name="Alpha Graph Lead",
                role="OrgAdmin",
                is_active=True,
            )
            cls.user_alpha_member = User(
                organization_id=cls.org_alpha_id,
                email=f"alpha.dev.{uuid4().hex[:6]}@example.com",
                hashed_password=get_password_hash("AlphaDevSecret123!"),
                full_name="Alpha Engineer",
                role="Member",
                is_active=True,
            )

            # 4. Beta User (Cross-tenant adversary)
            cls.user_beta = User(
                organization_id=cls.org_beta_id,
                email=f"beta.intruder.{uuid4().hex[:6]}@example.com",
                hashed_password=get_password_hash("BetaSecret123!"),
                full_name="Beta Intruder",
                role="OrgAdmin",
                is_active=True,
            )

            session.add_all([cls.user_alpha, cls.user_alpha_member, cls.user_beta])
            session.commit()
            session.refresh(cls.user_alpha)
            session.refresh(cls.user_alpha_member)
            session.refresh(cls.user_beta)

            # 5. Populate structural organizational entities in Tenant Alpha
            cls.dept_alpha = Department(
                organization_id=cls.org_alpha_id,
                name="Platform Engineering",
                description="Core Cloud & Infrastructure Engineering",
            )
            session.add(cls.dept_alpha)
            session.commit()
            session.refresh(cls.dept_alpha)

            cls.project_alpha = Project(
                organization_id=cls.org_alpha_id,
                name="Apollo Core",
                description="Next-generation Enterprise Gateway",
            )
            session.add(cls.project_alpha)
            session.commit()
            session.refresh(cls.project_alpha)

            # 6. Auth Tokens
            token_alpha = create_access_token(
                data={"sub": str(cls.user_alpha.id), "email": cls.user_alpha.email, "org_id": str(cls.org_alpha_id), "role": "OrgAdmin"},
                expires_delta=timedelta(hours=2),
            )
            cls.headers_alpha = {"Authorization": f"Bearer {token_alpha}"}

            token_beta = create_access_token(
                data={"sub": str(cls.user_beta.id), "email": cls.user_beta.email, "org_id": str(cls.org_beta_id), "role": "OrgAdmin"},
                expires_delta=timedelta(hours=2),
            )
            cls.headers_beta = {"Authorization": f"Bearer {token_beta}"}

    def test_01_full_graph_construction_pipeline(self) -> None:
        """Verifies full relational extraction pipeline creating entities & relationships from DB models."""
        resp = self.client.post(
            "/api/v1/graph/build",
            json={"rebuild_all": True},
            headers=self.headers_alpha,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertGreaterEqual(data["entities_created"], 3)  # Org, Dept, Project, Users
        self.assertGreaterEqual(data["relationships_created"], 1)

    def test_02_incremental_unstructured_text_extraction(self) -> None:
        """Verifies incremental named entity recognition and triple extraction from free text."""
        statement = (
            "Project Apollo Core is led by Alpha Graph Lead. "
            "Alpha Engineer works on Apollo Core. "
            "Platform Engineering governs Apollo Core."
        )
        resp = self.client.post(
            "/api/v1/graph/update",
            json={"text_content": statement},
            headers=self.headers_alpha,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertGreaterEqual(data["entities_extracted"], 1)
        self.assertGreaterEqual(data["relationships_extracted"], 1)

    def test_03_multi_hop_traversal_and_cycle_prevention(self) -> None:
        """Verifies multi-hop BFS traversal resolves connected neighborhood without infinite cycles."""
        with Session(sync_test_engine) as session:
            project_entity = session.query(KgEntity).filter(
                KgEntity.organization_id == self.org_alpha_id,
                KgEntity.name == "Apollo Core",
            ).first()
            self.assertIsNotNone(project_entity)
            entity_id = project_entity.id

        resp = self.client.post(
            "/api/v1/graph/query",
            json={"start_entity_id": str(entity_id), "max_depth": 3},
            headers=self.headers_alpha,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertGreaterEqual(len(data["nodes"]), 1)

        # Entity IDs must be distinct (cycle prevention verification)
        node_ids = [n["id"] for n in data["nodes"]]
        self.assertEqual(len(node_ids), len(set(node_ids)))

    def test_04_depth_capping_and_validation(self) -> None:
        """Verifies that requesting depth > 5 is rejected by schema validator (ge=1, le=5)."""
        with Session(sync_test_engine) as session:
            dept_entity = session.query(KgEntity).filter(
                KgEntity.organization_id == self.org_alpha_id,
                KgEntity.name == "Platform Engineering",
            ).first()
            self.assertIsNotNone(dept_entity)
            entity_id = dept_entity.id

        # Depth 6 must fail with 422
        resp = self.client.post(
            "/api/v1/graph/query",
            json={"start_entity_id": str(entity_id), "max_depth": 6},
            headers=self.headers_alpha,
        )
        self.assertEqual(resp.status_code, 422)

        # Depth 5 must succeed
        resp_valid = self.client.post(
            "/api/v1/graph/query",
            json={"start_entity_id": str(entity_id), "max_depth": 5},
            headers=self.headers_alpha,
        )
        self.assertEqual(resp_valid.status_code, 200)
        self.assertGreaterEqual(resp_valid.json()["data"]["max_depth_reached"], 0)

    def test_05_downstream_impact_blast_radius_analysis(self) -> None:
        """Verifies downstream impact blast radius traversal and severity scoring."""
        with Session(sync_test_engine) as session:
            project_entity = session.query(KgEntity).filter(
                KgEntity.organization_id == self.org_alpha_id,
                KgEntity.name == "Apollo Core",
            ).first()
            self.assertIsNotNone(project_entity)
            entity_id = project_entity.id

        resp = self.client.get(
            f"/api/v1/graph/impact/{entity_id}?max_depth=3",
            headers=self.headers_alpha,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["root_entity"]["id"], str(entity_id))
        self.assertIn("severity_score", data)
        self.assertGreaterEqual(data["severity_score"], 0.0)
        self.assertLessEqual(data["severity_score"], 1.0)
        self.assertIn("affected_departments", data)
        self.assertIn("dependent_projects", data)
        self.assertIn("dependency_tree", data)

    def test_06_expertise_discovery_scoring(self) -> None:
        """Verifies subject-matter expert discovery and ranking."""
        resp = self.client.get(
            "/api/v1/graph/expertise?topic=Engineering&limit=5",
            headers=self.headers_alpha,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["topic"], "Engineering")
        self.assertIn("experts", data)
        self.assertIsInstance(data["experts"], list)

    def test_07_graph_explorer_topology_metrics(self) -> None:
        """Verifies graph explorer force-directed visualization payload and topological density."""
        resp = self.client.get(
            "/api/v1/graph/explorer?max_depth=2",
            headers=self.headers_alpha,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertIn("nodes", data)
        self.assertIn("links", data)
        self.assertIn("metrics", data)
        metrics = data["metrics"]
        self.assertGreaterEqual(metrics["total_entities"], 1)
        self.assertGreaterEqual(metrics["density"], 0.0)

    def test_08_multi_tenant_isolation_boundary_enforcement(self) -> None:
        """Verifies strict cross-tenant isolation: Tenant Beta cannot read or impact Tenant Alpha's graph."""
        with Session(sync_test_engine) as session:
            alpha_entity = session.query(KgEntity).filter(
                KgEntity.organization_id == self.org_alpha_id
            ).first()
            self.assertIsNotNone(alpha_entity)
            alpha_entity_id = alpha_entity.id

        # 1. Tenant Beta attempts to inspect Tenant Alpha's entity
        resp = self.client.get(
            f"/api/v1/graph/entity/{alpha_entity_id}",
            headers=self.headers_beta,
        )
        self.assertEqual(resp.status_code, 404)

        # 2. Tenant Beta attempts to inspect Tenant Alpha's relationships
        resp = self.client.get(
            f"/api/v1/graph/relationships/{alpha_entity_id}",
            headers=self.headers_beta,
        )
        self.assertEqual(resp.status_code, 404)

        # 3. Tenant Beta attempts to run impact analysis on Tenant Alpha's entity
        resp = self.client.get(
            f"/api/v1/graph/impact/{alpha_entity_id}",
            headers=self.headers_beta,
        )
        self.assertEqual(resp.status_code, 404)

        # 4. Tenant Beta queries graph with Alpha's entity ID -> must return 404
        resp = self.client.post(
            "/api/v1/graph/query",
            json={"start_entity_id": str(alpha_entity_id)},
            headers=self.headers_beta,
        )
        self.assertEqual(resp.status_code, 404)

    def test_09_graph_traversal_performance_benchmark(self) -> None:
        """Verifies that multi-hop graph queries and impact analysis execute within SLA (< 2000ms)."""
        start = time.perf_counter()
        resp = self.client.get(
            "/api/v1/graph/explorer",
            headers=self.headers_alpha,
        )
        duration_ms = (time.perf_counter() - start) * 1000.0

        self.assertEqual(resp.status_code, 200)
        self.assertLess(duration_ms, 2000.0, f"Graph explorer latency {duration_ms:.2f}ms exceeded 2000ms SLA")
