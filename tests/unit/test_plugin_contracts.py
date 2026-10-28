"""Unit Test Suite: Plugin SDK, Extension Framework & Developer Ecosystem Contracts.

Specification Source: devdocs/p3/p3.5.txt (Chapters 1-20)
Architecture: docs/Architecture/plugin-sdk-extension-framework.md
ADR Reference: ADR-059, ADR-060, ADR-061
Role: Member 1 (Project Lead & AI Architect)
"""

import asyncio
import unittest

from backend.app.services.ai.interfaces import ORG_ADMIN_PERMISSIONS, ROLE_PERMISSIONS, AIPermission
from backend.app.services.plugins.contracts import (
    BasePlugin,
    CapabilityPermissionGuard,
    PluginCapability,
    PluginCategory,
    PluginExecutionInput,
    PluginHookBroker,
    PluginLogStatus,
    PluginManifest,
    PluginManifestValidator,
    PluginSandboxRunner,
    SampleClaudeAIPlugin,
    SampleSAPInvoicePlugin,
    SemanticVersionValidator,
)


class TestPluginContractsUnit(unittest.IsolatedAsyncioTestCase):
    """Unit tests validating core Plugin SDK specifications, algorithms, and sandbox boundaries."""

    # --------------------------------------------------------------------------
    # 1. Semantic Versioning & Compatibility
    # --------------------------------------------------------------------------
    def test_semver_parsing_and_compatibility(self) -> None:
        """Verifies parsing of SemVer strings and compatibility evaluation."""
        major, minor, patch = SemanticVersionValidator.parse("3.5.1")
        self.assertEqual((major, minor, patch), (3, 5, 1))

        # Test valid range
        self.assertTrue(SemanticVersionValidator.is_compatible("3.5.0", "3.0.0", "3.9.9"))
        self.assertTrue(SemanticVersionValidator.is_compatible("3.0.0", "3.0.0", "4.0.0"))
        self.assertTrue(SemanticVersionValidator.is_compatible("4.0.0", "3.0.0", "4.0.0"))

        # Test out of range
        self.assertFalse(SemanticVersionValidator.is_compatible("2.9.9", "3.0.0", "4.0.0"))
        self.assertFalse(SemanticVersionValidator.is_compatible("4.1.0", "3.0.0", "4.0.0"))

        # Test invalid string
        with self.assertRaises(ValueError):
            SemanticVersionValidator.parse("invalid-version")

    # --------------------------------------------------------------------------
    # 2. Manifest Validation & Checksum
    # --------------------------------------------------------------------------
    def test_manifest_validation_success_and_checksum(self) -> None:
        """Verifies manifest schema parsing, checksum generation, and serialization."""
        raw_manifest = {
            "id": "custom-ocr-engine",
            "name": "Enterprise Optical Character Recognition Engine",
            "version": "1.0.4",
            "developer": "VisionAI Labs",
            "category": "AI",
            "entry_point": "ocr_plugin:OCREngine",
            "min_keep_version": "3.2.0",
            "max_keep_version": "3.9.0",
            "permissions": ["Documents.Read", "AI.Query"],
            "event_hooks": ["document.uploaded"],
            "configuration_schema": {"dpi": {"type": "integer", "default": 300}},
        }

        manifest = PluginManifestValidator.validate(raw_manifest, current_platform_version="3.5.0")
        self.assertEqual(manifest.id, "custom-ocr-engine")
        self.assertEqual(manifest.category, PluginCategory.AI)
        self.assertEqual(len(manifest.permissions), 2)

        # Verify checksum calculation
        checksum = manifest.calculate_checksum()
        self.assertEqual(len(checksum), 64)  # SHA-256 length

        # Serialization roundtrip
        d = manifest.to_dict()
        self.assertEqual(d["id"], "custom-ocr-engine")
        self.assertEqual(d["category"], "AI")

    def test_manifest_validation_missing_fields_and_incompatible_version(self) -> None:
        """Verifies validation failure on missing fields or platform version incompatibility."""
        # Missing id
        with self.assertRaises(ValueError) as ctx:
            PluginManifestValidator.validate({"name": "No ID Plugin", "version": "1.0.0"})
        self.assertIn("Missing mandatory manifest field", str(ctx.exception))

        # Incompatible version
        incompatible_manifest = {
            "id": "legacy-plugin",
            "name": "Legacy Tool",
            "version": "0.9.0",
            "developer": "Legacy Dev",
            "category": "WORKFLOW",
            "entry_point": "legacy:main",
            "min_keep_version": "1.0.0",
            "max_keep_version": "2.5.0",
        }
        with self.assertRaises(ValueError) as ctx:
            PluginManifestValidator.validate(incompatible_manifest, current_platform_version="3.5.0")
        self.assertIn("is incompatible with platform version", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 3. Capability Permission Enforcement
    # --------------------------------------------------------------------------
    def test_capability_permission_guard(self) -> None:
        """Verifies capability authorization gating and security violation exceptions."""
        granted = [PluginCapability.DOCUMENTS_READ.value, PluginCapability.AI_QUERY.value]

        # Allowed
        self.assertTrue(
            CapabilityPermissionGuard.verify_capability(
                granted,
                PluginCapability.DOCUMENTS_READ,
                plugin_id="test-plugin",
            )
        )

        # Denied
        with self.assertRaises(PermissionError) as ctx:
            CapabilityPermissionGuard.verify_capability(
                granted,
                PluginCapability.NETWORK_OUTBOUND,
                plugin_id="test-plugin",
            )
        self.assertIn("Security Capability Violation", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 4. Sandbox Runner & Timeout Boundary
    # --------------------------------------------------------------------------
    async def test_sandbox_runner_success(self) -> None:
        """Verifies sandboxed execution collects metrics and handles success cleanly."""
        plugin = SampleClaudeAIPlugin()
        plugin.initialize({"model": "claude-3-5-sonnet-20241022"})

        runner = PluginSandboxRunner(default_timeout_seconds=5.0)
        inp = PluginExecutionInput(
            plugin_id="ai-anthropic-claude",
            action="inference",
            parameters={"prompt": "Summarize Q3 financial results."},
        )

        output = await runner.execute_sandboxed(plugin, inp)
        self.assertEqual(output.status, PluginLogStatus.SUCCESS)
        self.assertEqual(output.plugin_id, "ai-anthropic-claude")
        self.assertIn("tokens_used", output.result_data)
        self.assertGreater(output.duration_ms, 0.0)

    async def test_sandbox_runner_timeout_boundary(self) -> None:
        """Verifies runner trips TIMEOUT status when plugin exceeds SLA."""
        class SlowHangingPlugin(BasePlugin):
            async def execute(self, execution_input: PluginExecutionInput) -> dict:
                await asyncio.sleep(2.0)
                return {"done": True}

        manifest = PluginManifest(
            id="slow-plugin",
            name="Slow Plugin",
            version="1.0.0",
            developer="Test",
            description="",
            category=PluginCategory.AI,
            entry_point="slow:plugin",
        )
        plugin = SlowHangingPlugin(manifest)

        runner = PluginSandboxRunner()
        inp = PluginExecutionInput(
            plugin_id="slow-plugin",
            action="test",
            timeout_seconds=0.1,  # Strict timeout
        )

        output = await runner.execute_sandboxed(plugin, inp)
        self.assertEqual(output.status, PluginLogStatus.TIMEOUT)
        self.assertIn("exceeded timeout SLA", output.error_message)

    async def test_sandbox_runner_exception_isolation(self) -> None:
        """Verifies plugin errors are trapped without crashing the host process."""
        class CrashPlugin(BasePlugin):
            async def execute(self, execution_input: PluginExecutionInput) -> dict:
                raise RuntimeError("Intentional plugin logic crash")

        manifest = PluginManifest(
            id="crash-plugin",
            name="Crash Plugin",
            version="1.0.0",
            developer="Test",
            description="",
            category=PluginCategory.ANALYTICS,
            entry_point="crash:plugin",
        )
        plugin = CrashPlugin(manifest)

        runner = PluginSandboxRunner()
        inp = PluginExecutionInput(plugin_id="crash-plugin", action="calc")
        output = await runner.execute_sandboxed(plugin, inp)

        self.assertEqual(output.status, PluginLogStatus.ERROR)
        self.assertIn("Intentional plugin logic crash", output.error_message)

    # --------------------------------------------------------------------------
    # 5. Plugin Hook Broker & Event Dispatch
    # --------------------------------------------------------------------------
    async def test_plugin_hook_broker_dispatch(self) -> None:
        """Verifies event hook subscription and concurrent asynchronous dispatch."""
        broker = PluginHookBroker()

        received_events: list[str] = []

        async def handler_a(topic: str, payload: dict) -> dict:
            received_events.append(f"A:{topic}:{payload.get('doc_id')}")
            return {"handler": "A"}

        async def handler_b(topic: str, payload: dict) -> dict:
            received_events.append(f"B:{topic}:{payload.get('doc_id')}")
            return {"handler": "B"}

        broker.subscribe("document.uploaded", "plugin-a", handler_a)
        broker.subscribe("document.uploaded", "plugin-b", handler_b)

        res = await broker.dispatch_event("document.uploaded", {"doc_id": "doc-99"})
        self.assertEqual(res["dispatched_count"], 2)
        self.assertIn("plugin-a", res["results"])
        self.assertIn("plugin-b", res["results"])
        self.assertIn("A:document.uploaded:doc-99", received_events)
        self.assertIn("B:document.uploaded:doc-99", received_events)

        # Test unsubscribe
        broker.unsubscribe_plugin("plugin-a")
        res2 = await broker.dispatch_event("document.uploaded", {"doc_id": "doc-100"})
        self.assertEqual(res2["dispatched_count"], 1)
        self.assertIn("plugin-b", res2["results"])
        self.assertNotIn("plugin-a", res2["results"])

    # --------------------------------------------------------------------------
    # 6. Sample Plugin Implementations
    # --------------------------------------------------------------------------
    async def test_sample_sap_invoice_plugin(self) -> None:
        """Verifies SAP ERP integration reference plugin execution and event hooks."""
        sap_plugin = SampleSAPInvoicePlugin()
        sap_plugin.initialize({"endpoint_url": "https://sap.acme-corp.com/api"})

        runner = PluginSandboxRunner()
        inp = PluginExecutionInput(
            plugin_id="sap-s4hana-connector",
            action="sync_invoices",
            parameters={"limit": 10},
        )
        out = await runner.execute_sandboxed(sap_plugin, inp)
        self.assertEqual(out.status, PluginLogStatus.SUCCESS)
        self.assertEqual(out.result_data["synced_count"], 10)
        self.assertEqual(len(out.result_data["entities"]), 5)

        # Hook invocation
        hook_res = await sap_plugin.on_event("document.uploaded", {"document_id": "doc-abc"})
        self.assertEqual(hook_res["status"], "SYNCED")
        self.assertEqual(hook_res["doc_id"], "doc-abc")

    # --------------------------------------------------------------------------
    # 7. RBAC Plugin Permissions
    # --------------------------------------------------------------------------
    def test_rbac_plugin_permissions_integration(self) -> None:
        """Verifies Phase 3.5 plugin permissions are registered in role hierarchies."""
        self.assertIn(AIPermission.PLUGIN_VIEW.value, ORG_ADMIN_PERMISSIONS)
        self.assertIn(AIPermission.PLUGIN_MANAGE.value, ORG_ADMIN_PERMISSIONS)
        self.assertIn(AIPermission.PLUGIN_INSTALL.value, ORG_ADMIN_PERMISSIONS)
        self.assertIn(AIPermission.PLUGIN_EXECUTE.value, ORG_ADMIN_PERMISSIONS)

        # Check Viewer has view only
        viewer_perms = ROLE_PERMISSIONS["Viewer"]
        self.assertIn(AIPermission.PLUGIN_VIEW.value, viewer_perms)
        self.assertNotIn(AIPermission.PLUGIN_MANAGE.value, viewer_perms)
        self.assertNotIn(AIPermission.PLUGIN_INSTALL.value, viewer_perms)


if __name__ == "__main__":
    unittest.main()
