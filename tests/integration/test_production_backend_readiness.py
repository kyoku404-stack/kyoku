"""Integration Test Suite: Production Backend Readiness & Security Hardening.

Specification Source: devdocs/p1/p1.10.txt (Chapters 6, 8, 9, 11, 15, 18)
Phase: 1.10 — Deployment, Infrastructure & Production Readiness
Role: Member 2 (Backend Lead)
"""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app


class TestProductionBackendReadinessIntegration(unittest.TestCase):
    """Integration test suite validating production backend behavior and security headers."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_root_discovery_and_security_headers(self) -> None:
        """Verifies root endpoint returns 200 OK along with mandatory security headers."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertEqual(data["name"], settings.PROJECT_NAME)
        self.assertEqual(data["version"], settings.VERSION)

        # Defense-in-depth security headers
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(response.headers.get("X-XSS-Protection"), "1; mode=block")
        self.assertEqual(
            response.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin"
        )
        self.assertIn("geolocation=()", response.headers.get("Permissions-Policy", ""))
        self.assertIsNotNone(response.headers.get("X-Request-ID"))

    def test_health_probes_security_headers(self) -> None:
        """Verifies composite /health probe executes and includes security headers."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")

    def test_gzip_compression_on_metrics(self) -> None:
        """Verifies GZip middleware handles compressed responses on large payloads."""
        headers = {"Accept-Encoding": "gzip"}
        response = self.client.get("/metrics", headers=headers)
        self.assertEqual(response.status_code, 200)

        # Large responses (metrics payload > 1000 bytes) should be gzip compressed
        if len(response.content) > settings.GZIP_MINIMUM_SIZE:
            self.assertEqual(response.headers.get("content-encoding"), "gzip")

    def test_cors_preflight_headers(self) -> None:
        """Verifies CORS headers are properly formatted for trusted origin."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        }
        response = self.client.options("/health", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"), "http://localhost:3000"
        )

    def test_openapi_schema_availability(self) -> None:
        """Verifies OpenAPI schema is exposed when ENABLE_OPENAPI_DOCS is enabled."""
        if settings.ENABLE_OPENAPI_DOCS:
            response = self.client.get(f"{settings.API_V1_STR}/openapi.json")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["info"]["title"], settings.PROJECT_NAME)
            self.assertEqual(data["info"]["version"], settings.VERSION)


if __name__ == "__main__":
    unittest.main()
