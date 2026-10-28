"""Unit Test Suite for Phase 3.1 Enterprise Integrations & Connector Framework Contracts.

Verifies:
1. Auth credentials expiration and validation.
2. Document normalizer text cleaning, permission mapping, and envelope formatting.
3. Cryptographic SHA-256 incremental change detection (added, updated, deleted, unchanged).
4. Synchronization scheduler interval calculation and due evaluation.
5. Mock external platform adapter lifecycle (connect, authenticate, discover, fetch, disconnect).

Specification: devdocs/p3/p3.1.txt & docs/Architecture/enterprise-integrations-connector-framework.md
Author: Member 1 (Project Lead & AI Architect)
"""

import unittest
from datetime import UTC, datetime, timedelta

from backend.app.services.connectors.contracts import (
    AuthCredentials,
    AuthType,
    DefaultChangeDetector,
    DefaultDocumentNormalizer,
    DefaultSyncScheduler,
    ExternalResourceItem,
    MockExternalPlatformAdapter,
    NormalizedPermissionLevel,
    PlatformCategory,
    PlatformType,
    SyncAction,
)


class TestConnectorFrameworkContracts(unittest.TestCase):
    """Unit tests for Phase 3.1 connector interfaces and reference algorithms."""

    def setUp(self) -> None:
        self.normalizer = DefaultDocumentNormalizer()
        self.change_detector = DefaultChangeDetector()
        self.scheduler = DefaultSyncScheduler()
        self.mock_adapter = MockExternalPlatformAdapter(PlatformType.GOOGLE_DRIVE)

    # --------------------------------------------------------------------------
    # 1. AuthCredentials Tests
    # --------------------------------------------------------------------------

    def test_01_auth_credentials_validity_and_expiry(self) -> None:
        """Verifies token expiration logic and attribute initialization."""
        now = datetime.now(UTC)
        valid_creds = AuthCredentials(
            auth_type=AuthType.OAUTH2,
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_in=3600,
            authenticated_at=now,
        )
        self.assertFalse(valid_creds.is_expired())

        # Expired credentials
        expired_creds = AuthCredentials(
            auth_type=AuthType.OAUTH2,
            access_token="expired-token",
            expires_in=300,
            authenticated_at=now - timedelta(seconds=600),
        )
        self.assertTrue(expired_creds.is_expired())

    # --------------------------------------------------------------------------
    # 2. Document Normalizer Tests
    # --------------------------------------------------------------------------

    def test_02_normalizer_clean_text_and_html_stripping(self) -> None:
        """Verifies HTML tags are stripped and special characters unescaped."""
        raw_html = "<p>Welcome to <strong>KEEP</strong> &amp; Enterprise RAG!</p>"
        cleaned = self.normalizer.clean_text(raw_html)
        self.assertEqual(cleaned, "Welcome to KEEP & Enterprise RAG!")

        # None and empty handling
        self.assertEqual(self.normalizer.clean_text(None), "")
        self.assertEqual(self.normalizer.clean_text("   "), "")

    def test_03_permission_mapping(self) -> None:
        """Verifies platform ACLs map to appropriate KEEP RBAC roles."""
        # Admin / Owner
        level, roles = self.normalizer.map_permissions(["owner", "reader"])
        self.assertEqual(level, NormalizedPermissionLevel.ADMIN)
        self.assertIn("SuperAdmin", roles)
        self.assertIn("OrgAdmin", roles)

        # Editor / Write
        level, roles = self.normalizer.map_permissions(["contributor", "write"])
        self.assertEqual(level, NormalizedPermissionLevel.EDITOR)
        self.assertIn("Manager", roles)
        self.assertNotIn("Member", roles)

        # Public
        level, roles = self.normalizer.map_permissions(["public"])
        self.assertEqual(level, NormalizedPermissionLevel.PUBLIC)
        self.assertIn("Guest", roles)

        # Default viewer
        level, roles = self.normalizer.map_permissions(["unknown_role"])
        self.assertEqual(level, NormalizedPermissionLevel.READ)
        self.assertIn("Member", roles)

    def test_04_normalize_external_item(self) -> None:
        """Verifies complete conversion of ExternalResourceItem into NormalizedDocument."""
        now = datetime.now(UTC)
        raw_item = ExternalResourceItem(
            external_id="gdrive-101",
            name="<h1>Product Roadmap 2027</h1>",
            mime_type="text/markdown",
            content_text="Detailed product milestones and quarterly OKRs.",
            source_url="https://drive.google.com/open?id=101",
            author="lisa.wong@enterprise.com",
            department="Product",
            created_at=now - timedelta(days=5),
            modified_at=now,
            version="3",
            external_permissions=["editor"],
        )

        doc = self.normalizer.normalize(raw_item, PlatformType.GOOGLE_DRIVE, PlatformCategory.CLOUD_STORAGE)

        self.assertEqual(doc.external_id, "gdrive-101")
        self.assertEqual(doc.title, "Product Roadmap 2027")
        self.assertEqual(doc.source_platform, PlatformType.GOOGLE_DRIVE)
        self.assertEqual(doc.platform_category, PlatformCategory.CLOUD_STORAGE)
        self.assertEqual(doc.permission_level, NormalizedPermissionLevel.EDITOR)
        self.assertIn("product", doc.tags)
        self.assertIn("google_drive", doc.tags)
        self.assertTrue(len(doc.checksum) == 64)  # SHA-256 hex string

    # --------------------------------------------------------------------------
    # 3. Incremental Change Detection Tests
    # --------------------------------------------------------------------------

    def test_05_incremental_change_detection_lifecycle(self) -> None:
        """Verifies detection of ADDED, UPDATED, DELETED, and SKIPPED resources."""
        # External system currently has item1, item2 (modified), and item3 (new)
        item1 = ExternalResourceItem(
            external_id="res-1",
            name="Policy Alpha",
            content_text="Security rules version 1",
            mime_type="text/plain",
        )
        item2 = ExternalResourceItem(
            external_id="res-2",
            name="Policy Beta",
            content_text="Security rules version 2 (updated text)",
            mime_type="text/plain",
        )
        item3 = ExternalResourceItem(
            external_id="res-3",
            name="Policy Gamma",
            content_text="Brand new security rule",
            mime_type="text/plain",
        )

        cs1 = self.change_detector.compute_checksum("Security rules version 1", "text/plain")
        cs2_old = self.change_detector.compute_checksum("Old outdated rules", "text/plain")
        cs4_deleted = self.change_detector.compute_checksum("Old removed document", "text/plain")

        # Known checksums from previous sync: res-1 (unchanged), res-2 (old content), res-4 (now deleted)
        known_state = {
            "res-1": cs1,
            "res-2": cs2_old,
            "res-4": cs4_deleted,
        }

        result = self.change_detector.detect_changes([item1, item2, item3], known_state)

        self.assertEqual(result.total_detected, 4)
        self.assertEqual(result.added_count, 1)      # res-3
        self.assertEqual(result.updated_count, 1)    # res-2
        self.assertEqual(result.unchanged_count, 1)  # res-1
        self.assertEqual(result.deleted_count, 1)    # res-4

        actions = {item.external_id: item.action for item in result.items}
        self.assertEqual(actions["res-1"], SyncAction.SKIPPED)
        self.assertEqual(actions["res-2"], SyncAction.UPDATED)
        self.assertEqual(actions["res-3"], SyncAction.ADDED)
        self.assertEqual(actions["res-4"], SyncAction.DELETED)

    # --------------------------------------------------------------------------
    # 4. Synchronization Scheduler Tests
    # --------------------------------------------------------------------------

    def test_06_sync_scheduler_interval_and_due_check(self) -> None:
        """Verifies calculation of next synchronization timestamp and due status."""
        base_time = datetime(2026, 10, 28, 12, 0, 0, tzinfo=UTC)
        next_sync = self.scheduler.calculate_next_sync(base_time, 60)
        self.assertEqual(next_sync, datetime(2026, 10, 28, 13, 0, 0, tzinfo=UTC))

        # First sync (None) is always due
        self.assertTrue(self.scheduler.is_sync_due(None, 60))

        # Sync 30 minutes ago with 60 min interval is NOT due
        past_recent = datetime.now(UTC) - timedelta(minutes=30)
        self.assertFalse(self.scheduler.is_sync_due(past_recent, 60))

        # Sync 90 minutes ago with 60 min interval IS due
        past_overdue = datetime.now(UTC) - timedelta(minutes=90)
        self.assertTrue(self.scheduler.is_sync_due(past_overdue, 60))

    # --------------------------------------------------------------------------
    # 5. Mock External Platform Adapter Tests
    # --------------------------------------------------------------------------

    def test_07_mock_adapter_lifecycle(self) -> None:
        """Verifies connect, authenticate, discover, fetch, and disconnect on Mock Adapter."""
        creds = AuthCredentials(
            auth_type=AuthType.OAUTH2,
            access_token="mock-valid-oauth-token",
        )

        # Connection initially false
        self.assertFalse(self.mock_adapter.test_connection())

        # Authenticate and connect
        auth_res = self.mock_adapter.authenticate(creds)
        self.assertTrue(auth_res["authenticated"])
        self.assertTrue(self.mock_adapter.test_connection())

        # Discover resources
        resources = self.mock_adapter.discover_resources()
        self.assertGreaterEqual(len(resources), 3)

        # Fetch individual resource
        first_id = resources[0].external_id
        fetched = self.mock_adapter.fetch_resource_content(first_id)
        self.assertEqual(fetched.external_id, first_id)
        self.assertTrue(len(fetched.content_text) > 0)

        # Disconnect
        self.mock_adapter.disconnect()
        self.assertFalse(self.mock_adapter.test_connection())

        # Calling fetch while disconnected raises ConnectionError
        with self.assertRaises(ConnectionError):
            self.mock_adapter.fetch_resource_content(first_id)


if __name__ == "__main__":
    unittest.main()
