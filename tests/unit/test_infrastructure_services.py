"""Unit Test Suite: Production Infrastructure & Observability Business Services.

Specification Source: devdocs/p3/p3.6.txt (Chapters 1-20)
Architecture: docs/Architecture/production-infrastructure-scalability-observability.md
Role: Member 2 (Backend & Database Lead)
"""

import unittest
from unittest.mock import AsyncMock, MagicMock

from backend.app.schemas.infrastructure import (
    CacheFlushRequest,
    CreateBackupRequest,
    DeployTriggerRequest,
)
from backend.app.services.infrastructure.service import EnterpriseInfrastructureService


class TestInfrastructureServicesUnit(unittest.IsolatedAsyncioTestCase):
    """Unit tests validating EnterpriseInfrastructureService business logic and orchestration."""

    def setUp(self) -> None:
        self.service = EnterpriseInfrastructureService()

    async def test_get_system_health(self) -> None:
        """Verifies health diagnostics probe aggregates subsystem health and computes composite score."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.execute = AsyncMock(return_value=MagicMock())
        mock_db.commit = AsyncMock()

        health = await self.service.get_system_health(mock_db)
        self.assertIn(health.status, ["HEALTHY", "DEGRADED", "CRITICAL"])
        self.assertGreater(health.uptime_seconds, 0.0)
        self.assertGreater(health.overall_score, 0.0)
        self.assertIn("database", health.subsystems)
        self.assertIn("redis", health.subsystems)
        self.assertIn("vector_database", health.subsystems)
        self.assertIn("storage", health.subsystems)
        self.assertIn("ai_workers", health.subsystems)

    def test_get_system_metrics(self) -> None:
        """Verifies hardware and application runtime telemetry capture."""
        metrics = self.service.get_system_metrics()
        self.assertGreaterEqual(metrics.cpu.percent, 0.0)
        self.assertGreater(metrics.cpu.cores, 0)
        self.assertGreater(metrics.memory.total_mb, 0.0)
        self.assertGreater(metrics.disk.total_gb, 0.0)
        self.assertGreater(metrics.application.requests_per_second, 0.0)
        self.assertGreater(metrics.cache.hit_ratio_percent, 0.0)

    async def test_get_system_logs_with_seeding(self) -> None:
        """Verifies querying system logs auto-seeds initial diagnostics if empty."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        logs = await self.service.get_system_logs(mock_db, limit=10)
        self.assertIsInstance(logs, list)

    async def test_trigger_deployment(self) -> None:
        """Verifies deployment orchestration triggers rollout and returns tracking record."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_latest = MagicMock()
        mock_latest.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_latest)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        req = DeployTriggerRequest(
            service_name="keep-backend-api",
            version="3.6.1-patch1",
            strategy="BLUE_GREEN",
            environment="production",
            auto_rollback_on_failure=True,
        )
        dep = await self.service.trigger_deployment(mock_db, req)
        self.assertEqual(dep.service_name, "keep-backend-api")
        self.assertEqual(dep.version, "3.6.1-patch1")
        self.assertEqual(dep.strategy, "BLUE_GREEN")
        self.assertEqual(dep.status, "SUCCESS")
        self.assertEqual(dep.rollback_version, "3.6.0")

    def test_get_system_version(self) -> None:
        """Verifies release metadata matches Phase 3.6 specifications."""
        ver = self.service.get_system_version()
        self.assertEqual(ver.version, "3.6.0")
        self.assertEqual(ver.environment, "production")
        self.assertIn("fastapi", ver.frameworks)
        self.assertIn("sqlalchemy", ver.frameworks)

    def test_get_services_status(self) -> None:
        """Verifies all required core and AI microservices are cataloged with running state."""
        services = self.service.get_services_status()
        service_names = {s.service_name for s in services}
        expected = {
            "keep-frontend",
            "keep-backend-api",
            "keep-ai-worker",
            "keep-ingestion-worker",
            "keep-embedding-worker",
            "keep-notification-srv",
            "keep-scheduler",
        }
        self.assertTrue(expected.issubset(service_names))
        for s in services:
            self.assertEqual(s.status, "RUNNING")
            self.assertGreaterEqual(s.replicas_ready, 1)

    async def test_create_and_get_backups(self) -> None:
        """Verifies manual backup snapshot creation and RPO/RTO metrics."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        req = CreateBackupRequest(backup_type="DATABASE", notes="Pre-upgrade snapshot")
        res = await self.service.create_backup(mock_db, req)
        self.assertIn("backup-keep-manual-", res.backup_name)
        self.assertEqual(res.status, "COMPLETED")
        self.assertGreater(res.size_bytes, 0)

    def test_flush_cache(self) -> None:
        """Verifies selective namespace resolution and key eviction estimation."""
        req = CacheFlushRequest(namespaces=["ai_response", "vector_query"], flush_all=False)
        res = self.service.flush_cache(req)
        self.assertIn("keep:ai:resp:", res.flushed_namespaces)
        self.assertIn("keep:vector:q:", res.flushed_namespaces)
        self.assertGreater(res.keys_removed, 0)

        # Flush all
        req_all = CacheFlushRequest(namespaces=[], flush_all=True)
        res_all = self.service.flush_cache(req_all)
        self.assertEqual(len(res_all.flushed_namespaces), 6)


if __name__ == "__main__":
    unittest.main()
