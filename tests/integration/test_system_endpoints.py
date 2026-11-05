"""Integration Test Suite: Production Infrastructure & System Operations REST APIs.

Phase: 3.6
Owner: Member 2 (Backend & Database Lead)
Domain: tests/integration/test_system_endpoints.py
Specification: devdocs/p3/p3.6.txt (Chapter 16) & docs/api/api-contract.md (Section 18)
"""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestSystemEndpointsIntegration(unittest.TestCase):
    """Integration test suite for Phase 3.6 System & Infrastructure REST APIs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            cls.org = Organization(
                name="Infra Test Enterprise",
                domain=f"infra-{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            cls.admin_user = User(
                email=f"admin-{uuid4().hex[:6]}@infra.com",
                hashed_password=get_password_hash("Password123!"),
                full_name="Infra Admin",
                role="OrgAdmin",
                organization_id=cls.org_id,
                is_active=True,
            )
            session.add(cls.admin_user)
            session.commit()
            session.refresh(cls.admin_user)
            cls.admin_id = cls.admin_user.id

        token_payload = {
            "sub": str(cls.admin_id),
            "email": cls.admin_user.email,
            "org_id": str(cls.org_id),
            "role": "OrgAdmin",
            "mfa_verified": True,
        }
        cls.auth_token = create_access_token(data=token_payload)
        cls.headers = {"Authorization": f"Bearer {cls.auth_token}"}

    def test_01_get_system_health(self) -> None:
        """Verifies GET /api/v1/system/health returns composite health diagnostic."""
        res = self.client.get("/api/v1/system/health", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertIn("status", data)
        self.assertIn("subsystems", data)
        self.assertIn("database", data["subsystems"])
        self.assertIn("redis", data["subsystems"])
        self.assertIn("overall_score", data)

    def test_02_get_system_metrics(self) -> None:
        """Verifies GET /api/v1/system/metrics returns system telemetry."""
        res = self.client.get("/api/v1/system/metrics", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertIn("cpu", data)
        self.assertIn("memory", data)
        self.assertIn("disk", data)
        self.assertIn("network", data)
        self.assertIn("application", data)
        self.assertIn("cache", data)

    def test_03_get_system_logs(self) -> None:
        """Verifies GET /api/v1/system/logs returns diagnostic logs."""
        res = self.client.get("/api/v1/system/logs?limit=10", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertIsInstance(body["data"], list)

    def test_04_trigger_deployment(self) -> None:
        """Verifies POST /api/v1/system/deploy triggers a service deployment."""
        payload = {
            "service_name": "keep-backend-api",
            "version": "3.6.1-patch1",
            "strategy": "BLUE_GREEN",
            "environment": "production",
            "auto_rollback_on_failure": True,
        }
        res = self.client.post("/api/v1/system/deploy", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertEqual(data["service_name"], "keep-backend-api")
        self.assertEqual(data["version"], "3.6.1-patch1")
        self.assertEqual(data["status"], "SUCCESS")
        self.assertIn("dep-", data["deployment_id"])

    def test_05_get_system_version(self) -> None:
        """Verifies GET /api/v1/system/version returns release metadata."""
        res = self.client.get("/api/v1/system/version", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertEqual(data["version"], "3.6.0")
        self.assertEqual(data["environment"], "production")
        self.assertIn("fastapi", data["frameworks"])

    def test_06_get_services_status(self) -> None:
        """Verifies GET /api/v1/system/status returns all microservice statuses."""
        res = self.client.get("/api/v1/system/status", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 6)
        service_names = [s["service_name"] for s in data]
        self.assertIn("keep-frontend", service_names)
        self.assertIn("keep-backend-api", service_names)

    def test_07_get_and_create_backups(self) -> None:
        """Verifies GET /api/v1/system/backups and POST /api/v1/system/backups/create."""
        # 1. Create backup
        create_payload = {
            "backup_type": "DATABASE",
            "notes": "E2E integration test snapshot",
        }
        create_res = self.client.post("/api/v1/system/backups/create", json=create_payload, headers=self.headers)
        self.assertEqual(create_res.status_code, 201)
        create_body = create_res.json()
        self.assertTrue(create_body["success"])
        self.assertEqual(create_body["data"]["status"], "COMPLETED")

        # 2. List backups
        list_res = self.client.get("/api/v1/system/backups", headers=self.headers)
        self.assertEqual(list_res.status_code, 200)
        list_body = list_res.json()
        self.assertTrue(list_body["success"])
        backups_data = list_body["data"]
        self.assertGreaterEqual(len(backups_data["backups"]), 1)
        self.assertEqual(backups_data["rpo_target_minutes"], 60)

    def test_08_flush_cache(self) -> None:
        """Verifies POST /api/v1/system/cache/flush invalidates namespaces."""
        payload = {
            "namespaces": ["ai_response", "vector_query"],
            "flush_all": False,
        }
        res = self.client.post("/api/v1/system/cache/flush", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertIn("keep:ai:resp:", data["flushed_namespaces"])
        self.assertGreater(data["keys_removed"], 0)


if __name__ == "__main__":
    unittest.main()
