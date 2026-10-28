"""Integration Test Suite: Plugin SDK, Extension Framework & Developer Ecosystem REST APIs.

Phase: 3.5
Owner: Member 2 (Backend & Database Lead)
Domain: tests/integration/test_plugin_endpoints.py
Specification: devdocs/p3/p3.5.txt (Chapters 1-20) & docs/api/api-contract.md (Section 17)
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


class TestPluginEndpointsIntegration(unittest.TestCase):
    """Integration test suite for Phase 3.5 Plugin REST APIs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            cls.org = Organization(
                name="Plugin Test Enterprise",
                domain=f"plugin-{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            cls.admin_user = User(
                email=f"admin-{uuid4().hex[:6]}@plugin.com",
                hashed_password=get_password_hash("Password123!"),
                full_name="Plugin Platform Admin",
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

    def test_01_browse_marketplace(self) -> None:
        """Verifies browsing the plugin marketplace catalog and automatic seeding."""
        response = self.client.get("/api/v1/plugins/marketplace", headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertTrue(data["success"])
        items = data["data"]
        self.assertGreaterEqual(len(items), 3)

        plugin_ids = [item["plugin_id"] for item in items]
        self.assertIn("ai-anthropic-claude", plugin_ids)
        self.assertIn("sap-s4hana-connector", plugin_ids)
        self.assertIn("slack-realtime-notifier", plugin_ids)

    def test_02_publish_marketplace_plugin(self) -> None:
        """Verifies registering a custom community plugin into the marketplace."""
        payload = {
            "id": f"zendesk-support-sync-{uuid4().hex[:4]}",
            "name": "Zendesk Support Enterprise Connector",
            "description": "Bidirectional customer issue sync and AI auto-response generation.",
            "category": "INTEGRATION",
            "developer": "Zendesk Integration Team",
            "version": "1.0.0",
            "entry_point": "plugins.zendesk:ZendeskPlugin",
            "min_keep_version": "3.0.0",
            "max_keep_version": "3.9.9",
            "permissions": ["NOTIFICATIONS_SEND", "NETWORK_EGRESS"],
            "event_hooks": ["on_ticket_created"],
            "configuration_schema": {"type": "object", "properties": {"api_token": {"type": "string"}}},
        }
        response = self.client.post("/api/v1/plugins/marketplace/publish", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 201, response.text)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "PUBLISHED")

    def test_03_install_plugin(self) -> None:
        """Verifies installing a certified marketplace plugin into the tenant workspace."""
        payload = {
            "plugin_id": "ai-anthropic-claude",
            "version": "1.2.0",
            "configuration": {"api_key": "sk-ant-test-token-42", "temperature": 0.3},
            "approved_permissions": ["AI_INFERENCE", "READ_DOCUMENTS"],
        }
        response = self.client.post("/api/v1/plugins/install", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 201, response.text)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["plugin_id"], "ai-anthropic-claude")
        self.assertTrue(data["data"]["is_enabled"])
        self.assertEqual(data["data"]["status"], "ACTIVE")

    def test_04_list_installed_plugins(self) -> None:
        """Verifies retrieving the installed plugins for the organization."""
        response = self.client.get("/api/v1/plugins/list", headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertTrue(data["success"])
        items = data["data"]
        self.assertGreaterEqual(len(items), 1)

        installed_ids = [item["plugin_id"] for item in items]
        self.assertIn("ai-anthropic-claude", installed_ids)

    def test_05_get_plugin_details(self) -> None:
        """Verifies fetching details of a specific installed plugin."""
        response = self.client.get("/api/v1/plugins/ai-anthropic-claude", headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["plugin_id"], "ai-anthropic-claude")
        self.assertEqual(data["data"]["configuration"]["temperature"], 0.3)

    def test_06_update_plugin_config(self) -> None:
        """Verifies updating runtime configuration for an installed plugin."""
        payload = {"configuration": {"temperature": 0.7, "model": "claude-3-5-sonnet-latest"}}
        response = self.client.post("/api/v1/plugins/ai-anthropic-claude/config", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["configuration"]["temperature"], 0.7)
        self.assertEqual(data["data"]["configuration"]["model"], "claude-3-5-sonnet-latest")

    def test_07_disable_and_enable_plugin(self) -> None:
        """Verifies toggling plugin activation state."""
        # Disable
        dis_res = self.client.post("/api/v1/plugins/disable", json={"plugin_id": "ai-anthropic-claude"}, headers=self.headers)
        self.assertEqual(dis_res.status_code, 200, dis_res.text)
        dis_data = dis_res.json()
        self.assertFalse(dis_data["data"]["is_enabled"])
        self.assertEqual(dis_data["data"]["status"], "DISABLED")

        # Enable
        en_res = self.client.post("/api/v1/plugins/enable", json={"plugin_id": "ai-anthropic-claude"}, headers=self.headers)
        self.assertEqual(en_res.status_code, 200, en_res.text)
        en_data = en_res.json()
        self.assertTrue(en_data["data"]["is_enabled"])
        self.assertEqual(en_data["data"]["status"], "ACTIVE")

    def test_08_execute_plugin_action(self) -> None:
        """Verifies sandboxed execution dispatch and telemetry log creation."""
        payload = {
            "action": "execute_inference",
            "parameters": {"prompt": "Analyze revenue trends from the Q3 spreadsheet."},
            "timeout_seconds": 15.0,
        }
        response = self.client.post("/api/v1/plugins/ai-anthropic-claude/execute", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "SUCCESS")
        self.assertEqual(data["data"]["plugin_id"], "ai-anthropic-claude")
        self.assertIn("execution_id", data["data"])

    def test_09_get_execution_logs(self) -> None:
        """Verifies querying execution history audit trail."""
        response = self.client.get("/api/v1/plugins/logs", headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["plugin_id"], "ai-anthropic-claude")

    def test_10_get_plugin_analytics(self) -> None:
        """Verifies calculating operational metrics and latency metrics."""
        response = self.client.get("/api/v1/plugins/analytics", headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertTrue(data["success"])
        analytics = data["data"]
        self.assertGreaterEqual(analytics["total_installed_plugins"], 1)
        self.assertGreaterEqual(analytics["total_executions"], 1)
        self.assertIn("AI", analytics["plugins_by_category"])

    def test_11_uninstall_plugin(self) -> None:
        """Verifies cleanly uninstalling a plugin."""
        payload = {"plugin_id": "ai-anthropic-claude", "purge_data": False}
        response = self.client.post("/api/v1/plugins/uninstall", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertTrue(data["success"])

        # Check list is empty of this plugin
        list_res = self.client.get("/api/v1/plugins/list", headers=self.headers)
        self.assertEqual(list_res.status_code, 200)
        p_ids = [item["plugin_id"] for item in list_res.json()["data"]]
        self.assertNotIn("ai-anthropic-claude", p_ids)


if __name__ == "__main__":
    unittest.main()
