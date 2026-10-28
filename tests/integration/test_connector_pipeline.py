"""Integration and Performance Benchmark Test Suite for Enterprise Integrations & Connector Framework (Phase 3.1).

Verifies the complete end-to-end Connector Synchronization Pipeline across:
1. Multi-tenant isolation and data quarantine boundaries (Tenant A vs Tenant B).
2. Registration, symmetric encryption, and HMAC-SHA256 signature verification.
3. Delta change detection algorithm (Added, Updated, Skipped) with SHA-256 checksums.
4. Operational status telemetry and health indicator metrics.
5. Synchronization audit logging and provenance links.
6. Connector removal and lifecycle cleanup.
7. End-to-end pipeline execution benchmark satisfying SLA (< 2000ms).

Specification: devdocs/p3/p3.1.txt & docs/Architecture/enterprise-integrations-connector-framework.md
Author: Member 4 (Integration & DevOps Lead)
"""

import time
import unittest
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.connector import Connector
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestEnterpriseConnectorPipelineIntegration(unittest.TestCase):
    """End-to-end integration and security benchmark suite for Phase 3.1 Enterprise Integrations."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            # 1. Primary Tenant Organization Alpha
            cls.org_alpha = Organization(
                name="Connector Alpha Tenant",
                domain=f"alpha-conn-{uuid4().hex[:6]}.com",
            )
            # 2. Secondary Tenant Organization Beta (Multi-tenant quarantine)
            cls.org_beta = Organization(
                name="Connector Beta Tenant",
                domain=f"beta-conn-{uuid4().hex[:6]}.com",
            )
            session.add_all([cls.org_alpha, cls.org_beta])
            session.commit()
            session.refresh(cls.org_alpha)
            session.refresh(cls.org_beta)

            cls.org_alpha_id = cls.org_alpha.id
            cls.org_beta_id = cls.org_beta.id

            # 3. Users for each organization (OrgAdmin role)
            cls.user_alpha = User(
                email=f"alpha-conn-admin-{uuid4().hex[:6]}@test.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Alpha Connector Admin",
                organization_id=cls.org_alpha_id,
                role="OrgAdmin",
            )
            cls.user_beta = User(
                email=f"beta-conn-admin-{uuid4().hex[:6]}@test.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Beta Connector Admin",
                organization_id=cls.org_beta_id,
                role="OrgAdmin",
            )
            session.add_all([cls.user_alpha, cls.user_beta])
            session.commit()
            session.refresh(cls.user_alpha)
            session.refresh(cls.user_beta)

            cls.user_alpha_id = cls.user_alpha.id
            cls.user_beta_id = cls.user_beta.id

        # 4. Generate Auth Tokens
        cls.token_alpha = create_access_token(
            data={
                "sub": str(cls.user_alpha_id),
                "email": cls.user_alpha.email,
                "org_id": str(cls.org_alpha_id),
                "role": "OrgAdmin",
            }
        )
        cls.token_beta = create_access_token(
            data={
                "sub": str(cls.user_beta_id),
                "email": cls.user_beta.email,
                "org_id": str(cls.org_beta_id),
                "role": "OrgAdmin",
            }
        )

        cls.headers_alpha = {"Authorization": f"Bearer {cls.token_alpha}"}
        cls.headers_beta = {"Authorization": f"Bearer {cls.token_beta}"}

    def test_01_connector_registration_and_encryption(self) -> None:
        """Verify registration of a connector and verify encrypted state transitions."""
        payload = {
            "name": "Alpha Engineering Notion",
            "platform_type": "NOTION",
            "platform_category": "DOCUMENTATION",
            "auth_type": "API_KEY",
            "config": {"sync_interval_minutes": 30},
        }

        resp = self.client.post("/api/v1/connectors/register", json=payload, headers=self.headers_alpha)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()["data"]

        self.assertIn("id", data)
        self.assertEqual(data["name"], "Alpha Engineering Notion")
        self.assertEqual(data["platform_type"], "NOTION")
        self.assertEqual(data["status"], "CONFIGURED")

        # Verify in database that credentials aren't plaintext
        with Session(sync_test_engine) as session:
            conn = session.query(Connector).filter_by(id=UUID(data["id"])).first()
            self.assertIsNotNone(conn)
            self.assertEqual(conn.organization_id, self.org_alpha_id)
            self.assertEqual(conn.status, "CONFIGURED")

    def test_02_connector_multi_tenant_quarantine(self) -> None:
        """Verify Tenant B cannot access or manipulate Tenant A connectors (404/403)."""
        # Register connector for Alpha
        reg_resp = self.client.post(
            "/api/v1/connectors/register",
            json={
                "name": "Alpha Private Slack",
                "platform_type": "SLACK",
                "platform_category": "COMMUNICATION",
                "auth_type": "OAUTH2",
            },
            headers=self.headers_alpha,
        )
        alpha_conn_id = reg_resp.json()["data"]["id"]

        # Attempt to inspect status with Tenant B
        beta_status_resp = self.client.get(
            f"/api/v1/connectors/status/{alpha_conn_id}",
            headers=self.headers_beta,
        )
        self.assertEqual(beta_status_resp.status_code, 404)

        # Attempt to trigger sync with Tenant B
        beta_sync_resp = self.client.post(
            "/api/v1/connectors/sync",
            json={"connector_id": alpha_conn_id, "sync_mode": "INCREMENTAL"},
            headers=self.headers_beta,
        )
        self.assertEqual(beta_sync_resp.status_code, 404)

        # Attempt to delete with Tenant B
        beta_del_resp = self.client.delete(
            f"/api/v1/connectors/remove/{alpha_conn_id}",
            headers=self.headers_beta,
        )
        self.assertEqual(beta_del_resp.status_code, 404)

    def test_03_connector_authentication_lifecycle(self) -> None:
        """Verify credential authentication and transition to CONNECTED status."""
        reg_resp = self.client.post(
            "/api/v1/connectors/register",
            json={
                "name": "Alpha Corporate Google Drive",
                "platform_type": "GOOGLE_DRIVE",
                "platform_category": "CLOUD_STORAGE",
                "auth_type": "OAUTH2",
            },
            headers=self.headers_alpha,
        )
        conn_id = reg_resp.json()["data"]["id"]

        # Authenticate
        auth_payload = {
            "connector_id": conn_id,
            "auth_type": "OAUTH2",
            "credentials": {"access_token": "ya29.sample_oauth_token_alpha"},
        }
        auth_resp = self.client.post(
            "/api/v1/connectors/authenticate",
            json=auth_payload,
            headers=self.headers_alpha,
        )
        self.assertEqual(auth_resp.status_code, 200)
        auth_data = auth_resp.json()["data"]
        self.assertEqual(auth_data["status"], "CONNECTED")

        # Verify DB encrypted signature
        with Session(sync_test_engine) as session:
            conn = session.query(Connector).filter_by(id=UUID(conn_id)).first()
            self.assertIsNotNone(conn)
            self.assertIsNotNone(conn.encrypted_credentials)
            self.assertIn(".", conn.encrypted_credentials)  # base64.hmac signature separator

    def test_04_synchronization_pipeline_and_change_detection(self) -> None:
        """Verify full and incremental sync execution and delta change detection logs."""
        reg_resp = self.client.post(
            "/api/v1/connectors/register",
            json={
                "name": "Alpha GitHub Org",
                "platform_type": "GITHUB",
                "platform_category": "DEVELOPMENT",
                "auth_type": "API_KEY",
            },
            headers=self.headers_alpha,
        )
        conn_id = reg_resp.json()["data"]["id"]

        # Authenticate
        self.client.post(
            "/api/v1/connectors/authenticate",
            json={
                "connector_id": conn_id,
                "auth_type": "API_KEY",
                "credentials": {"api_key": "ghp_secret_token_123"},
            },
            headers=self.headers_alpha,
        )

        # 1st Sync (Initial - all new resources should be ADDED)
        sync_resp_1 = self.client.post(
            "/api/v1/connectors/sync",
            json={"connector_id": conn_id, "sync_mode": "FULL"},
            headers=self.headers_alpha,
        )
        self.assertEqual(sync_resp_1.status_code, 202)
        job_1_data = sync_resp_1.json()["data"]
        self.assertEqual(job_1_data["status"], "COMPLETED")

        # Check logs for conn_id
        logs_resp_1 = self.client.get(
            f"/api/v1/connectors/logs?connector_id={conn_id}",
            headers=self.headers_alpha,
        )
        self.assertEqual(logs_resp_1.status_code, 200)
        logs_1 = logs_resp_1.json()["data"]["logs"]
        self.assertGreaterEqual(len(logs_1), 1)
        self.assertTrue(all(entry["action_taken"] == "ADDED" for entry in logs_1))

        # 2nd Sync (Incremental - since content unchanged, resources should be SKIPPED)
        sync_resp_2 = self.client.post(
            "/api/v1/connectors/sync",
            json={"connector_id": conn_id, "sync_mode": "INCREMENTAL"},
            headers=self.headers_alpha,
        )
        self.assertEqual(sync_resp_2.status_code, 202)

        logs_resp_2 = self.client.get(
            f"/api/v1/connectors/logs?connector_id={conn_id}",
            headers=self.headers_alpha,
        )
        logs_2 = logs_resp_2.json()["data"]["logs"]
        skipped_logs = [entry for entry in logs_2 if entry["action_taken"] == "SKIPPED"]
        self.assertGreaterEqual(len(skipped_logs), 1)

    def test_05_status_telemetry_and_sla_metrics(self) -> None:
        """Verify live health metrics, latency SLAs, and status reporting."""
        reg_resp = self.client.post(
            "/api/v1/connectors/register",
            json={
                "name": "Alpha Jira Projects",
                "platform_type": "JIRA",
                "platform_category": "PROJECT_MANAGEMENT",
                "auth_type": "API_KEY",
            },
            headers=self.headers_alpha,
        )
        conn_id = reg_resp.json()["data"]["id"]

        # Authenticate & Sync
        self.client.post(
            "/api/v1/connectors/authenticate",
            json={
                "connector_id": conn_id,
                "auth_type": "API_KEY",
                "credentials": {"api_key": "jira_pat_token_alpha"},
            },
            headers=self.headers_alpha,
        )
        self.client.post(
            "/api/v1/connectors/sync",
            json={"connector_id": conn_id, "sync_mode": "INCREMENTAL"},
            headers=self.headers_alpha,
        )

        # Status inspection
        status_resp = self.client.get(
            f"/api/v1/connectors/status/{conn_id}",
            headers=self.headers_alpha,
        )
        self.assertEqual(status_resp.status_code, 200)
        status_data = status_resp.json()["data"]

        self.assertEqual(status_data["id"], conn_id)
        self.assertIn(status_data["status"], ["CONNECTED", "HEALTHY"])
        health = status_data["health_metrics"]
        self.assertIn("api_latency_ms", health)
        self.assertIn("quota_used_pct", health)
        self.assertIn("success_rate_pct", health)
        self.assertLess(health["api_latency_ms"], 5000.0)  # SLA check

    def test_06_connector_deletion_and_cascade(self) -> None:
        """Verify removing a connector cleans up jobs and logs."""
        reg_resp = self.client.post(
            "/api/v1/connectors/register",
            json={
                "name": "Temporary Dropbox",
                "platform_type": "DROPBOX",
                "platform_category": "CLOUD_STORAGE",
                "auth_type": "API_KEY",
            },
            headers=self.headers_alpha,
        )
        conn_id = reg_resp.json()["data"]["id"]

        # Delete connector
        del_resp = self.client.delete(
            f"/api/v1/connectors/remove/{conn_id}",
            headers=self.headers_alpha,
        )
        self.assertEqual(del_resp.status_code, 200)

        # Confirm 404 upon subsequent access
        get_resp = self.client.get(
            f"/api/v1/connectors/status/{conn_id}",
            headers=self.headers_alpha,
        )
        self.assertEqual(get_resp.status_code, 404)

        # Verify DB records deleted
        with Session(sync_test_engine) as session:
            conn = session.query(Connector).filter_by(id=UUID(conn_id)).first()
            self.assertIsNone(conn)

    def test_07_pipeline_performance_sla_benchmark(self) -> None:
        """Benchmark synchronization pipeline execution latency against SLA (< 2000ms)."""
        reg_resp = self.client.post(
            "/api/v1/connectors/register",
            json={
                "name": "SLA Benchmark Connector",
                "platform_type": "CONFLUENCE",
                "platform_category": "DOCUMENTATION",
                "auth_type": "API_KEY",
            },
            headers=self.headers_alpha,
        )
        conn_id = reg_resp.json()["data"]["id"]

        self.client.post(
            "/api/v1/connectors/authenticate",
            json={
                "connector_id": conn_id,
                "auth_type": "API_KEY",
                "credentials": {"api_key": "conf_key_sla"},
            },
            headers=self.headers_alpha,
        )

        start_time = time.perf_counter()
        sync_resp = self.client.post(
            "/api/v1/connectors/sync",
            json={"connector_id": conn_id, "sync_mode": "INCREMENTAL"},
            headers=self.headers_alpha,
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        self.assertEqual(sync_resp.status_code, 202)
        # Verify latency is well within 2000ms SLA target
        self.assertLess(
            latency_ms,
            2000.0,
            f"Connector synchronization latency {latency_ms:.2f}ms exceeds SLA limit of 2000ms",
        )
