"""Unit Test Suite for Phase 3.7 Release & Security Audit Contracts & Algorithms.

Specification Reference: devdocs/p3/p3.7.txt (Chapters 1-20)
Architecture Reference: docs/Architecture/final-quality-assurance-security-audit-production-release.md
Role: Member 1 (Project Lead & AI Architect)
"""

import unittest

from backend.app.services.ai.interfaces import (
    ORG_ADMIN_PERMISSIONS,
    VIEWER_PERMISSIONS,
    AIPermission,
)
from backend.app.services.release.contracts import (
    AuditSeverity,
    CheckStatus,
    PreflightCheckCategory,
    PreflightReadinessEvaluator,
    ReleaseArtifact,
    ReleaseSpec,
    ReleaseStatus,
    ReleaseTaggingManager,
    SecurityAuditEvaluator,
    SecurityComplianceStandard,
)


class TestReleaseContractsUnit(unittest.TestCase):
    """Verifies domain contracts, pre-flight gate algorithms, and security audit evaluators."""

    def setUp(self) -> None:
        self.valid_checks = {
            "database_migrations": {
                "category": PreflightCheckCategory.PERSISTENCE,
                "status": CheckStatus.PASSED,
                "details": {"head": "0a1b2c3d4e5f"},
            },
            "database_pool": {
                "category": PreflightCheckCategory.PERSISTENCE,
                "status": CheckStatus.PASSED,
                "details": {"active": 2, "size": 20},
            },
            "redis_cache": {
                "category": PreflightCheckCategory.CACHE,
                "status": CheckStatus.PASSED,
                "details": {"hit_ratio": 94.2},
            },
            "storage_headroom": {
                "category": PreflightCheckCategory.STORAGE,
                "status": CheckStatus.PASSED,
                "details": {"headroom_pct": 69.3},
            },
            "vector_database": {
                "category": PreflightCheckCategory.AI_INFRA,
                "status": CheckStatus.PASSED,
                "details": {"hnsw_ready": True},
            },
            "ai_model_cache": {
                "category": PreflightCheckCategory.AI_INFRA,
                "status": CheckStatus.PASSED,
                "details": {"model_cached": True},
            },
            "security_audit": {
                "category": PreflightCheckCategory.GOVERNANCE,
                "status": CheckStatus.PASSED,
                "details": {"critical_count": 0},
            },
        }

    # =========================================================================
    # 1. SemVer Validation & Artifact Fingerprinting
    # =========================================================================

    def test_semver_validation_valid_and_invalid(self) -> None:
        """Verifies strict SemVer 2.0.0 format checking."""
        valid_versions = ["1.0.0", "v1.0.0", "1.0.0-rc.1", "2.1.4+build.2026", "0.9.12"]
        for v in valid_versions:
            self.assertTrue(ReleaseTaggingManager.validate_semver(v), f"Failed valid version: {v}")

        invalid_versions = ["1.0", "v1", "release-1.0.0", "1.0.0.0", "latest", ""]
        for v in invalid_versions:
            self.assertFalse(ReleaseTaggingManager.validate_semver(v), f"Accepted invalid version: {v}")

    def test_artifact_manifest_generation_and_hashing(self) -> None:
        """Verifies deterministic SHA-256 fingerprinting across release artifacts."""
        artifacts = [
            ReleaseArtifact("keep-backend", "DOCKER_IMAGE", "sha-backend-001", {"tag": "keep-backend:1.0.0"}),
            ReleaseArtifact("keep-frontend", "DOCKER_IMAGE", "sha-frontend-001", {"tag": "keep-frontend:1.0.0"}),
        ]
        manifest = ReleaseTaggingManager.generate_artifact_manifest("1.0.0", "8767c08", artifacts)

        self.assertEqual(manifest["version"], "1.0.0")
        self.assertEqual(manifest["git_commit"], "8767c08")
        self.assertEqual(len(manifest["artifacts"]), 2)
        self.assertIn("manifest_checksum_sha256", manifest)
        self.assertEqual(len(manifest["manifest_checksum_sha256"]), 64)

    # =========================================================================
    # 2. Pre-Flight Readiness Evaluator
    # =========================================================================

    def test_preflight_evaluation_all_passing(self) -> None:
        """Verifies that 100% passing checks yield is_ready=True and a composite score of 1.0."""
        report = PreflightReadinessEvaluator.evaluate(self.valid_checks, "1.0.0", "8767c08")

        self.assertTrue(report.is_ready)
        self.assertEqual(report.overall_score, 1.0)
        self.assertEqual(len(report.failing_checks), 0)
        self.assertEqual(len(report.checks), 7)
        self.assertEqual(report.target_version, "1.0.0")

    def test_preflight_evaluation_critical_database_veto(self) -> None:
        """Verifies hard veto cap (<= 0.40) and is_ready=False when database_migrations fails."""
        failing_checks = dict(self.valid_checks)
        failing_checks["database_migrations"] = {
            "category": PreflightCheckCategory.PERSISTENCE,
            "status": CheckStatus.FAILED,
            "details": {"error": "Pending migration: 0a1b2c3d4e5f"},
        }
        report = PreflightReadinessEvaluator.evaluate(failing_checks, "1.0.0", "8767c08")

        self.assertFalse(report.is_ready)
        self.assertLessEqual(report.overall_score, 0.40)
        self.assertIn("database_migrations", report.failing_checks)

    def test_preflight_evaluation_critical_vector_db_veto(self) -> None:
        """Verifies hard veto cap (<= 0.40) and is_ready=False when vector_database fails."""
        failing_checks = dict(self.valid_checks)
        failing_checks["vector_database"] = {
            "category": PreflightCheckCategory.AI_INFRA,
            "status": CheckStatus.FAILED,
            "details": {"error": "pgvector index degraded"},
        }
        report = PreflightReadinessEvaluator.evaluate(failing_checks, "1.0.0", "8767c08")

        self.assertFalse(report.is_ready)
        self.assertLessEqual(report.overall_score, 0.40)
        self.assertIn("vector_database", report.failing_checks)

    def test_preflight_evaluation_warning_scores(self) -> None:
        """Verifies that non-critical WARNING checks grant 50% partial credit."""
        warning_checks = dict(self.valid_checks)
        warning_checks["storage_headroom"] = {
            "category": PreflightCheckCategory.STORAGE,
            "status": CheckStatus.WARNING,
            "details": {"headroom_pct": 14.5},
        }
        report = PreflightReadinessEvaluator.evaluate(warning_checks, "1.0.0", "8767c08")

        # Storage weight is 0.10; 50% partial credit loses 0.05
        self.assertEqual(report.overall_score, 0.95)
        self.assertTrue(report.is_ready)
        self.assertEqual(len(report.failing_checks), 0)

    # =========================================================================
    # 3. Security Audit Evaluator
    # =========================================================================

    def test_security_audit_all_controls_passing(self) -> None:
        """Verifies that clean baseline security audit achieves 100% compliance."""
        report = SecurityAuditEvaluator.run_audit()

        self.assertEqual(report.compliance_standard, SecurityComplianceStandard.OWASP_TOP_10_AND_LLM_TOP_10)
        self.assertEqual(report.overall_compliance_percent, 100.0)
        self.assertEqual(report.total_controls, 10)
        self.assertEqual(report.passed_controls, 10)
        self.assertEqual(report.failed_controls, 0)
        self.assertEqual(len(report.findings), 0)

    def test_security_audit_simulated_vulnerability(self) -> None:
        """Verifies that security audit catches and reports simulated control failures."""
        report = SecurityAuditEvaluator.run_audit(simulated_failures=["SEC-01", "SEC-06"])

        self.assertEqual(report.overall_compliance_percent, 80.0)
        self.assertEqual(report.total_controls, 10)
        self.assertEqual(report.passed_controls, 8)
        self.assertEqual(report.failed_controls, 2)
        self.assertEqual(len(report.findings), 2)

        finding_controls = [f.control_id for f in report.findings]
        self.assertIn("SEC-01", finding_controls)
        self.assertIn("SEC-06", finding_controls)
        self.assertEqual(report.findings[0].severity, AuditSeverity.CRITICAL)

    # =========================================================================
    # 4. Release Execution & Gate Enforcement
    # =========================================================================

    def test_execute_release_success(self) -> None:
        """Verifies successful release execution when pre-flight readiness criteria are met."""
        report = PreflightReadinessEvaluator.evaluate(self.valid_checks, "1.0.0", "8767c08")
        spec = ReleaseSpec(
            version="1.0.0",
            release_tag="v1.0.0",
            changelog="KEEP v1.0.0 GA Production Release",
            enforce_preflight=True,
        )
        record = ReleaseTaggingManager.execute_release(spec, "8767c08", report, user_id="admin-001")

        self.assertEqual(record.version, "1.0.0")
        self.assertEqual(record.release_tag, "v1.0.0")
        self.assertEqual(record.status, ReleaseStatus.COMPLETED)
        self.assertEqual(record.preflight_score, 1.0)
        self.assertEqual(record.deployed_by, "admin-001")
        self.assertIn("artifacts", record.artifacts)
        self.assertIn("manifest_checksum_sha256", record.artifacts)

    def test_execute_release_blocked_by_preflight(self) -> None:
        """Verifies that release execution raises PermissionError when pre-flight check fails."""
        failing_checks = dict(self.valid_checks)
        failing_checks["database_migrations"] = {
            "category": PreflightCheckCategory.PERSISTENCE,
            "status": CheckStatus.FAILED,
        }
        report = PreflightReadinessEvaluator.evaluate(failing_checks, "1.0.0", "8767c08")
        spec = ReleaseSpec(
            version="1.0.0",
            release_tag="v1.0.0",
            changelog="KEEP v1.0.0",
            enforce_preflight=True,
        )
        with self.assertRaises(PermissionError):
            ReleaseTaggingManager.execute_release(spec, "8767c08", report)

    def test_execute_release_invalid_semver(self) -> None:
        """Verifies that invalid SemVer version strings raise ValueError."""
        report = PreflightReadinessEvaluator.evaluate(self.valid_checks, "bad_version", "8767c08")
        spec = ReleaseSpec(
            version="bad_version",
            release_tag="v1.0.0",
            changelog="Bad version",
            enforce_preflight=False,
        )
        with self.assertRaises(ValueError):
            ReleaseTaggingManager.execute_release(spec, "8767c08", report)

    # =========================================================================
    # 5. RBAC Permission Hierarchy
    # =========================================================================

    def test_release_rbac_hierarchy(self) -> None:
        """Verifies that RELEASE_VIEW and RELEASE_DEPLOY are correctly assigned to roles."""
        self.assertIn(AIPermission.RELEASE_VIEW.value, VIEWER_PERMISSIONS)
        self.assertIn(AIPermission.RELEASE_VIEW.value, ORG_ADMIN_PERMISSIONS)
        self.assertIn(AIPermission.RELEASE_DEPLOY.value, ORG_ADMIN_PERMISSIONS)
        self.assertNotIn(AIPermission.RELEASE_DEPLOY.value, VIEWER_PERMISSIONS)


if __name__ == "__main__":
    unittest.main()
