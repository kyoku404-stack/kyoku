"""Backend Integration & Performance SLA Pipeline Test Suite for Phase 3.5.

Phase: 3.5
Owner: Member 4 (Integration & DevOps Lead)
Domain: tests/integration/test_plugin_pipeline.py
Specification: devdocs/p3/p3.5.txt (Chapters 1-20)
"""

import asyncio
import time
import unittest
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.app.db.session import async_session_factory
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.schemas.plugin import (
    PluginConfigUpdateRequest,
    PluginExecuteRequest,
    PluginInstallRequest,
    PluginPublishRequest,
)
from backend.app.services.plugins.contracts import (
    PluginHookBroker,
)
from backend.app.services.plugins.service import EnterprisePluginService
from tests.conftest import sync_test_engine


class TestPluginPipelineIntegration(unittest.IsolatedAsyncioTestCase):
    """Verifies end-to-end plugin execution pipeline, SLA limits, and hook dispatch concurrency."""

    @classmethod
    def setUpClass(cls) -> None:
        with Session(sync_test_engine, expire_on_commit=False) as session:
            cls.org = Organization(
                name="Pipeline Plugin Enterprise",
                domain=f"pipeline-{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            cls.user = User(
                email=f"devops-{uuid4().hex[:6]}@pipeline.com",
                hashed_password="hash",
                full_name="DevOps Lead",
                role="OrgAdmin",
                organization_id=cls.org_id,
                is_active=True,
            )
            session.add(cls.user)
            session.commit()
            session.refresh(cls.user)
            cls.user_id = cls.user.id

        cls.service = EnterprisePluginService()

    async def test_01_full_lifecycle_pipeline(self) -> None:
        """Verifies complete end-to-end lifecycle: publish -> install -> config -> execute -> telemetry -> uninstall."""
        async with async_session_factory() as db:
            # 1. Seed & Publish community extension
            plugin_slug = f"custom-ocr-{uuid4().hex[:4]}"
            pub_payload = PluginPublishRequest(
                id=plugin_slug,
                name="Deep OCR Pipeline",
                description="High-throughput OCR document pipeline",
                category="AI",
                developer="DevOps AI Guild",
                version="1.0.0",
                entry_point=f"plugins.ocr.{plugin_slug}",
                min_keep_version="3.0.0",
                max_keep_version="3.9.9",
                permissions=["READ_DOCUMENTS", "AI_INFERENCE"],
                event_hooks=["on_document_uploaded"],
                configuration_schema={"type": "object", "properties": {"api_key": {"type": "string"}}},
            )
            pub_res = await self.service.publish_marketplace_plugin(db, self.user_id, pub_payload)
            self.assertEqual(pub_res["status"], "PUBLISHED")

            # 2. Install extension into tenant workspace
            inst_payload = PluginInstallRequest(
                plugin_id=plugin_slug,
                version="1.0.0",
                configuration={"api_key": "ocr-secret-key-123"},
                approved_permissions=["READ_DOCUMENTS", "AI_INFERENCE"],
            )
            installed = await self.service.install_plugin(db, self.org_id, self.user_id, inst_payload)
            self.assertEqual(installed["plugin_id"], plugin_slug)
            self.assertTrue(installed["is_enabled"])
            self.assertEqual(len(installed["permissions"]), 2)

            # 3. Update configuration
            cfg_payload = PluginConfigUpdateRequest(configuration={"api_key": "ocr-rotated-key-456", "dpi": 300})
            updated_cfg = await self.service.update_plugin_configuration(db, self.org_id, plugin_slug, cfg_payload)
            self.assertEqual(updated_cfg["configuration"]["dpi"], 300)

            # 4. Execute sandboxed action and verify latency SLA (< 500ms for local mock)
            exec_payload = PluginExecuteRequest(
                action="extract_text",
                parameters={"document_id": "doc-999", "pages": [1, 2]},
                timeout_seconds=5.0,
            )
            exec_res = await self.service.execute_plugin_action(db, self.org_id, self.user_id, plugin_slug, exec_payload)
            self.assertEqual(exec_res["status"], "SUCCESS")
            self.assertLess(exec_res["duration_ms"], 500.0)

            # 5. Query execution telemetry logs
            logs = await self.service.list_execution_logs(db, self.org_id, plugin_slug)
            self.assertGreaterEqual(len(logs), 1)
            self.assertEqual(logs[0]["action"], "extract_text")
            self.assertEqual(logs[0]["status"], "SUCCESS")

            # 6. Verify operational analytics aggregation
            analytics = await self.service.get_plugin_analytics(db, self.org_id)
            self.assertGreaterEqual(analytics["total_installed_plugins"], 1)
            self.assertGreaterEqual(analytics["total_executions"], 1)

            # 7. Uninstall and purge
            uninst_res = await self.service.uninstall_plugin(db, self.org_id, plugin_slug, purge_data=True)
            self.assertTrue(uninst_res["success"])

    async def test_02_concurrent_sandbox_executions(self) -> None:
        """Verifies running multiple concurrent plugin executions simultaneously without deadlock."""
        claude_id = "ai-anthropic-claude"
        async with async_session_factory() as db:
            try:
                await self.service.install_plugin(
                    db,
                    self.org_id,
                    self.user_id,
                    PluginInstallRequest(plugin_id=claude_id, configuration={"model": "claude-3-5"}),
                )
            except Exception:
                pass  # May already be installed

        async def _run_worker(i: int) -> dict:
            async with async_session_factory() as task_db:
                return await self.service.execute_plugin_action(
                    task_db,
                    self.org_id,
                    self.user_id,
                    claude_id,
                    PluginExecuteRequest(
                        action="execute_inference",
                        parameters={"prompt": f"Concurrent task query {i}"},
                        timeout_seconds=5.0,
                    ),
                )

        start_t = time.perf_counter()
        tasks = [_run_worker(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        total_duration_ms = (time.perf_counter() - start_t) * 1000.0

        self.assertEqual(len(results), 5)
        for r in results:
            self.assertEqual(r["status"], "SUCCESS")

        self.assertLess(total_duration_ms, 5000.0)

    async def test_03_event_hook_broker_concurrency(self) -> None:
        """Verifies asynchronous event hook broker dispatching across multiple subscribers."""
        broker = PluginHookBroker()

        async def sub1(topic: str, payload: dict) -> dict:
            await asyncio.sleep(0.01)
            return {"handler": "sub1", "received": payload.get("id")}

        async def sub2(topic: str, payload: dict) -> dict:
            await asyncio.sleep(0.01)
            return {"handler": "sub2", "received": payload.get("id")}

        broker.subscribe("on_document_uploaded", "plugin-a", sub1)
        broker.subscribe("on_document_uploaded", "plugin-b", sub2)

        dispatch_res = await broker.dispatch_event("on_document_uploaded", {"id": "doc-test-123"})
        self.assertEqual(dispatch_res["dispatched_count"], 2)
        self.assertEqual(dispatch_res["results"]["plugin-a"]["status"], "SUCCESS")
        self.assertEqual(dispatch_res["results"]["plugin-b"]["status"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()
