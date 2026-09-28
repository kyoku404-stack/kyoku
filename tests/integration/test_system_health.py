"""Integration Test Suite: System Health & API Discovery.

Verifies end-to-end routing, application startup, OpenAPI schema generation,
CORS headers, and system health status.
"""

import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings


class TestSystemHealthIntegration(unittest.TestCase):
    """Integration test case for system-level endpoints and health checks."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_root_discovery_endpoint(self) -> None:
        """Verifies GET / returns application metadata and online status."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], settings.PROJECT_NAME)
        self.assertEqual(data["version"], settings.VERSION)
        self.assertEqual(data["status"], "online")
        self.assertEqual(data["documentation"], "/docs")

    def test_api_v1_health_check(self) -> None:
        """Verifies GET /api/v1/health returns healthy status and timestamp."""
        response = self.client.get(f"{settings.API_V1_STR}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["version"], settings.VERSION)
        self.assertIn("timestamp", data)

    def test_openapi_schema_generation(self) -> None:
        """Verifies FastAPI generates valid OpenAPI JSON schema."""
        response = self.client.get(f"{settings.API_V1_STR}/openapi.json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("openapi", data)
        self.assertEqual(data["info"]["title"], settings.PROJECT_NAME)
        self.assertIn(f"{settings.API_V1_STR}/health", data["paths"])

    def test_interactive_docs_accessible(self) -> None:
        """Verifies Swagger /docs and Redoc /redoc are rendered."""
        swagger_res = self.client.get("/docs")
        self.assertEqual(swagger_res.status_code, 200)

        redoc_res = self.client.get("/redoc")
        self.assertEqual(redoc_res.status_code, 200)

    def test_cors_preflight_headers(self) -> None:
        """Verifies CORS middleware attaches proper access-control headers."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
        response = self.client.options(f"{settings.API_V1_STR}/health", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://localhost:3000")


if __name__ == "__main__":
    unittest.main()
