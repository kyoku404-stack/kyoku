"""Integration Test Pipeline: Phase 3.7 Production Release & Security Audit E2E Pipeline.

Phase: 3.7
Owner: Member 4 (Integration & DevOps Lead)
Domain: tests/integration/test_production_release_pipeline.py
Specification: devdocs/p3/p3.7.txt & docs/Architecture/final-quality-assurance-security-audit-production-release.md
"""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.services.release.contracts import (
    CheckStatus,
    PreflightCheckCategory,
    PreflightCheckResult,
    SystemReadinessReport,
)
from tests.conftest import sync_test_engine


class TestProductionReleasePipelineIntegration(unittest.TestCase):
    """End-to-end integration test pipeline for Phase 3.7 production release gate."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            cls.org = Organization(
                name="Pipeline Test Enterprise",
                domain=f"pipeline-{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            # Admin User (OrgAdmin role has release.view and release.deploy)
            cls.admin_user = User(
                email=f"admin-{uuid4().hex[:6]}@pipeline.com",
                hashed_password=get_password_hash("Password123!"),
                full_name="Release Admin",
                role="OrgAdmin",
                organization_id=cls.org_id,
                is_active=True,
            )
            session.add(cls.admin_user)

            # Member User (Member role lacks release.deploy)
            cls.member_user = User(
                email=f"member-{uuid4().hex[:6]}@pipeline.com",
                hashed_password=get_password_hash("Password123!"),
                full_name="Standard Member",
                role="Member",
                organization_id=cls.org_id,
                is_active=True,
            )
            session.add(cls.member_user)
            session.commit()
            session.refresh(cls.admin_user)
            session.refresh(cls.member_user)

            cls.admin_id = cls.admin_user.id
            cls.member_id = cls.member_user.id

        admin_payload = {
            "sub": str(cls.admin_id),
            "email": cls.admin_user.email,
            "org_id": str(cls.org_id),
            "role": "OrgAdmin",
            "mfa_verified": True,
        }
        cls.admin_token = create_access_token(data=admin_payload)
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}

        member_payload = {
            "sub": str(cls.member_id),
            "email": cls.member_user.email,
            "org_id": str(cls.org_id),
            "role": "Member",
            "mfa_verified": True,
        }
        cls.member_token = create_access_token(data=member_payload)
        cls.member_headers = {"Authorization": f"Bearer {cls.member_token}"}

    def test_01_preflight_system_readiness_probe(self) -> None:
        """Step 1: Executes pre-flight readiness evaluation across all 7 core subsystems."""
        res = self.client.get("/api/v1/system/readiness?target_version=1.0.0", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        data = body["data"]

        self.assertTrue(data["is_ready"])
        self.assertGreaterEqual(data["overall_score"], 0.90)
        self.assertEqual(data["target_version"], "1.0.0")
        self.assertEqual(len(data["failing_checks"]), 0)

        # Verify all 7 required subsystem checkpoints are evaluated
        checks = {chk["check_name"]: chk for chk in data["checks"]}
        required_checks = [
            "database_migrations",
            "database_pool",
            "redis_cache",
            "storage_headroom",
            "vector_database",
            "ai_model_cache",
            "security_audit",
        ]
        for req in required_checks:
            self.assertIn(req, checks)
            self.assertIn(checks[req]["status"], ["PASSED", "WARNING"])
            self.assertGreater(checks[req]["score"], 0.0)

    def test_02_owasp_security_audit_evaluation(self) -> None:
        """Step 2: Executes automated OWASP Top 10 and LLM Top 10 security audit."""
        res = self.client.get("/api/v1/system/security/audit", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        data = body["data"]

        self.assertEqual(data["compliance_standard"], "OWASP_TOP_10_AND_LLM_TOP_10")
        self.assertEqual(data["overall_compliance_percent"], 100.0)
        self.assertEqual(data["total_controls"], 10)
        self.assertEqual(data["passed_controls"], 10)
        self.assertEqual(data["failed_controls"], 0)
        self.assertEqual(len(data["findings"]), 0)

        # Verify critical control IDs exist
        control_ids = [c["control_id"] for c in data["controls"]]
        self.assertIn("SEC-01", control_ids)  # SQL Injection Defense
        self.assertIn("SEC-02", control_ids)  # XSS
        self.assertIn("SEC-04", control_ids)  # Broken Access Control
        self.assertIn("SEC-06", control_ids)  # AI Prompt Injection
        self.assertIn("SEC-10", control_ids)  # Plugin Sandbox

    def test_03_production_release_packaging_and_dispatch(self) -> None:
        """Step 3: Dispatches production release v1.0.0 with SHA-256 artifact manifest generation."""
        payload = {
            "version": "1.0.0",
            "release_tag": "v1.0.0",
            "changelog": "KEEP Enterprise Platform v1.0.0 Production Release. Verified through end-to-end QA.",
            "environment": "production",
            "enforce_preflight": True,
        }
        res = self.client.post("/api/v1/system/release", json=payload, headers=self.admin_headers)
        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertTrue(body["success"])
        data = body["data"]

        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(data["release_tag"], "v1.0.0")
        self.assertEqual(data["status"], "COMPLETED")
        self.assertGreaterEqual(data["preflight_score"], 0.90)
        self.assertIsNotNone(data["release_id"])
        self.assertIsNotNone(data["completed_at"])

        # Check artifact manifest and SHA-256 checksums
        artifacts = data["artifacts"]
        self.assertIn("manifest_checksum_sha256", artifacts)
        self.assertEqual(len(artifacts["artifacts"]), 2)
        artifact_names = [a["name"] for a in artifacts["artifacts"]]
        self.assertIn("kyoku-backend", artifact_names)
        self.assertIn("kyoku-frontend", artifact_names)

    def test_04_release_catalog_retrieval(self) -> None:
        """Step 4: Retrieves historical releases catalog ordered chronologically."""
        res = self.client.get("/api/v1/system/releases?limit=10", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        data = body["data"]

        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        latest = data[0]
        self.assertEqual(latest["version"], "1.0.0")
        self.assertEqual(latest["release_tag"], "v1.0.0")
        self.assertEqual(latest["status"], "COMPLETED")

    def test_05_preflight_enforcement_veto(self) -> None:
        """Step 5: Verifies release deployment is rejected with HTTP 412 when pre-flight checks fail."""
        failing_report = SystemReadinessReport(
            is_ready=False,
            overall_score=0.40,
            evaluated_at=None,  # type: ignore[arg-type]
            target_version="1.0.1",
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

        with patch("backend.app.api.v1.release.release_service.get_deployment_readiness", AsyncMock(return_value=failing_report)):
            payload = {
                "version": "1.0.1",
                "release_tag": "v1.0.1",
                "changelog": "Attempting release with failing gates",
                "environment": "production",
                "enforce_preflight": True,
            }
            res = self.client.post("/api/v1/system/release", json=payload, headers=self.admin_headers)
            self.assertEqual(res.status_code, 412)
            error_data = res.json().get("error", {})
            self.assertIn("Pre-flight readiness checks failed", error_data.get("message", ""))

    def test_06_rbac_enforcement(self) -> None:
        """Step 6: Verifies unauthorized users lacking release.deploy cannot dispatch releases."""
        payload = {
            "version": "1.0.2",
            "release_tag": "v1.0.2",
            "changelog": "Unauthorized member release attempt",
            "environment": "production",
            "enforce_preflight": True,
        }
        res = self.client.post("/api/v1/system/release", json=payload, headers=self.member_headers)
        self.assertEqual(res.status_code, 403)


if __name__ == "__main__":
    unittest.main()
