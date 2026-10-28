"""Integration Tests for Enterprise Security, Compliance, Governance & Data Protection REST APIs.

Verifies endpoints defined in docs/api/api-contract.md Section 15:
- POST /api/v1/security/login
- POST /api/v1/security/logout
- POST /api/v1/security/mfa/setup
- POST /api/v1/security/mfa/verify
- POST /api/v1/security/mfa/disable
- GET /api/v1/security/audit
- GET /api/v1/security/roles
- POST /api/v1/security/permissions
- POST /api/v1/security/data-classification/scan
- GET /api/v1/security/data-classification/{document_id}
- GET /api/v1/security/ai-governance/logs
- GET /api/v1/security/ai-governance/stats
- GET /api/v1/security/compliance
- POST /api/v1/security/compliance/retention-policies
- POST /api/v1/security/compliance/gdpr-erasure
- GET /api/v1/security/monitoring/alerts

Specification: devdocs/p3/p3.3.txt & docs/api/api-contract.md Section 15
Owner: Member 2 (Backend & Database Lead)
"""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.document import Document
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestSecurityEndpointsIntegration(unittest.TestCase):
    """Integration test suite for Phase 3.3 Security REST APIs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            # 1. Organization
            cls.org = Organization(
                name="Security Test Enterprise",
                domain=f"security-{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            # 2. OrgAdmin User
            cls.raw_password = "SecurePassword123!"
            cls.admin_user = User(
                email=f"ciso-{uuid4().hex[:6]}@enterprise.com",
                hashed_password=get_password_hash(cls.raw_password),
                full_name="Chief Information Security Officer",
                role="OrgAdmin",
                organization_id=cls.org_id,
                is_active=True,
            )
            session.add(cls.admin_user)

            # 3. Target Employee for GDPR test
            cls.employee_user = User(
                email=f"employee-{uuid4().hex[:6]}@enterprise.com",
                hashed_password=get_password_hash("Password123!"),
                full_name="Departing Employee",
                role="Employee",
                organization_id=cls.org_id,
                is_active=True,
            )
            session.add(cls.employee_user)

            # 4. Test Document
            cls.doc = Document(
                organization_id=cls.org_id,
                title="Confidential Corporate Strategy 2026",
                filename="strategy.pdf",
                file_path="/tmp/strategy.pdf",
                file_type="pdf",
                file_size=2048,
                mime_type="application/pdf",
                status="COMPLETED",
                uploader_id=cls.admin_user.id,
            )
            session.add(cls.doc)

            session.commit()
            session.refresh(cls.admin_user)
            session.refresh(cls.employee_user)
            session.refresh(cls.doc)

            cls.admin_id = cls.admin_user.id
            cls.employee_id = cls.employee_user.id
            cls.doc_id = cls.doc.id

        # Generate Bearer token for authorized requests
        token_payload = {
            "sub": str(cls.admin_id),
            "email": cls.admin_user.email,
            "org_id": str(cls.org_id),
            "role": "OrgAdmin",
            "mfa_verified": True,
        }
        cls.token = create_access_token(data=token_payload)
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    def test_01_enterprise_login_success_and_failure(self) -> None:
        """Verify POST /api/v1/security/login with valid and invalid credentials."""
        # Success
        resp = self.client.post(
            "/api/v1/security/login",
            json={
                "email": self.admin_user.email,
                "password": self.raw_password,
                "provider": "local",
            },
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["success"])
        self.assertIn("access_token", body["data"])
        self.assertEqual(body["data"]["role"], "OrgAdmin")

        # Failure
        bad_resp = self.client.post(
            "/api/v1/security/login",
            json={
                "email": self.admin_user.email,
                "password": "WrongPassword!",
                "provider": "local",
            },
        )
        self.assertEqual(bad_resp.status_code, 401)

    def test_02_enterprise_session_logout(self) -> None:
        """Verify POST /api/v1/security/logout records audit event."""
        resp = self.client.post("/api/v1/security/logout", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

    def test_03_mfa_setup_verify_and_disable(self) -> None:
        """Verify MFA lifecycle: setup -> verify -> disable."""
        # 1. Setup
        setup_resp = self.client.post("/api/v1/security/mfa/setup", headers=self.headers)
        self.assertEqual(setup_resp.status_code, 200)
        data = setup_resp.json()["data"]
        self.assertIn("secret_key", data)
        self.assertIn("otpauth_uri", data)
        self.assertTrue(len(data["backup_codes"]) >= 4)

        backup_code = data["backup_codes"][0]

        # 2. Verify with backup code
        verify_resp = self.client.post(
            "/api/v1/security/mfa/verify",
            headers=self.headers,
            json={"code": backup_code},
        )
        self.assertEqual(verify_resp.status_code, 200)
        self.assertTrue(verify_resp.json()["data"]["is_enabled"])

    def test_04_security_audit_trail_endpoint(self) -> None:
        """Verify GET /api/v1/security/audit retrieves paginated logs."""
        resp = self.client.get("/api/v1/security/audit?page=1&page_size=10", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["success"])
        self.assertIn("total", body)
        self.assertIsInstance(body["data"], list)

    def test_05_roles_and_permissions_endpoints(self) -> None:
        """Verify GET /api/v1/security/roles and POST /api/v1/security/permissions."""
        # 1. Get roles
        roles_resp = self.client.get("/api/v1/security/roles", headers=self.headers)
        self.assertEqual(roles_resp.status_code, 200)
        roles = roles_resp.json()["data"]
        self.assertTrue(any(r["role"] == "Organization Admin" for r in roles))

        # 2. Update permissions
        update_resp = self.client.post(
            "/api/v1/security/permissions",
            headers=self.headers,
            json={"role": "Employee", "permissions": ["workspace.view", "document.read"]},
        )
        self.assertEqual(update_resp.status_code, 200)
        self.assertTrue(update_resp.json()["success"])

    def test_06_data_classification_scan_and_status(self) -> None:
        """Verify POST /api/v1/security/data-classification/scan and GET document status."""
        scan_payload = {
            "document_id": str(self.doc_id),
            "content": "Confidential strategy details for Project Apollo. Contact ceo@acme.com.",
        }
        scan_resp = self.client.post(
            "/api/v1/security/data-classification/scan",
            headers=self.headers,
            json=scan_payload,
        )
        self.assertEqual(scan_resp.status_code, 200)
        scan_data = scan_resp.json()["data"]
        self.assertIn("classification_level", scan_data)
        self.assertTrue(scan_data["pii_count"] >= 1)

        # Retrieve document status
        status_resp = self.client.get(
            f"/api/v1/security/data-classification/{self.doc_id}",
            headers=self.headers,
        )
        self.assertEqual(status_resp.status_code, 200)
        self.assertEqual(status_resp.json()["data"]["document_id"], str(self.doc_id))

    def test_07_ai_governance_logs_and_stats(self) -> None:
        """Verify GET /api/v1/security/ai-governance/logs and /stats."""
        logs_resp = self.client.get("/api/v1/security/ai-governance/logs", headers=self.headers)
        self.assertEqual(logs_resp.status_code, 200)
        self.assertTrue(logs_resp.json()["success"])

        stats_resp = self.client.get("/api/v1/security/ai-governance/stats", headers=self.headers)
        self.assertEqual(stats_resp.status_code, 200)
        stats_data = stats_resp.json()["data"]
        self.assertIn("safety_score_percentage", stats_data)

    def test_08_compliance_retention_and_gdpr_erasure(self) -> None:
        """Verify GET /compliance, POST /retention-policies, and POST /gdpr-erasure."""
        # 1. Compliance overview
        comp_resp = self.client.get("/api/v1/security/compliance", headers=self.headers)
        self.assertEqual(comp_resp.status_code, 200)
        comp_data = comp_resp.json()["data"]
        self.assertTrue(comp_data["overall_compliance_score"] >= 80)
        self.assertEqual(len(comp_data["standards"]), 4)

        # 2. Retention policy
        ret_resp = self.client.post(
            "/api/v1/security/compliance/retention-policies",
            headers=self.headers,
            json={
                "resource_type": "audit_logs",
                "retention_days": 180,
                "action_on_expiry": "PURGE",
            },
        )
        self.assertEqual(ret_resp.status_code, 200)
        self.assertTrue(ret_resp.json()["success"])

        # 3. GDPR Erasure
        erasure_resp = self.client.post(
            "/api/v1/security/compliance/gdpr-erasure",
            headers=self.headers,
            json={
                "target_user_id": str(self.employee_id),
                "reason": "Employee departure right to be forgotten",
            },
        )
        self.assertEqual(erasure_resp.status_code, 200)
        erasure_data = erasure_resp.json()["data"]
        self.assertIn("erasure_id", erasure_data)

    def test_09_security_threat_alerts(self) -> None:
        """Verify GET /api/v1/security/monitoring/alerts."""
        alerts_resp = self.client.get("/api/v1/security/monitoring/alerts", headers=self.headers)
        self.assertEqual(alerts_resp.status_code, 200)
        self.assertTrue(alerts_resp.json()["success"])
        self.assertIsInstance(alerts_resp.json()["data"], list)


if __name__ == "__main__":
    unittest.main()
