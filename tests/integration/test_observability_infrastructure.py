"""DevOps Integration Test Suite: Observability Infrastructure, Health SLAs, and Prometheus Telemetry.

Specification Source: devdocs/p1/p1.9.txt (Chapter 6, 7, 8, 10, 15, 16, 17)
Architecture: docs/Architecture/observability-architecture.md
Role: Member 4 (DevOps & Integration Lead)
"""

from __future__ import annotations

import time
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.constants import UserRole
from backend.app.core.logging import SensitiveDataFilter
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestObservabilityInfrastructure(unittest.TestCase):
    """DevOps test suite verifying Prometheus metrics exposition, health check SLAs, and tracing."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        # Warm up endpoints
        cls.client.get("/health")
        cls.client.get("/health/api")

        with Session(sync_test_engine) as session:
            cls.org = Organization(
                name=f"DevOps Obs Org {uuid4().hex[:6]}",
                domain=f"devops_obs_{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.flush()

            cls.admin_user = User(
                email=f"devops_admin_{uuid4().hex[:6]}@enterprise.io",
                hashed_password=get_password_hash("DevOpsSecure2026!"),
                full_name="DevOps Admin Lead",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org.id,
                is_active=True,
            )
            cls.member_user = User(
                email=f"devops_member_{uuid4().hex[:6]}@enterprise.io",
                hashed_password=get_password_hash("DevOpsSecure2026!"),
                full_name="DevOps Member User",
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
                "email": cls.admin_user.email,
                "role": "OrgAdmin",
                "org_id": str(cls.org_id),
            }
        )
        cls.headers_admin = {"Authorization": f"Bearer {cls.token_admin}"}

        cls.token_member = create_access_token(
            data={
                "sub": str(cls.member_id),
                "email": cls.member_user.email,
                "role": "Member",
                "org_id": str(cls.org_id),
            }
        )
        cls.headers_member = {"Authorization": f"Bearer {cls.token_member}"}

    # --------------------------------------------------------------------------
    # 1. Prometheus Metric Exposition Validation (GET /metrics)
    # --------------------------------------------------------------------------
    def test_prometheus_exposition_format_and_metrics(self) -> None:
        """GET /metrics returns 200 text/plain exposition matching standard Prometheus schema."""
        # Generate some traffic first to populate metrics
        self.client.get("/health")
        self.client.get("/health/database")

        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.headers["content-type"].startswith("text/plain"),
            f"Expected text/plain, got {response.headers['content-type']}",
        )

        body = response.text
        # Verify mandatory Prometheus metric declarations
        required_metrics = [
            "http_requests_total",
            "http_request_duration_seconds",
            "db_pool_active_connections",
            "storage_used_bytes",
            "ai_tokens_consumed_total",
            "process_uptime_seconds",
        ]
        for metric_name in required_metrics:
            self.assertIn(
                f"# HELP {metric_name}",
                body,
                f"Missing Prometheus HELP declaration for {metric_name}",
            )
            self.assertIn(
                f"# TYPE {metric_name}",
                body,
                f"Missing Prometheus TYPE declaration for {metric_name}",
            )

        # Verify metric labels and format
        self.assertIn("http_requests_total{", body)
        self.assertIn('handler="/health"', body)

    # --------------------------------------------------------------------------
    # 2. Multi-Tier Health Check Latency SLAs & Probes
    # --------------------------------------------------------------------------
    def test_composite_health_probe_sla(self) -> None:
        """GET /health responds with composite dependencies within strict SLA."""
        start = time.perf_counter()
        response = self.client.get("/health")
        elapsed_ms = (time.perf_counter() - start) * 1000

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["status"], ("healthy", "degraded"))
        self.assertIn("database", data["dependencies"])
        self.assertIn("storage", data["dependencies"])
        self.assertIn("api", data["dependencies"])
        self.assertIn("auth", data["dependencies"])
        self.assertLess(elapsed_ms, 250.0, f"Composite probe exceeded SLA: {elapsed_ms:.2f}ms")

    def test_database_probe_pgvector_and_sla(self) -> None:
        """GET /health/database validates PostgreSQL pool and pgvector within SLA."""
        start = time.perf_counter()
        response = self.client.get("/health/database")
        elapsed_ms = (time.perf_counter() - start) * 1000

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["status"], ("healthy", "degraded"))
        self.assertTrue(data["vector_extension"])
        self.assertIn("pool", data)
        self.assertGreaterEqual(data["pool"]["size"], 1)
        self.assertLess(elapsed_ms, 200.0, f"Database probe exceeded SLA: {elapsed_ms:.2f}ms")

    def test_storage_probe_write_capability_and_sla(self) -> None:
        """GET /health/storage verifies filesystem write probe and capacity within SLA."""
        start = time.perf_counter()
        response = self.client.get("/health/storage")
        elapsed_ms = (time.perf_counter() - start) * 1000

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["status"], ("healthy", "degraded"))
        self.assertTrue(data["writable"])
        self.assertGreaterEqual(data["free_bytes"], 0)
        self.assertGreater(data["total_bytes"], 0)
        self.assertLessEqual(data["used_percent"], 100.0)
        self.assertLess(elapsed_ms, 200.0, f"Storage probe exceeded SLA: {elapsed_ms:.2f}ms")

    def test_api_probe_runtime_diagnostics_and_sla(self) -> None:
        """GET /health/api validates memory, event loop and uptime within SLA."""
        start = time.perf_counter()
        response = self.client.get("/health/api")
        elapsed_ms = (time.perf_counter() - start) * 1000

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertGreaterEqual(data["uptime_seconds"], 0)
        self.assertGreater(data["memory_rss_mb"], 0)
        self.assertIn("python_version", data)
        self.assertLess(elapsed_ms, 150.0, f"API probe exceeded SLA: {elapsed_ms:.2f}ms")

    def test_auth_probe_jwt_readiness_and_sla(self) -> None:
        """GET /health/auth verifies cryptographic JWT configuration within SLA."""
        start = time.perf_counter()
        response = self.client.get("/health/auth")
        elapsed_ms = (time.perf_counter() - start) * 1000

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["jwt_secret_configured"])
        self.assertEqual(data["algorithm"], settings.ALGORITHM)
        self.assertEqual(data["access_token_expire_minutes"], settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.assertLess(elapsed_ms, 150.0, f"Auth probe exceeded SLA: {elapsed_ms:.2f}ms")

    # --------------------------------------------------------------------------
    # 3. System Telemetry Summary RBAC & Aggregations
    # --------------------------------------------------------------------------
    def test_metrics_summary_rbac_protection(self) -> None:
        """GET /api/v1/metrics/summary strictly enforces authentication and admin authorization."""
        # Anonymous request -> 401
        res_anon = self.client.get("/api/v1/metrics/summary")
        self.assertEqual(res_anon.status_code, 401)

        # Standard Member user -> 403 Forbidden
        res_member = self.client.get("/api/v1/metrics/summary", headers=self.headers_member)
        self.assertEqual(res_member.status_code, 403)

        # OrgAdmin user -> 200 OK
        res_admin = self.client.get("/api/v1/metrics/summary", headers=self.headers_admin)
        self.assertEqual(res_admin.status_code, 200)

        payload = res_admin.json()
        self.assertTrue(payload["success"])
        data = payload["data"]
        self.assertIn(data["system_status"], ("healthy", "degraded", "unhealthy"))
        self.assertIn("kpis", data)
        kpis = data["kpis"]
        self.assertIn("requests_per_second", kpis)
        self.assertIn("p95_latency_ms", kpis)
        self.assertIn("error_rate_percent", kpis)
        self.assertIn("storage_percent", kpis)
        self.assertIn("database_pool_usage_percent", kpis)
        self.assertIn("alerts", data)
        self.assertIn("subsystem_health", data)

    # --------------------------------------------------------------------------
    # 4. W3C TraceContext & Request Correlation Header Propagation
    # --------------------------------------------------------------------------
    def test_request_id_and_w3c_traceparent_propagation(self) -> None:
        """Middleware preserves or synthesizes X-Request-ID, X-Trace-ID, and W3C traceparent."""
        custom_req_id = "req-devops-custom-999"
        w3c_traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

        res = self.client.get(
            "/health",
            headers={
                "X-Request-ID": custom_req_id,
                "traceparent": w3c_traceparent,
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("x-request-id"), custom_req_id)
        self.assertEqual(res.headers.get("x-trace-id"), "4bf92f3577b34da6a3ce929d0e0e4736")
        self.assertTrue(res.headers.get("traceparent").startswith("00-4bf92f3577b34da6a3ce929d0e0e4736-"))
        self.assertIn("x-process-time", res.headers)

    def test_auto_synthesized_correlation_identifiers(self) -> None:
        """When headers are absent, middleware generates valid UUID4 request ID and hex trace ID."""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)

        req_id = res.headers.get("x-request-id")
        trace_id = res.headers.get("x-trace-id")
        traceparent = res.headers.get("traceparent")

        self.assertIsNotNone(req_id)
        self.assertIsNotNone(trace_id)
        self.assertIsNotNone(traceparent)
        self.assertEqual(len(trace_id), 32)
        self.assertTrue(traceparent.startswith("00-"))

    # --------------------------------------------------------------------------
    # 5. Sensitive Data Redaction in Logging Framework
    # --------------------------------------------------------------------------
    def test_sensitive_credentials_redaction_in_logs(self) -> None:
        """SensitiveDataFilter recursively sanitizes passwords, tokens, and authorization keys."""
        raw_data = {
            "password": "ClearTextPassword123!",
            "access_token": "secret_jwt_token_payload",
            "nested": {
                "secret_key": "enterprise_api_key_777",
                "safe_field": "public_data",
            },
        }

        sanitized = SensitiveDataFilter.sanitize_dict(raw_data)
        self.assertEqual(sanitized["password"], "***REDACTED***")
        self.assertEqual(sanitized["access_token"], "***REDACTED***")
        self.assertEqual(sanitized["nested"]["secret_key"], "***REDACTED***")
        self.assertEqual(sanitized["nested"]["safe_field"], "public_data")

        # Test text masking
        text_with_secret = "User login authorization: Bearer secret_token_123"
        masked = SensitiveDataFilter.mask_text(text_with_secret)
        self.assertIn("***REDACTED***", masked)
