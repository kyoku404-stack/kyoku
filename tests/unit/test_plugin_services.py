"""Unit Test Suite: Enterprise Plugin Service & Lifecycle Orchestration.

Phase: 3.5
Owner: Member 2 (Backend & Database Lead)
Domain: tests/unit/test_plugin_services.py
Specification: devdocs/p3/p3.5.txt (Chapters 1-20)
"""

import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from backend.app.schemas.plugin import (
    PluginExecuteRequest,
    PluginInstallRequest,
    PluginPublishRequest,
    PluginUpdateRequest,
)
from backend.app.services.plugins.service import (
    DEFAULT_SEED_PLUGINS,
    EnterprisePluginService,
)


class TestEnterprisePluginServiceUnit(unittest.IsolatedAsyncioTestCase):
    """Unit tests verifying EnterprisePluginService business operations and isolation."""

    def setUp(self) -> None:
        self.service = EnterprisePluginService()
        self.org_id = uuid.uuid4()
        self.user_id = uuid.uuid4()

    async def test_seed_default_marketplace(self) -> None:
        """Verifies default certified marketplace plugins are seeded when missing."""
        mock_db = AsyncMock()
        mock_db.get.return_value = None  # None exist yet

        await self.service.seed_default_marketplace(mock_db)

        # 3 default seed items should have been added
        self.assertEqual(mock_db.add.call_count, len(DEFAULT_SEED_PLUGINS) * 2)  # Plugin + Manifest
        mock_db.commit.assert_awaited_once()

    async def test_publish_marketplace_plugin_incompatible_semver(self) -> None:
        """Verifies that publishing a plugin with incompatible platform version bounds is rejected."""
        mock_db = AsyncMock()
        payload = PluginPublishRequest(
            id="future-plugin",
            name="Future AI Plugin",
            description="Requires KEEP 4.0.0+",
            category="AI",
            developer="NextGen",
            version="1.0.0",
            entry_point="future.ai:Plugin",
            min_keep_version="4.0.0",
            max_keep_version="4.9.9",
        )

        with self.assertRaises(HTTPException) as ctx:
            await self.service.publish_marketplace_plugin(mock_db, self.user_id, payload)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("incompatible", ctx.exception.detail)

    async def test_publish_marketplace_plugin_success(self) -> None:
        """Verifies successful registration of a community plugin."""
        mock_db = AsyncMock()
        mock_db.get.return_value = None  # New plugin

        mock_query_res = MagicMock()
        mock_query_res.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_query_res

        payload = PluginPublishRequest(
            id="community-summarizer",
            name="Community Summarizer",
            description="Fast text summarization plugin",
            category="AI",
            developer="Community Dev",
            version="1.0.0",
            entry_point="summarizer:Plugin",
            min_keep_version="3.0.0",
            max_keep_version="3.9.9",
        )

        result = await self.service.publish_marketplace_plugin(mock_db, self.user_id, payload)
        self.assertEqual(result["plugin_id"], "community-summarizer")
        self.assertEqual(result["status"], "PUBLISHED")
        mock_db.commit.assert_awaited_once()

    async def test_install_plugin_duplicate_check(self) -> None:
        """Verifies duplicate installation within the same organization raises 400."""
        mock_db = AsyncMock()
        mock_existing = MagicMock()

        mock_query_res = MagicMock()
        mock_query_res.scalars.return_value.first.return_value = mock_existing
        mock_db.execute.return_value = mock_query_res

        payload = PluginInstallRequest(plugin_id="sap-s4hana-connector")

        with self.assertRaises(HTTPException) as ctx:
            await self.service.install_plugin(mock_db, self.org_id, self.user_id, payload)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("already installed", ctx.exception.detail)

    async def test_install_plugin_not_found(self) -> None:
        """Verifies installation of non-existent catalog plugin raises 404."""
        mock_db = AsyncMock()

        mock_query_res = MagicMock()
        mock_query_res.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_query_res
        mock_db.get.return_value = None

        payload = PluginInstallRequest(plugin_id="non-existent-plugin")

        with self.assertRaises(HTTPException) as ctx:
            await self.service.install_plugin(mock_db, self.org_id, self.user_id, payload)
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_toggle_enable_disable_plugin(self) -> None:
        """Verifies enable and disable transitions."""
        mock_db = AsyncMock()
        mock_inst = MagicMock(is_enabled=False, status="DISABLED")

        mock_query_res = MagicMock()
        mock_query_res.scalars.return_value.first.return_value = mock_inst
        mock_db.execute.return_value = mock_query_res

        # Mock get_plugin
        with patch.object(self.service, "get_plugin", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "id": str(uuid.uuid4()),
                "plugin_id": "sap-s4hana-connector",
                "is_enabled": True,
                "status": "ACTIVE",
            }
            res_enable = await self.service.enable_plugin(mock_db, self.org_id, "sap-s4hana-connector")
            self.assertTrue(mock_inst.is_enabled)
            self.assertEqual(mock_inst.status, "ACTIVE")
            self.assertEqual(res_enable["status"], "ACTIVE")

            mock_get.return_value = {
                "id": str(uuid.uuid4()),
                "plugin_id": "sap-s4hana-connector",
                "is_enabled": False,
                "status": "DISABLED",
            }
            res_disable = await self.service.disable_plugin(mock_db, self.org_id, "sap-s4hana-connector")
            self.assertFalse(mock_inst.is_enabled)
            self.assertEqual(mock_inst.status, "DISABLED")
            self.assertEqual(res_disable["status"], "DISABLED")

    async def test_update_plugin_version_validation(self) -> None:
        """Verifies version upgrade bounds validation."""
        mock_db = AsyncMock()
        mock_inst = MagicMock(version="1.0.0")

        mock_inst_res = MagicMock()
        mock_inst_res.scalars.return_value.first.return_value = mock_inst

        # Manifest with incompatible platform
        mock_manifest = MagicMock(
            min_keep_version="4.0.0",
            max_keep_version="4.5.0",
        )
        mock_mf_res = MagicMock()
        mock_mf_res.scalars.return_value.first.return_value = mock_manifest

        mock_db.execute.side_effect = [mock_inst_res, mock_mf_res]

        payload = PluginUpdateRequest(plugin_id="sap-s4hana-connector", target_version="2.0.0")
        with self.assertRaises(HTTPException) as ctx:
            await self.service.update_plugin_version(mock_db, self.org_id, payload)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("incompatible", ctx.exception.detail)

    async def test_execute_plugin_action_disabled_fails(self) -> None:
        """Verifies executing action on disabled plugin raises 400."""
        mock_db = AsyncMock()
        mock_inst = MagicMock(is_enabled=False)

        mock_inst_res = MagicMock()
        mock_inst_res.scalars.return_value.first.return_value = mock_inst
        mock_db.execute.return_value = mock_inst_res

        payload = PluginExecuteRequest(action="test_action", parameters={})

        with self.assertRaises(HTTPException) as ctx:
            await self.service.execute_plugin_action(
                mock_db, self.org_id, self.user_id, "sap-s4hana-connector", payload
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("disabled", ctx.exception.detail)

    async def test_execute_plugin_action_success_and_telemetry(self) -> None:
        """Verifies sandboxed execution dispatch and telemetry log persistence."""
        mock_db = AsyncMock()
        mock_inst = MagicMock(
            id=uuid.uuid4(),
            is_enabled=True,
            version="1.2.0",
            configuration={"api_key": "sk-test"},
        )

        mock_inst_res = MagicMock()
        mock_inst_res.scalars.return_value.first.return_value = mock_inst
        mock_db.execute.return_value = mock_inst_res

        payload = PluginExecuteRequest(
            action="summarize_chat",
            parameters={"prompt": "Summarize this ticket"},
            timeout_seconds=10.0,
        )

        result = await self.service.execute_plugin_action(
            mock_db, self.org_id, self.user_id, "ai-anthropic-claude", payload
        )

        self.assertEqual(result["plugin_id"], "ai-anthropic-claude")
        self.assertEqual(result["status"], "SUCCESS")
        self.assertIn("result", result)
        self.assertGreaterEqual(result["duration_ms"], 0.0)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

    async def test_uninstall_plugin_with_purge(self) -> None:
        """Verifies uninstallation and log purging."""
        mock_db = AsyncMock()
        mock_inst = MagicMock(id=uuid.uuid4())
        mock_plugin = MagicMock(installs_count=5)

        mock_inst_res = MagicMock()
        mock_inst_res.scalars.return_value.first.return_value = mock_inst
        mock_db.execute.return_value = mock_inst_res
        mock_db.get.return_value = mock_plugin

        result = await self.service.uninstall_plugin(
            mock_db, self.org_id, "sap-s4hana-connector", purge_data=True
        )

        self.assertTrue(result["success"])
        self.assertEqual(mock_plugin.installs_count, 4)
        mock_db.delete.assert_called_once_with(mock_inst)
        mock_db.commit.assert_awaited_once()

    async def test_plugin_analytics_aggregation(self) -> None:
        """Verifies calculation of KPIs, error rates, and category distribution."""
        mock_db = AsyncMock()

        # Mock inst query: total_installed=3, active=2
        mock_inst_res = MagicMock()
        mock_inst_res.first.return_value = (3, 2)

        # Mock log query: total_execs=100, avg_latency=54.2, error_count=4
        mock_log_res = MagicMock()
        mock_log_res.first.return_value = (100, 54.21, 4)

        # Mock cat query: [('AI', 2), ('INTEGRATION', 1)]
        mock_cat_res = MagicMock()
        mock_cat_res.all.return_value = [("AI", 2), ("INTEGRATION", 1)]

        mock_db.execute.side_effect = [mock_inst_res, mock_log_res, mock_cat_res]

        analytics = await self.service.get_plugin_analytics(mock_db, self.org_id)
        self.assertEqual(analytics["total_installed_plugins"], 3)
        self.assertEqual(analytics["active_plugins"], 2)
        self.assertEqual(analytics["total_executions"], 100)
        self.assertEqual(analytics["avg_latency_ms"], 54.21)
        self.assertEqual(analytics["error_rate"], 4.0)
        self.assertEqual(analytics["plugins_by_category"], {"AI": 2, "INTEGRATION": 1})


if __name__ == "__main__":
    unittest.main()
