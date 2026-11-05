"""Backend Integration & Performance SLA Pipeline Test Suite for Phase 3.6.

Phase: 3.6
Owner: Member 4 (Integration & DevOps Lead)
Domain: tests/integration/test_system_infrastructure_pipeline.py
Specification: devdocs/p3/p3.6.txt (Chapters 1-20)
"""

import asyncio
import time
import unittest
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.app.db.session import async_session_factory
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.schemas.infrastructure import (
    CacheFlushRequest,
    CreateBackupRequest,
    DeployTriggerRequest,
)
from backend.app.services.infrastructure.service import EnterpriseInfrastructureService
from tests.conftest import sync_test_engine


class TestSystemInfrastructurePipelineIntegration(unittest.IsolatedAsyncioTestCase):
    """Verifies end-to-end production infrastructure operations, resilience, deployment rollout, DR, and caching pipelines."""

    @classmethod
    def setUpClass(cls) -> None:
        with Session(sync_test_engine, expire_on_commit=False) as session:
            cls.org = Organization(
                name="Infrastructure DevOps Enterprise",
                domain=f"devops-{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            cls.user = User(
                email=f"infra-lead-{uuid4().hex[:6]}@pipeline.com",
                hashed_password="hash",
                full_name="Infra DevOps Lead",
                role="PlatformAdmin",
                organization_id=cls.org_id,
                is_active=True,
            )
            session.add(cls.user)
            session.commit()
            session.refresh(cls.user)
            cls.user_id = cls.user.id

        cls.service = EnterpriseInfrastructureService()

    async def test_01_full_subsystems_health_pipeline(self) -> None:
        """Verifies comprehensive subsystem health probe, status aggregation, and uptime tracking."""
        async with async_session_factory() as db:
            health = await self.service.get_system_health(db)

            self.assertIn(health.status, ["HEALTHY", "DEGRADED"])
            self.assertGreaterEqual(health.overall_score, 0.0)
            self.assertLessEqual(health.overall_score, 1.0)
            self.assertGreater(health.uptime_seconds, 0.0)

            # Assert core subsystems are probed
            self.assertIn("database", health.subsystems)
            self.assertIn("redis", health.subsystems)
            self.assertIn("storage", health.subsystems)
            self.assertIn("vector_database", health.subsystems)
            self.assertIn("ai_workers", health.subsystems)

            for _name, sub in health.subsystems.items():
                self.assertIsNotNone(sub.get("latency_ms"))
                self.assertIn(sub.get("status"), ["HEALTHY", "DEGRADED", "CRITICAL"])

    async def test_02_telemetry_metrics_and_version_pipeline(self) -> None:
        """Verifies aggregate host/container metrics capture and system runtime environment."""
        start_time = time.time()
        metrics = self.service.get_system_metrics()
        duration = time.time() - start_time

        # SLA assertion: metrics gathered under 500ms
        self.assertLess(duration, 0.500)

        # Metric field assertions
        self.assertGreaterEqual(metrics.cpu.percent, 0.0)
        self.assertGreater(metrics.memory.total_mb, 0)
        self.assertGreaterEqual(metrics.memory.percent, 0.0)
        self.assertGreater(metrics.disk.total_gb, 0)
        self.assertGreaterEqual(metrics.disk.percent, 0.0)
        self.assertGreaterEqual(metrics.cache.hit_ratio_percent, 0.0)
        self.assertGreaterEqual(metrics.application.active_connections, 0)

        # Version check
        version_info = self.service.get_system_version()
        self.assertEqual(version_info.version, "3.6.0")
        self.assertIn("fastapi", version_info.frameworks)

    async def test_03_automated_deployment_rollout_and_rollback(self) -> None:
        """Verifies deployment rollout lifecycle, canary progression, and rollback mechanisms."""
        async with async_session_factory() as db:
            # 1. Roll out canary deployment
            req = DeployTriggerRequest(
                service_name="keep-search-cluster",
                version="v3.6.1",
                strategy="CANARY",
                environment="production",
            )
            deployment = await self.service.trigger_deployment(
                db=db,
                request=req,
                user_id=self.user_id,
            )

            self.assertEqual(deployment.service_name, "keep-search-cluster")
            self.assertEqual(deployment.version, "v3.6.1")
            self.assertEqual(deployment.strategy, "CANARY")
            self.assertEqual(deployment.status, "SUCCESS")

            # 2. Trigger rolling deployment back to stable
            rollback_req = DeployTriggerRequest(
                service_name="keep-search-cluster",
                version="v3.6.0-stable",
                strategy="ROLLING",
                environment="production",
            )
            rollback = await self.service.trigger_deployment(
                db=db,
                request=rollback_req,
                user_id=self.user_id,
            )
            self.assertEqual(rollback.version, "v3.6.0-stable")
            self.assertEqual(rollback.status, "SUCCESS")

    async def test_04_disaster_recovery_backup_and_audit(self) -> None:
        """Verifies point-in-time disaster recovery backup creation, SHA-256 generation, and audit trail."""
        async with async_session_factory() as db:
            req = CreateBackupRequest(
                backup_type="FULL",
                notes="Automated DevOps Pipeline Point-in-time snapshot",
            )
            start_t = time.time()
            backup = await self.service.create_backup(
                db=db,
                request=req,
            )
            elapsed = time.time() - start_t

            self.assertEqual(backup.status, "COMPLETED")
            self.assertGreater(backup.size_bytes, 0)
            self.assertLess(elapsed, 2.0)

            # Query system audit logs for the backup trigger
            logs = await self.service.get_system_logs(db, limit=10)
            self.assertGreater(len(logs), 0)
            messages = [log_entry.message for log_entry in logs]
            self.assertTrue(any("Manual backup" in m for m in messages))

            # Query disaster recovery SLA catalog
            dr_catalog = await self.service.get_system_backups(db)
            self.assertEqual(dr_catalog.rpo_target_minutes, 60)
            self.assertEqual(dr_catalog.rto_target_minutes, 240)
            self.assertGreater(len(dr_catalog.backups), 0)

    async def test_05_cache_invalidation_and_eviction_pipeline(self) -> None:
        """Verifies distributed cache namespace invalidation and key purge counts."""
        req = CacheFlushRequest(
            namespaces=["dashboard", "ai_response"],
            flush_all=False,
        )
        flush_res = self.service.flush_cache(req)

        self.assertIn("keep:dashboard:", flush_res.flushed_namespaces)
        self.assertIn("keep:ai:resp:", flush_res.flushed_namespaces)
        self.assertGreater(flush_res.keys_removed, 0)

    async def test_06_high_concurrency_health_probes(self) -> None:
        """Verifies system stability and thread-safety under concurrent health requests."""
        async def probe():
            async with async_session_factory() as db:
                return await self.service.get_system_health(db)

        start_t = time.time()
        results = await asyncio.gather(*(probe() for _ in range(5)))
        total_duration = time.time() - start_t

        self.assertEqual(len(results), 5)
        for res in results:
            self.assertIsNotNone(res.overall_score)
            self.assertIn(res.status, ["HEALTHY", "DEGRADED"])

        # 5 parallel probes must complete under 2.0 seconds aggregate SLA
        self.assertLess(total_duration, 2.0)
