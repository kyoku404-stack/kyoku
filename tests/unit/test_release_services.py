"""Unit Test Suite: Enterprise Release & Security Audit Services.

Phase: 3.7
Owner: Member 2 (Backend & Database Lead)
Domain: tests/unit/test_release_services.py
Specification: devdocs/p3/p3.7.txt & docs/Architecture/final-quality-assurance-security-audit-production-release.md
"""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import HTTPException

from backend.app.models.release import (
    ProductionRelease,
    SecurityAuditRecord,
)
from backend.app.schemas.release import ReleaseDeployRequest
from backend.app.services.release.contracts import (
    CheckStatus,
    PreflightCheckCategory,
    PreflightCheckResult,
    SystemReadinessReport,
)
from backend.app.services.release.service import EnterpriseReleaseService


class TestEnterpriseReleaseServiceUnit(unittest.IsolatedAsyncioTestCase):
    """Unit tests verifying EnterpriseReleaseService orchestrations."""

    def setUp(self) -> None:
        self.service = EnterpriseReleaseService()
        self.mock_db = AsyncMock()
        self.mock_db.add = MagicMock()

    async def test_get_deployment_readiness_all_passing(self) -> None:
        """Verifies pre-flight evaluation produces passing readiness status when all checks pass."""
        report = await self.service.get_deployment_readiness(self.mock_db)

        self.assertIsInstance(report, SystemReadinessReport)
        self.assertTrue(report.is_ready)
        self.assertGreaterEqual(report.overall_score, 0.90)
        self.assertEqual(len(report.checks), 7)
        self.assertEqual(len(report.failing_checks), 0)

        categories = {chk.category for chk in report.checks}
        self.assertIn(PreflightCheckCategory.PERSISTENCE, categories)
        self.assertIn(PreflightCheckCategory.CACHE, categories)
        self.assertIn(PreflightCheckCategory.STORAGE, categories)
        self.assertIn(PreflightCheckCategory.AI_INFRA, categories)
        self.assertIn(PreflightCheckCategory.GOVERNANCE, categories)

    async def test_trigger_production_release_success(self) -> None:
        """Verifies successful production release packaging and persistence."""
        user_id = str(uuid4())
        request = ReleaseDeployRequest(
            version="1.0.0",
            release_tag="v1.0.0",
            changelog="Initial production release for KEEP platform Phase 3.7.",
            environment="production",
            enforce_preflight=True,
        )

        db_release = await self.service.trigger_production_release(
            db=self.mock_db,
            request=request,
            user_id=user_id,
        )

        self.assertIsInstance(db_release, ProductionRelease)
        self.assertEqual(db_release.version, "1.0.0")
        self.assertEqual(db_release.release_tag, "v1.0.0")
        self.assertEqual(db_release.status, "COMPLETED")
        self.assertGreaterEqual(db_release.preflight_score, 0.90)
        self.assertIn("manifest_checksum_sha256", db_release.artifacts_json)
        self.assertEqual(len(db_release.artifacts_json["artifacts"]), 2)

        # Ensure DB transaction was committed
        self.mock_db.commit.assert_awaited()
        self.mock_db.refresh.assert_awaited()

    async def test_trigger_production_release_fails_when_preflight_fails(self) -> None:
        """Verifies release is rejected with HTTP 412 if pre-flight score falls below gate."""
        failing_report = SystemReadinessReport(
            is_ready=False,
            overall_score=0.40,
            evaluated_at=None,  # type: ignore[arg-type]
            target_version="1.0.0",
            git_commit="8767c08",
            checks=[
                PreflightCheckResult(
                    check_name="database_migrations",
                    category=PreflightCheckCategory.PERSISTENCE,
                    status=CheckStatus.FAILED,
                    score=0.0,
                    is_critical=True,
                )
            ],
            failing_checks=["database_migrations"],
        )

        # Patch get_deployment_readiness to return failing report
        self.service.get_deployment_readiness = AsyncMock(return_value=failing_report)  # type: ignore[method-assign]

        request = ReleaseDeployRequest(
            version="1.0.0",
            release_tag="v1.0.0",
            changelog="Attempting release with failing migrations",
            enforce_preflight=True,
        )

        with self.assertRaises(HTTPException) as ctx:
            await self.service.trigger_production_release(
                db=self.mock_db,
                request=request,
                user_id=str(uuid4()),
            )

        self.assertEqual(ctx.exception.status_code, 412)
        self.assertIn("database_migrations", ctx.exception.detail)

    async def test_get_release_history(self) -> None:
        """Verifies querying production release history from database session."""
        mock_release = ProductionRelease(
            release_id="rel-v1.0.0-test",
            version="1.0.0",
            release_tag="v1.0.0",
            git_commit="8767c08",
            changelog="Production release",
            status="COMPLETED",
            preflight_score=1.0,
            artifacts_json={},
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_release]
        self.mock_db.execute.return_value = mock_result

        history = await self.service.get_release_history(self.mock_db, limit=10)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].release_id, "rel-v1.0.0-test")

    async def test_get_security_audit_report(self) -> None:
        """Verifies automated security audit calculation and database record persistence."""
        auditor_id = str(uuid4())
        audit_record = await self.service.get_security_audit_report(
            db=self.mock_db,
            auditor_id=auditor_id,
        )

        self.assertIsInstance(audit_record, SecurityAuditRecord)
        self.assertEqual(audit_record.compliance_standard, "OWASP_TOP_10_AND_LLM_TOP_10")
        self.assertEqual(audit_record.total_controls, 10)
        self.assertEqual(audit_record.passed_controls, 10)
        self.assertEqual(audit_record.failed_controls, 0)
        self.assertEqual(float(audit_record.overall_score), 100.0)
        self.assertEqual(len(audit_record.controls_json), 10)
        self.assertEqual(len(audit_record.findings_json), 0)

        self.mock_db.commit.assert_awaited()
        self.mock_db.refresh.assert_awaited()


if __name__ == "__main__":
    unittest.main()
