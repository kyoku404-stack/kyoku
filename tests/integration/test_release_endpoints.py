"""Integration Test Suite: Production Release & Security Audit REST APIs.

Phase: 3.7
Owner: Member 2 (Backend & Database Lead)
Domain: tests/integration/test_release_endpoints.py
Specification: devdocs/p3/p3.7.txt & docs/api/api-contract.md (Section 19)
"""

from __future__ import annotations

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestReleaseEndpointsIntegration(unittest.TestCase):
    """Integration test suite for Phase 3.7 Production Release & Security Audit REST APIs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            cls.org = Organization(
                name="Release Test Enterprise",
                domain=f"release-{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            # Admin user with OrgAdmin role (includes release.view and release.deploy)
            cls.admin_user = User(
                email=f"admin-{uuid4().hex[:6]}@release.com",
                hashed_password=get_password_hash("Password123!"),
                full_name="Release Admin",
                role="OrgAdmin",
                organization_id=cls.org_id,
                is_active=True,
            )
            session.add(cls.admin_user)

            # Member user with Member role (lacks release.deploy)
            cls.regular_user = User(
                email=f"member-{uuid4().hex[:6]}@release.com",
                hashed_password=get_password_hash("Password123!"),
                full_name="Regular Member",
                role="Member",
                organization_id=cls.org_id,
                is_active=True,
            )
            session.add(cls.regular_user)
            session.commit()
            session.refresh(cls.admin_user)
            session.refresh(cls.regular_user)

            cls.admin_id = cls.admin_user.id
            cls.regular_id = cls.regular_user.id

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
            "sub": str(cls.regular_id),
            "email": cls.regular_user.email,
            "org_id": str(cls.org_id),
            "role": "Member",
            "mfa_verified": True,
        }
        cls.member_token = create_access_token(data=member_payload)
        cls.member_headers = {"Authorization": f"Bearer {cls.member_token}"}

    def test_01_get_system_readiness(self) -> None:
        """Verifies GET /api/v1/system/readiness computes system readiness score and subsystem checks."""
        res = self.client.get("/api/v1/system/readiness", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertIn("is_ready", data)
        self.assertTrue(data["is_ready"])
        self.assertGreaterEqual(data["overall_score"], 0.90)
        self.assertIn("checks", data)
        self.assertEqual(len(data["checks"]), 7)

        check_names = [chk["check_name"] for chk in data["checks"]]
        self.assertIn("database_migrations", check_names)
        self.assertIn("vector_database", check_names)
        self.assertIn("security_audit", check_names)

    def test_02_post_production_release_success(self) -> None:
        """Verifies POST /api/v1/system/release executes deployment and packages artifacts."""
        payload = {
            "version": "1.0.0",
            "release_tag": "v1.0.0",
            "changelog": "Phase 3.7 final production release with end-to-end quality assurance.",
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
        self.assertIn("artifacts", data)
        self.assertIn("manifest_checksum_sha256", data["artifacts"])

    def test_03_post_production_release_permission_denied_for_member(self) -> None:
        """Verifies POST /api/v1/system/release denies access to members without release.deploy."""
        payload = {
            "version": "1.0.1",
            "release_tag": "v1.0.1",
            "changelog": "Unauthorized attempt",
            "environment": "production",
            "enforce_preflight": True,
        }
        res = self.client.post("/api/v1/system/release", json=payload, headers=self.member_headers)
        self.assertEqual(res.status_code, 403)

    def test_04_get_release_history(self) -> None:
        """Verifies GET /api/v1/system/releases returns list of historical releases."""
        res = self.client.get("/api/v1/system/releases?limit=10", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        latest = data[0]
        self.assertEqual(latest["version"], "1.0.0")
        self.assertEqual(latest["status"], "COMPLETED")

    def test_05_get_security_audit(self) -> None:
        """Verifies GET /api/v1/system/security/audit returns OWASP Top 10 compliance report."""
        res = self.client.get("/api/v1/system/security/audit", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertEqual(data["compliance_standard"], "OWASP_TOP_10_AND_LLM_TOP_10")
        self.assertEqual(data["total_controls"], 10)
        self.assertEqual(data["passed_controls"], 10)
        self.assertEqual(data["failed_controls"], 0)
        self.assertEqual(data["overall_compliance_percent"], 100.0)
        self.assertEqual(len(data["controls"]), 10)
        self.assertEqual(len(data["findings"]), 0)


if __name__ == "__main__":
    unittest.main()
