"""Unit Test Suite: Production Infrastructure, Scalability, Observability & High Availability Contracts.

Specification Source: devdocs/p3/p3.6.txt (Chapters 1-20)
Architecture: docs/Architecture/production-infrastructure-scalability-observability.md
ADR Reference: ADR-062, ADR-063, ADR-064
Role: Member 1 (Project Lead & AI Architect)
"""

import unittest
from datetime import UTC, datetime, timedelta

from backend.app.services.ai.interfaces import (
    ORG_ADMIN_PERMISSIONS,
    PROJECT_MANAGER_PERMISSIONS,
    ROLE_PERMISSIONS,
    AIPermission,
)
from backend.app.services.infrastructure.contracts import (
    CacheNamespace,
    DeploymentOrchestrator,
    DeploymentSpec,
    DeploymentStatus,
    DeploymentStrategy,
    DisasterRecoveryEvaluator,
    HealthScoringEngine,
    LogLevel,
    MultiTierCacheManager,
    ServiceHealthStatus,
    SubsystemHealth,
)


class TestInfrastructureContractsUnit(unittest.TestCase):
    """Unit tests validating production infrastructure contracts, scoring engines, and SLAs."""

    # --------------------------------------------------------------------------
    # 1. Health Scoring Engine Tests
    # --------------------------------------------------------------------------
    def test_health_scoring_all_healthy(self) -> None:
        """Verifies composite assessment reports HEALTHY with near 1.0 score when all subsystems are operational."""
        subsystems = {
            "database": SubsystemHealth("database", ServiceHealthStatus.HEALTHY, latency_ms=2.1),
            "redis": SubsystemHealth("redis", ServiceHealthStatus.HEALTHY, latency_ms=0.8),
            "vector_database": SubsystemHealth("vector_database", ServiceHealthStatus.HEALTHY, latency_ms=5.4),
            "storage": SubsystemHealth("storage", ServiceHealthStatus.HEALTHY, latency_ms=1.2),
            "ai_workers": SubsystemHealth("ai_workers", ServiceHealthStatus.HEALTHY, latency_ms=12.0),
        }
        assessment = HealthScoringEngine.evaluate(subsystems, uptime_seconds=86400.0)
        self.assertEqual(assessment.status, ServiceHealthStatus.HEALTHY)
        self.assertGreaterEqual(assessment.overall_score, 0.95)
        self.assertEqual(assessment.uptime_seconds, 86400.0)

    def test_health_scoring_latency_penalty(self) -> None:
        """Verifies that high subsystem latency reduces the composite score."""
        normal_subsystems = {
            "database": SubsystemHealth("database", ServiceHealthStatus.HEALTHY, latency_ms=5.0),
            "redis": SubsystemHealth("redis", ServiceHealthStatus.HEALTHY, latency_ms=1.0),
        }
        high_latency_subsystems = {
            "database": SubsystemHealth("database", ServiceHealthStatus.HEALTHY, latency_ms=250.0),
            "redis": SubsystemHealth("redis", ServiceHealthStatus.HEALTHY, latency_ms=1.0),
        }
        score_normal = HealthScoringEngine.evaluate(normal_subsystems).overall_score
        score_delayed = HealthScoringEngine.evaluate(high_latency_subsystems).overall_score
        self.assertGreater(score_normal, score_delayed)

    def test_health_scoring_critical_database_veto(self) -> None:
        """Verifies that a critical database status vetoes the platform into CRITICAL."""
        subsystems = {
            "database": SubsystemHealth("database", ServiceHealthStatus.CRITICAL, latency_ms=0.0),
            "redis": SubsystemHealth("redis", ServiceHealthStatus.HEALTHY, latency_ms=0.5),
            "vector_database": SubsystemHealth("vector_database", ServiceHealthStatus.HEALTHY, latency_ms=2.0),
            "storage": SubsystemHealth("storage", ServiceHealthStatus.HEALTHY, latency_ms=1.0),
            "ai_workers": SubsystemHealth("ai_workers", ServiceHealthStatus.HEALTHY, latency_ms=5.0),
        }
        assessment = HealthScoringEngine.evaluate(subsystems)
        self.assertEqual(assessment.status, ServiceHealthStatus.CRITICAL)

    def test_health_scoring_degraded(self) -> None:
        """Verifies that degraded components yield a DEGRADED composite rating."""
        subsystems = {
            "database": SubsystemHealth("database", ServiceHealthStatus.HEALTHY, latency_ms=10.0),
            "redis": SubsystemHealth("redis", ServiceHealthStatus.DEGRADED, latency_ms=80.0),
            "vector_database": SubsystemHealth("vector_database", ServiceHealthStatus.DEGRADED, latency_ms=90.0),
            "storage": SubsystemHealth("storage", ServiceHealthStatus.HEALTHY, latency_ms=5.0),
            "ai_workers": SubsystemHealth("ai_workers", ServiceHealthStatus.HEALTHY, latency_ms=15.0),
        }
        assessment = HealthScoringEngine.evaluate(subsystems)
        self.assertEqual(assessment.status, ServiceHealthStatus.DEGRADED)
        self.assertGreaterEqual(assessment.overall_score, 0.65)
        self.assertLess(assessment.overall_score, 0.90)

    # --------------------------------------------------------------------------
    # 2. Disaster Recovery Evaluator Tests
    # --------------------------------------------------------------------------
    def test_dr_rpo_drift_and_compliance(self) -> None:
        """Verifies RPO drift computation and SLA compliance evaluation."""
        now = datetime.now(UTC)
        recent_backup = now - timedelta(minutes=25)
        stale_backup = now - timedelta(minutes=90)

        # Compliant scenario (25m <= 60m RPO)
        drift_recent = DisasterRecoveryEvaluator.calculate_rpo_drift(recent_backup, now)
        self.assertAlmostEqual(drift_recent, 1500, delta=5)
        eval_recent = DisasterRecoveryEvaluator.evaluate_compliance(drift_recent, rpo_target_seconds=3600)
        self.assertTrue(eval_recent["compliant"])
        self.assertFalse(eval_recent["alert_required"])

        # Non-compliant scenario (90m > 60m RPO)
        drift_stale = DisasterRecoveryEvaluator.calculate_rpo_drift(stale_backup, now)
        self.assertAlmostEqual(drift_stale, 5400, delta=5)
        eval_stale = DisasterRecoveryEvaluator.evaluate_compliance(drift_stale, rpo_target_seconds=3600)
        self.assertFalse(eval_stale["compliant"])
        self.assertTrue(eval_stale["alert_required"])
        self.assertEqual(eval_stale["alert_severity"], LogLevel.ERROR)

    def test_dr_checksum_verification(self) -> None:
        """Verifies SHA-256 integrity check against corrupt or valid payload."""
        sample_data = b"PostgreSQL database snapshot binary stream contents"
        import hashlib
        valid_checksum = hashlib.sha256(sample_data).hexdigest()

        self.assertTrue(DisasterRecoveryEvaluator.verify_checksum(sample_data, valid_checksum))
        self.assertFalse(DisasterRecoveryEvaluator.verify_checksum(sample_data, "badchecksum" + "0" * 53))

    # --------------------------------------------------------------------------
    # 3. Multi-Tier Cache Manager Tests
    # --------------------------------------------------------------------------
    def test_cache_key_building_and_ttl(self) -> None:
        """Verifies deterministic Redis cache keys and assigned TTL boundaries."""
        key = MultiTierCacheManager.build_cache_key(CacheNamespace.AI_RESPONSE, "prompt_hash_123")
        self.assertEqual(key, "keep:ai:resp:prompt_hash_123")

        ttl = MultiTierCacheManager.get_ttl(CacheNamespace.AI_RESPONSE)
        self.assertEqual(ttl, 21600)  # 6 Hours

        session_ttl = MultiTierCacheManager.get_ttl(CacheNamespace.SESSION)
        self.assertEqual(session_ttl, 86400)  # 24 Hours

    def test_cache_query_fingerprinting(self) -> None:
        """Verifies consistent hashing of query dictionaries regardless of key ordering."""
        query_a = {"user": "usr-1", "doc_id": "doc-5", "mode": "semantic"}
        query_b = {"mode": "semantic", "doc_id": "doc-5", "user": "usr-1"}

        hash_a = MultiTierCacheManager.compute_query_hash(query_a)
        hash_b = MultiTierCacheManager.compute_query_hash(query_b)
        self.assertEqual(hash_a, hash_b)
        self.assertEqual(len(hash_a), 64)

    def test_cache_namespace_flush_resolution(self) -> None:
        """Verifies resolution of canonical names and flush_all wildcard operations."""
        # Targeted namespaces
        targets = ["ai_response", "dashboard"]
        resolved = MultiTierCacheManager.resolve_namespaces_to_flush(targets)
        self.assertIn(CacheNamespace.AI_RESPONSE.value, resolved)
        self.assertIn(CacheNamespace.DASHBOARD.value, resolved)
        self.assertEqual(len(resolved), 2)

        # Flush all
        all_resolved = MultiTierCacheManager.resolve_namespaces_to_flush([], flush_all=True)
        self.assertEqual(len(all_resolved), len(CacheNamespace))

    # --------------------------------------------------------------------------
    # 4. Deployment Orchestration & Rollback Simulator Tests
    # --------------------------------------------------------------------------
    def test_deployment_orchestration_success(self) -> None:
        """Verifies clean rollout execution under normal conditions."""
        spec = DeploymentSpec(
            service_name="keep-backend-api",
            version="3.6.1",
            strategy=DeploymentStrategy.BLUE_GREEN,
            environment="production",
        )
        record = DeploymentOrchestrator.execute_deployment(spec, current_version="3.6.0")
        self.assertEqual(record.status, DeploymentStatus.SUCCESS)
        self.assertEqual(record.version, "3.6.1")
        self.assertEqual(record.rollback_version, "3.6.0")
        self.assertIn("dep-", record.deployment_id)

    def test_deployment_orchestration_auto_rollback(self) -> None:
        """Verifies automated rollback is triggered when verification exceeds error threshold."""
        spec = DeploymentSpec(
            service_name="keep-backend-api",
            version="3.6.2-broken",
            strategy=DeploymentStrategy.CANARY,
            auto_rollback_on_failure=True,
        )
        record = DeploymentOrchestrator.execute_deployment(
            spec,
            current_version="3.6.1",
            simulated_error_rate=2.5,
        )
        self.assertEqual(record.status, DeploymentStatus.ROLLED_BACK)
        self.assertEqual(record.rollback_version, "3.6.1")
        self.assertIn("Automated rollback triggered", record.details["action"])

    def test_deployment_orchestration_manual_failure_handling(self) -> None:
        """Verifies deployment status is FAILED when auto-rollback is disabled."""
        spec = DeploymentSpec(
            service_name="keep-ai-worker",
            version="3.6.2-faulty",
            auto_rollback_on_failure=False,
        )
        record = DeploymentOrchestrator.execute_deployment(
            spec,
            current_version="3.6.1",
            simulated_failure=True,
        )
        self.assertEqual(record.status, DeploymentStatus.FAILED)
        self.assertIsNone(record.rollback_version)

    # --------------------------------------------------------------------------
    # 5. RBAC Integration for System Permissions
    # --------------------------------------------------------------------------
    def test_system_permissions_rbac_hierarchy(self) -> None:
        """Verifies that Phase 3.6 system permissions are mapped into organizational roles."""
        self.assertIn(AIPermission.SYSTEM_VIEW.value, ROLE_PERMISSIONS["Viewer"])
        self.assertIn(AIPermission.SYSTEM_VIEW.value, ROLE_PERMISSIONS["Member"])
        self.assertIn(AIPermission.SYSTEM_BACKUP.value, PROJECT_MANAGER_PERMISSIONS)
        self.assertIn(AIPermission.SYSTEM_MANAGE.value, ORG_ADMIN_PERMISSIONS)
        self.assertIn(AIPermission.SYSTEM_DEPLOY.value, ORG_ADMIN_PERMISSIONS)


if __name__ == "__main__":
    unittest.main()
