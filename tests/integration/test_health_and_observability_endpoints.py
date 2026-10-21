"""Integration Test Suite: Multi-Tier Health Checks, Prometheus Metrics & Observability.

Specification Source: devdocs/p1/p1.9.txt (Chapter 7, 8, 9, 10, 16) & docs/API/api-contract.md Section 6
Phase: 1.9 — Logging, Monitoring & System Observability
Role: Member 2 (Backend & Database Lead)
"""

from __future__ import annotations

import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.constants import UserRole
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestHealthAndObservabilityEndpointsIntegration(unittest.TestCase):
    """Integration test suite validating all 7 observability and health check endpoints."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine) as session:
            cls.org = Organization(
                name=f"Obs Corp {uuid4().hex[:6]}",
                domain=f"obs_{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.flush()

            cls.admin_user = User(
                email=f"admin_{uuid4().hex[:6]}@obs.com",
                hashed_password=get_password_hash("SecretPass123!"),
                full_name="Observability Admin",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org.id,
                is_active=True,
            )
            cls.member_user = User(
                email=f"member_{uuid4().hex[:6]}@obs.com",
                hashed_password=get_password_hash("SecretPass123!"),
                full_name="Standard Member",
                role=UserRole.MEMBER,
                organization_id=cls.org.id,
                is_active=True,
            )
            session.add_all([cls.admin_user, cls.member_user])
            session.commit()

            cls.org_id = cls.org.id
            cls.admin_id = cls.admin_user.id
            cls.member_id = cls.member_user.id

        cls.token_admin = create_access_token(
            data={
                "sub": str(cls.admin_id),
                "email": "admin@obs.com",
                "role": "OrgAdmin",
                "org_id": str(cls.org_id),
            }
        )
        cls.headers_admin = {"Authorization": f"Bearer {cls.token_admin}"}

        cls.token_member = create_access_token(
            data={
                "sub": str(cls.member_id),
                "email": "member@obs.com",
                "role": "Member",
                "org_id": str(cls.org_id),
            }
        )
        cls.headers_member = {"Authorization": f"Bearer {cls.token_member}"}

    def test_composite_health_endpoint_200(self) -> None:
        """GET /health evaluates all subsystem dependencies and returns HTTP 200 composite status."""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn(data["status"], ("healthy", "degraded"))
        self.assertIn("version", data)
        self.assertIn("timestamp", data)
        self.assertGreaterEqual(data["uptime_seconds"], 0.0)
        self.assertIn("environment", data)

        deps = data["dependencies"]
        self.assertIn(deps["database"]["status"], ("healthy", "degraded"))
        self.assertTrue(deps["database"]["vector_extension_enabled"])
        self.assertIn(deps["storage"]["status"], ("healthy", "degraded"))
        self.assertTrue(deps["storage"]["writable"])
        self.assertEqual(deps["api"]["status"], "healthy")
        self.assertEqual(deps["auth"]["status"], "healthy")
        self.assertTrue(deps["auth"]["jwt_secret_configured"])

    def test_database_health_probe_200(self) -> None:
        """GET /health/database isolates database probe with connection pool metrics."""
        res = self.client.get("/health/database")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["status"], "healthy")
        self.assertGreaterEqual(data["latency_ms"], 0.0)
        self.assertIn("database", data)
        self.assertIn("version", data)
        self.assertTrue(data["vector_extension"])
        self.assertIn("pool", data)
        self.assertIn("size", data["pool"])
        self.assertIn("checked_out", data["pool"])

    def test_storage_health_probe_200(self) -> None:
        """GET /health/storage verifies filesystem write permissions, latency, and capacity."""
        res = self.client.get("/health/storage")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn(data["status"], ("healthy", "degraded"))
        self.assertIn("storage_root", data)
        self.assertTrue(data["writable"])
        self.assertGreaterEqual(data["latency_ms"], 0.0)
        self.assertGreater(data["total_bytes"], 0)
        self.assertGreaterEqual(data["used_bytes"], 0)
        self.assertGreater(data["free_bytes"], 0)
        self.assertGreaterEqual(data["used_percent"], 0.0)

    def test_api_health_probe_200(self) -> None:
        """GET /health/api validates API process runtime uptime and memory RSS."""
        res = self.client.get("/health/api")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["status"], "healthy")
        self.assertGreaterEqual(data["uptime_seconds"], 0.0)
        self.assertIn("python_version", data)
        self.assertGreater(data["memory_rss_mb"], 0.0)
        self.assertGreaterEqual(data["cpu_percent"], 0.0)
        self.assertGreaterEqual(data["active_requests"], 0)

    def test_auth_health_probe_200(self) -> None:
        """GET /health/auth inspects JWT secret configuration and token expiration parameters."""
        res = self.client.get("/health/auth")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["jwt_secret_configured"])
        self.assertEqual(data["algorithm"], "HS256")
        self.assertEqual(data["access_token_expire_minutes"], settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.assertEqual(data["refresh_token_expire_days"], 7)


    def test_prometheus_metrics_endpoint_200(self) -> None:
        """GET /metrics serves operational counters and histograms in Prometheus exposition format."""
        # Warm up the metrics with a call
        self.client.get("/health/api")

        res = self.client.get("/metrics")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/plain", res.headers.get("content-type", ""))

        text_body = res.text
        self.assertIn("# HELP http_requests_total", text_body)
        self.assertIn("# TYPE http_requests_total counter", text_body)
        self.assertIn("# HELP http_request_duration_seconds", text_body)
        self.assertIn("# TYPE http_request_duration_seconds histogram", text_body)
        self.assertIn("db_pool_active_connections", text_body)
        self.assertIn("storage_used_bytes", text_body)

    def test_metrics_summary_endpoint_authorized_admin(self) -> None:
        """GET /api/v1/metrics/summary returns aggregated telemetry JSON for OrgAdmin."""
        res = self.client.get("/api/v1/metrics/summary", headers=self.headers_admin)
        self.assertEqual(res.status_code, 200)
        body = res.json()

        self.assertTrue(body["success"])
        data = body["data"]
        self.assertEqual(data["system_status"], "healthy")
        self.assertGreaterEqual(data["uptime_seconds"], 0.0)
        self.assertIn("timestamp", data)

        kpis = data["kpis"]
        self.assertIn("requests_per_second", kpis)
        self.assertIn("p95_latency_ms", kpis)
        self.assertIn("error_rate_percent", kpis)
        self.assertGreaterEqual(kpis["active_users"], 1)
        self.assertGreaterEqual(kpis["total_documents"], 0)
        self.assertGreater(kpis["storage_capacity_bytes"], 0)
        self.assertIn("database_pool_usage_percent", kpis)

        alerts = data["alerts"]
        self.assertIsInstance(alerts, list)
        self.assertTrue(len(alerts) >= 1)
        self.assertEqual(alerts[0]["severity"], "INFO")

        subs = data["subsystem_health"]
        self.assertEqual(subs["database"], "healthy")
        self.assertEqual(subs["api"], "healthy")
        self.assertEqual(subs["auth"], "healthy")

    def test_metrics_summary_unauthorized_cases(self) -> None:
        """GET /api/v1/metrics/summary enforces strict authentication and authorization boundaries."""
        # 1. Unauthenticated request
        res_unauth = self.client.get("/api/v1/metrics/summary")
        self.assertEqual(res_unauth.status_code, 401)

        # 2. Authenticated user without audit.read permission (Standard Member)
        res_forbidden = self.client.get("/api/v1/metrics/summary", headers=self.headers_member)
        self.assertEqual(res_forbidden.status_code, 403)
        body = res_forbidden.json()
        self.assertIn("AUTH_PERMISSION_DENIED", body.get("error", {}).get("code", ""))

    def test_correlation_headers_propagation(self) -> None:
        """Verifies X-Request-ID and W3C TraceContext headers are propagated through API pipeline."""
        custom_request_id = "req-integration-test-correlation-001"
        custom_trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
        custom_traceparent = f"00-{custom_trace_id}-00f067aa0ba902b7-01"

        res = self.client.get(
            "/health",
            headers={
                "X-Request-ID": custom_request_id,
                "traceparent": custom_traceparent,
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("X-Request-ID"), custom_request_id)
        self.assertEqual(res.headers.get("X-Trace-ID"), custom_trace_id)
        self.assertIn(custom_trace_id, res.headers.get("traceparent", ""))
        self.assertIn("ms", res.headers.get("X-Process-Time", ""))

    def test_legacy_health_endpoints_backwards_compatibility(self) -> None:
        """Verifies GET /api/v1/health and GET /api/v1/health/details continue to function cleanly."""
        res_health = self.client.get("/api/v1/health")
        self.assertEqual(res_health.status_code, 200)
        data = res_health.json()
        self.assertIn(data["status"], ("healthy", "degraded"))
        self.assertIn("version", data)
        self.assertIn("environment", data)
        self.assertIn("timestamp", data)

        res_details = self.client.get("/api/v1/health/details")
        self.assertEqual(res_details.status_code, 200)
        body = res_details.json()
        self.assertTrue(body["success"])
        self.assertIn("components", body["data"])
        self.assertIn("database", body["data"]["components"])

    @patch("backend.app.services.health_service.HealthService.check_database")
    def test_unhealthy_dependency_triggers_503(self, mock_check_db) -> None:
        """Simulates database outage and verifies /health/database and /health return 503 Service Unavailable."""
        from backend.app.schemas.health import DatabaseHealthResponse, DatabasePoolInfo

        mock_check_db.return_value = (
            DatabaseHealthResponse(
                status="unhealthy",
                latency_ms=5000.0,
                database="postgresql",
                version="PostgreSQL 16.4",
                vector_extension=False,
                pool=DatabasePoolInfo(size=20, checked_out=20, overflow=10),
            ),
            503,
        )

        # 1. Isolated database probe returns 503
        res_db = self.client.get("/health/database")
        self.assertEqual(res_db.status_code, 503)
        self.assertEqual(res_db.json()["status"], "unhealthy")

        # 2. Composite health probe returns 503
        res_comp = self.client.get("/health")
        self.assertEqual(res_comp.status_code, 503)
        self.assertEqual(res_comp.json()["status"], "unhealthy")


if __name__ == "__main__":
    unittest.main()
