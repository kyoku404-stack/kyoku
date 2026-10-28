"""Integration Tests for Enterprise Connector REST API Endpoints (Phase 3.1).

Verifies all 7 Connector endpoints defined in docs/api/api-contract.md Section 13:
1. POST /api/v1/connectors/register
2. POST /api/v1/connectors/authenticate
3. GET /api/v1/connectors/list
4. POST /api/v1/connectors/sync
5. GET /api/v1/connectors/status/{id}
6. DELETE /api/v1/connectors/remove/{id}
7. GET /api/v1/connectors/logs

Specification: devdocs/p3/p3.1.txt & docs/api/api-contract.md Section 13
Owner: Member 2 (Backend & Database Lead)
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


class TestConnectorEndpointsIntegration(unittest.TestCase):
    """Integration test suite for Phase 3.1 Connector REST APIs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            # 1. Organization
            cls.org = Organization(
                name="Connectors Test Org",
                domain=f"connectors-{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            # 2. OrgAdmin User (has connector.manage and connector.view permissions)
            cls.user = User(
                email=f"connector-admin-{uuid4().hex[:6]}@test.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Connector Test Admin",
                organization_id=cls.org_id,
                role="OrgAdmin",
            )
            session.add(cls.user)
            session.commit()
            session.refresh(cls.user)
            cls.user_id = cls.user.id

        # Auth Token
        token = create_access_token(
            data={
                "sub": str(cls.user_id),
                "email": cls.user.email,
                "org_id": str(cls.org_id),
                "role": "OrgAdmin",
            }
        )
        cls.headers = {"Authorization": f"Bearer {token}"}
        cls.created_connector_id = None

    def test_01_register_connector(self) -> None:
        """POST /api/v1/connectors/register should return 201 Created."""
        payload = {
            "name": f"Corporate Google Drive {uuid4().hex[:4]}",
            "platform_type": "GOOGLE_DRIVE",
            "platform_category": "CLOUD_STORAGE",
            "auth_type": "OAUTH2",
            "config": {
                "sync_interval_minutes": 60,
                "sync_folders": ["root", "Engineering Docs"],
                "file_extensions": [".pdf", ".docx", ".gdoc", ".txt"],
            },
        }
        resp = self.client.post("/api/v1/connectors/register", json=payload, headers=self.headers)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data["success"])
        connector = data["data"]
        self.assertEqual(connector["name"], payload["name"])
        self.assertEqual(connector["platform_type"], "GOOGLE_DRIVE")
        self.assertEqual(connector["status"], "CONFIGURED")
        TestConnectorEndpointsIntegration.created_connector_id = connector["id"]

    def test_02_authenticate_connector(self) -> None:
        """POST /api/v1/connectors/authenticate should return 200 OK."""
        self.assertIsNotNone(self.created_connector_id)
        payload = {
            "connector_id": self.created_connector_id,
            "auth_type": "OAUTH2",
            "credentials": {
                "access_token": "ya29.sample_oauth_access_token",
                "refresh_token": "1//sample_refresh_token",
                "expires_in": 3600,
            },
        }
        resp = self.client.post("/api/v1/connectors/authenticate", json=payload, headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "CONNECTED")

    def test_03_list_connectors(self) -> None:
        """GET /api/v1/connectors/list should return 200 OK with registered connectors."""
        resp = self.client.get("/api/v1/connectors/list", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["data"]["total_connectors"], 1)
        conn_ids = [c["id"] for c in data["data"]["connectors"]]
        self.assertIn(self.created_connector_id, conn_ids)

    def test_04_start_sync(self) -> None:
        """POST /api/v1/connectors/sync should return 202 Accepted and run sync."""
        self.assertIsNotNone(self.created_connector_id)
        payload = {
            "connector_id": self.created_connector_id,
            "sync_mode": "INCREMENTAL",
        }
        resp = self.client.post("/api/v1/connectors/sync", json=payload, headers=self.headers)
        self.assertEqual(resp.status_code, 202)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["connector_id"], self.created_connector_id)
        self.assertIn(data["data"]["status"], ["RUNNING", "COMPLETED"])

    def test_05_get_connector_status(self) -> None:
        """GET /api/v1/connectors/status/{id} should return 200 OK with telemetry metrics."""
        self.assertIsNotNone(self.created_connector_id)
        resp = self.client.get(f"/api/v1/connectors/status/{self.created_connector_id}", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        conn_status = data["data"]
        self.assertEqual(conn_status["id"], self.created_connector_id)
        self.assertIn("health_metrics", conn_status)
        self.assertGreater(conn_status["health_metrics"]["api_latency_ms"], 0)

    def test_06_get_sync_logs(self) -> None:
        """GET /api/v1/connectors/logs should return 200 OK with audit records."""
        resp = self.client.get(
            f"/api/v1/connectors/logs?connector_id={self.created_connector_id}",
            headers=self.headers,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["data"]["total_logs"], 1)
        first_log = data["data"]["logs"][0]
        self.assertEqual(first_log["connector_id"], self.created_connector_id)
        self.assertIn("external_document_id", first_log)

    def test_07_remove_connector(self) -> None:
        """DELETE /api/v1/connectors/remove/{id} should return 200 OK."""
        self.assertIsNotNone(self.created_connector_id)
        resp = self.client.delete(f"/api/v1/connectors/remove/{self.created_connector_id}", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "DISCONNECTED")

        # Confirm removal
        check_resp = self.client.get(f"/api/v1/connectors/status/{self.created_connector_id}", headers=self.headers)
        self.assertEqual(check_resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
