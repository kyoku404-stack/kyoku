"""Integration Test Suite: DevOps, Container Readiness & Observability Pipeline.

Verifies:
- Central and detailed container health check endpoints (/api/v1/health, /api/v1/health/details)
- Distributed request tracing and correlation ID propagation (X-Request-ID)
- Request execution duration telemetry (X-Process-Time)
- Cross-Origin Resource Sharing (CORS) preflight and policy enforcement
- OpenAPI 3.1 specification completeness and interactive documentation (Swagger / Redoc)
- Standardized error envelope integrity on 401 Unauthorized, 422 Validation Error, and AppExceptions
- Environment configuration and runtime defaults
"""

import io
import unittest
import uuid

from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app


class TestDevOpsIntegration(unittest.TestCase):
    """Integration test case for DevOps, infrastructure readiness, and observability."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        # Login to obtain access token for authenticated probes
        login_res = cls.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "admin@enterprise.com", "password": "SecurePassword123!"},
        )
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        data = login_res.json()["data"]
        cls.access_token = data["access_token"]
        cls.auth_headers = {"Authorization": f"Bearer {cls.access_token}"}

    def test_container_health_probe_contract(self) -> None:
        """Verify GET /api/v1/health satisfies container orchestrator probe contract."""
        res = self.client.get(f"{settings.API_V1_STR}/health")
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("version"), settings.VERSION)
        self.assertEqual(data.get("environment"), settings.ENVIRONMENT)
        self.assertIn("timestamp", data)

    def test_system_diagnostics_detailed_contract(self) -> None:
        """Verify GET /api/v1/health/details returns component health metrics in standard envelope."""
        res = self.client.get(f"{settings.API_V1_STR}/health/details")
        self.assertEqual(res.status_code, 200)

        body = res.json()
        self.assertTrue(body.get("success"))
        self.assertIn("data", body)

        details = body["data"]
        self.assertEqual(details.get("status"), "healthy")
        self.assertGreaterEqual(details.get("uptime_seconds", -1), 0)
        self.assertIn("components", details)
        self.assertIn("database", details["components"])
        self.assertIn("redis", details["components"])

    def test_request_id_inbound_propagation(self) -> None:
        """Verify custom X-Request-ID is preserved across request lifecycle and returned in headers."""
        custom_req_id = "keep-trace-custom-id-" + str(uuid.uuid4())
        res = self.client.get(
            f"{settings.API_V1_STR}/health",
            headers={"X-Request-ID": custom_req_id},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("x-request-id"), custom_req_id)

    def test_request_id_automatic_uuid_generation(self) -> None:
        """Verify absence of X-Request-ID causes automated generation of valid UUID4."""
        res = self.client.get(f"{settings.API_V1_STR}/health")
        self.assertEqual(res.status_code, 200)

        req_id = res.headers.get("x-request-id")
        self.assertIsNotNone(req_id)
        # Verify valid UUID format
        parsed_uuid = uuid.UUID(req_id)
        self.assertEqual(str(parsed_uuid), req_id)

    def test_response_process_time_header(self) -> None:
        """Verify LoggingMiddleware measures request duration and attaches X-Process-Time."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)

        process_time = res.headers.get("x-process-time")
        self.assertIsNotNone(process_time)
        self.assertTrue(process_time.endswith("ms"))
        # Parse float milliseconds value
        ms = float(process_time[:-2])
        self.assertGreaterEqual(ms, 0.0)

    def test_cors_preflight_configuration(self) -> None:
        """Verify CORS OPTIONS preflight permits configured origins and exposed headers."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization,Content-Type,X-Request-ID",
        }
        res = self.client.options(f"{settings.API_V1_STR}/auth/login", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.headers.get("access-control-allow-origin"), "http://localhost:3000"
        )
        self.assertIn("POST", res.headers.get("access-control-allow-methods", ""))

    def test_openapi_specification_completeness(self) -> None:
        """Verify OpenAPI 3.1 specification contains all Phase 1.2 domain router paths."""
        res = self.client.get(f"{settings.API_V1_STR}/openapi.json")
        self.assertEqual(res.status_code, 200)

        schema = res.json()
        self.assertIn("openapi", schema)
        self.assertEqual(schema["info"]["title"], settings.PROJECT_NAME)
        self.assertEqual(schema["info"]["version"], settings.VERSION)

        paths = schema.get("paths", {})
        expected_endpoints = [
            f"{settings.API_V1_STR}/health",
            f"{settings.API_V1_STR}/health/details",
            f"{settings.API_V1_STR}/auth/login",
            f"{settings.API_V1_STR}/auth/refresh",
            f"{settings.API_V1_STR}/auth/me",
            f"{settings.API_V1_STR}/users",
            f"{settings.API_V1_STR}/organizations/current",
            f"{settings.API_V1_STR}/documents",
            f"{settings.API_V1_STR}/search/hybrid",
            f"{settings.API_V1_STR}/chat/query",
            f"{settings.API_V1_STR}/chat/stream",
            f"{settings.API_V1_STR}/analytics/summary",
        ]
        for ep in expected_endpoints:
            self.assertIn(ep, paths, f"Expected endpoint {ep} missing from OpenAPI paths")

    def test_interactive_api_documentation_endpoints(self) -> None:
        """Verify Swagger UI and Redoc interactive portals are rendered."""
        swagger_res = self.client.get("/docs")
        self.assertEqual(swagger_res.status_code, 200)
        self.assertIn("html", swagger_res.headers.get("content-type", ""))

        redoc_res = self.client.get("/redoc")
        self.assertEqual(redoc_res.status_code, 200)
        self.assertIn("html", redoc_res.headers.get("content-type", ""))

    def test_standardized_error_envelope_on_unauthorized(self) -> None:
        """Verify UnauthorizedException returns standardized ApiErrorResponse envelope."""
        res = self.client.get(f"{settings.API_V1_STR}/auth/me")
        self.assertEqual(res.status_code, 401)

        body = res.json()
        self.assertFalse(body.get("success"))
        self.assertIn("error", body)
        self.assertEqual(body["error"].get("code"), "AUTH_UNAUTHORIZED")
        self.assertIn("message", body["error"])

    def test_standardized_error_envelope_on_validation_failure(self) -> None:
        """Verify 422 RequestValidationError returns the standardized ApiErrorResponse envelope."""
        res = self.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "invalid-email-no-at-sign", "password": ""},
        )
        self.assertEqual(res.status_code, 422)

        body = res.json()
        self.assertFalse(body.get("success"))
        self.assertIn("error", body)
        self.assertEqual(body["error"].get("code"), "VALIDATION_ERROR")
        self.assertIn("message", body["error"])
        self.assertIsNotNone(body["error"].get("details"))

    def test_standardized_error_envelope_on_domain_validation_exception(self) -> None:
        """Verify business ValidationException returns standardized ApiErrorResponse envelope."""
        # Uploading unsupported file type triggers ValidationException
        file_payload = {"file": ("unsupported_script.exe", io.BytesIO(b"fake executable"), "application/octet-stream")}
        res = self.client.post(
            f"{settings.API_V1_STR}/documents/upload",
            files=file_payload,
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 422)

        body = res.json()
        self.assertFalse(body.get("success"))
        self.assertIn("error", body)
        self.assertEqual(body["error"].get("code"), "UNSUPPORTED_FILE_TYPE")
        self.assertIn("Unsupported file type", body["error"].get("message"))

    def test_settings_environment_configuration(self) -> None:
        """Verify Settings instance possesses required operational parameters."""
        self.assertIsNotNone(settings.PROJECT_NAME)
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertEqual(settings.API_V1_STR, "/api/v1")
        self.assertGreater(settings.ACCESS_TOKEN_EXPIRE_MINUTES, 0)
        self.assertIn("http://localhost:3000", settings.BACKEND_CORS_ORIGINS)


if __name__ == "__main__":
    unittest.main()
