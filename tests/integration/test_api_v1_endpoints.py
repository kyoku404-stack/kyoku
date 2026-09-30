"""Integration Test Suite: Phase 1.2 API v1 Endpoints & Middleware Pipeline.

Verifies:
- Middleware pipeline: RequestIDMiddleware (X-Request-ID) and LoggingMiddleware (X-Process-Time)
- Central Exception handling returning standardized ApiErrorResponse envelope
- Auth endpoints: /api/v1/auth/login, /api/v1/auth/refresh, /api/v1/auth/me, /api/v1/auth/logout
- Organization endpoints: /api/v1/organizations/current
- Users endpoints: /api/v1/users, /api/v1/users/{id}
- Documents endpoints: /api/v1/documents/upload, /api/v1/documents
- Search endpoints: /api/v1/search/hybrid
- Chat endpoints: /api/v1/chat/query, /api/v1/chat/stream (SSE)
- Analytics endpoints: /api/v1/analytics/summary, /api/v1/analytics/usage
- Health endpoints: /api/v1/health, /api/v1/health/details
- OpenAPI documentation schema completeness
"""

import io
import unittest
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app


class TestApiV1EndpointsIntegration(unittest.TestCase):
    """Integration test suite for API v1 routes and middleware."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        # Obtain a valid access token for authenticated test flows
        login_res = cls.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "admin@enterprise.com", "password": "SecurePassword123!"},
        )
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        data = login_res.json()["data"]
        cls.access_token = data["access_token"]
        cls.refresh_token = data["refresh_token"]
        cls.auth_headers = {"Authorization": f"Bearer {cls.access_token}"}

    def test_middleware_headers_present(self) -> None:
        """Verify X-Request-ID and X-Process-Time headers are attached to responses."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("x-request-id", res.headers)
        self.assertIn("x-process-time", res.headers)

    def test_auth_login_success(self) -> None:
        """Verify POST /api/v1/auth/login returns standard ApiResponse envelope."""
        res = self.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "user@enterprise.com", "password": "SecurePassword123!"},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertIn("access_token", body["data"])
        self.assertIn("refresh_token", body["data"])
        self.assertEqual(body["data"]["token_type"], "bearer")

    def test_auth_login_validation_error(self) -> None:
        """Verify validation errors conform to standardized ApiErrorResponse envelope."""
        res = self.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "not-an-email", "password": "short"},
        )
        self.assertEqual(res.status_code, 422)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")
        self.assertIsNotNone(body["error"]["details"])

    def test_auth_refresh_token(self) -> None:
        """Verify POST /api/v1/auth/refresh issues a new access token."""
        res = self.client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": self.refresh_token},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertIn("access_token", body["data"])

    def test_auth_me_authenticated_and_unauthenticated(self) -> None:
        """Verify GET /api/v1/auth/me enforces JWT authentication."""
        # Unauthenticated -> 401 Unauthorized
        unauth_res = self.client.get(f"{settings.API_V1_STR}/auth/me")
        self.assertEqual(unauth_res.status_code, 401)
        unauth_body = unauth_res.json()
        self.assertFalse(unauth_body["success"])
        self.assertEqual(unauth_body["error"]["code"], "AUTH_UNAUTHORIZED")

        # Authenticated -> 200 OK
        auth_res = self.client.get(f"{settings.API_V1_STR}/auth/me", headers=self.auth_headers)
        self.assertEqual(auth_res.status_code, 200)
        body = auth_res.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["email"], "admin@enterprise.com")

    def test_auth_logout(self) -> None:
        """Verify POST /api/v1/auth/logout succeeds."""
        res = self.client.post(f"{settings.API_V1_STR}/auth/logout", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])

    def test_organizations_current(self) -> None:
        """Verify GET /api/v1/organizations/current returns tenant info."""
        res = self.client.get(f"{settings.API_V1_STR}/organizations/current", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertIn("name", body["data"])
        self.assertIn("domain", body["data"])

    def test_users_list_and_detail(self) -> None:
        """Verify GET /api/v1/users paginated response and detail endpoint."""
        res = self.client.get(f"{settings.API_V1_STR}/users", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertIn("items", body["data"])

        # User detail
        user_id = body["data"]["items"][0]["id"]
        detail_res = self.client.get(f"{settings.API_V1_STR}/users/{user_id}", headers=self.auth_headers)
        self.assertEqual(detail_res.status_code, 200)
        self.assertTrue(detail_res.json()["success"])

    def test_document_upload_and_listing(self) -> None:
        """Verify document upload multipart and paginated listing."""
        file_content = b"%PDF-1.4 Mock PDF Content For Ingestion"
        files = {"file": ("enterprise_policy.pdf", io.BytesIO(file_content), "application/pdf")}
        data = {"title": "Enterprise Policy", "tags": "security,enterprise"}

        upload_res = self.client.post(
            f"{settings.API_V1_STR}/documents/upload",
            files=files,
            data=data,
            headers=self.auth_headers,
        )
        self.assertEqual(upload_res.status_code, 202)
        body = upload_res.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["filename"], "enterprise_policy.pdf")
        self.assertEqual(body["data"]["status"], "PROCESSING")

        # Unsupported file rejection
        bad_files = {"file": ("virus.exe", io.BytesIO(b"bad"), "application/x-msdownload")}
        bad_res = self.client.post(
            f"{settings.API_V1_STR}/documents/upload",
            files=bad_files,
            headers=self.auth_headers,
        )
        self.assertEqual(bad_res.status_code, 422)
        self.assertEqual(bad_res.json()["error"]["code"], "UNSUPPORTED_FILE_TYPE")

        # Document listing
        list_res = self.client.get(f"{settings.API_V1_STR}/documents", headers=self.auth_headers)
        self.assertEqual(list_res.status_code, 200)
        self.assertTrue(list_res.json()["success"])
        self.assertIn("items", list_res.json()["data"])

    def test_hybrid_search(self) -> None:
        """Verify POST /api/v1/search/hybrid returns ranked results."""
        payload = {
            "query": "enterprise remote work guidelines and stipend",
            "top_k": 10,
            "filters": {"document_types": ["pdf", "docx"]},
        }
        res = self.client.post(
            f"{settings.API_V1_STR}/search/hybrid",
            json=payload,
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertGreaterEqual(body["data"]["total_results"], 1)
        self.assertIn("results", body["data"])

    def test_chat_query_synchronous(self) -> None:
        """Verify POST /api/v1/chat/query returns answer and citations."""
        payload = {
            "query": "What is the annual home office stipend?",
            "top_k": 5,
            "include_citations": True,
        }
        res = self.client.post(
            f"{settings.API_V1_STR}/chat/query",
            json=payload,
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertIn("answer", body["data"])
        self.assertIn("citations", body["data"])

    def test_chat_stream_sse(self) -> None:
        """Verify POST /api/v1/chat/stream returns valid Server-Sent Events."""
        payload = {
            "query": "Summarize our quarterly security review policies.",
        }
        res = self.client.post(
            f"{settings.API_V1_STR}/chat/stream",
            json=payload,
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/event-stream", res.headers["content-type"])
        text = res.text
        self.assertIn("event: citation", text)
        self.assertIn("event: token", text)
        self.assertIn("event: done", text)

    def test_analytics_endpoints(self) -> None:
        """Verify GET /api/v1/analytics/summary and /usage."""
        summary_res = self.client.get(f"{settings.API_V1_STR}/analytics/summary", headers=self.auth_headers)
        self.assertEqual(summary_res.status_code, 200)
        self.assertTrue(summary_res.json()["success"])
        self.assertIn("total_documents", summary_res.json()["data"])

        usage_res = self.client.get(f"{settings.API_V1_STR}/analytics/usage", headers=self.auth_headers)
        self.assertEqual(usage_res.status_code, 200)
        self.assertTrue(usage_res.json()["success"])
        self.assertIn("queries_today", usage_res.json()["data"])

    def test_health_endpoints(self) -> None:
        """Verify GET /api/v1/health and GET /api/v1/health/details."""
        health_res = self.client.get(f"{settings.API_V1_STR}/health")
        self.assertEqual(health_res.status_code, 200)
        self.assertEqual(health_res.json()["status"], "healthy")

        details_res = self.client.get(f"{settings.API_V1_STR}/health/details")
        self.assertEqual(details_res.status_code, 200)
        self.assertTrue(details_res.json()["success"])
        self.assertIn("components", details_res.json()["data"])

    def test_openapi_schema_contains_v1_routes(self) -> None:
        """Verify OpenAPI documentation accurately registers all v1 endpoints."""
        res = self.client.get(f"{settings.API_V1_STR}/openapi.json")
        self.assertEqual(res.status_code, 200)
        paths = res.json()["paths"]

        expected_paths = [
            f"{settings.API_V1_STR}/auth/login",
            f"{settings.API_V1_STR}/auth/refresh",
            f"{settings.API_V1_STR}/auth/me",
            f"{settings.API_V1_STR}/users",
            f"{settings.API_V1_STR}/organizations/current",
            f"{settings.API_V1_STR}/documents/upload",
            f"{settings.API_V1_STR}/documents",
            f"{settings.API_V1_STR}/search/hybrid",
            f"{settings.API_V1_STR}/chat/query",
            f"{settings.API_V1_STR}/chat/stream",
            f"{settings.API_V1_STR}/analytics/summary",
            f"{settings.API_V1_STR}/health",
        ]

        for path in expected_paths:
            self.assertIn(path, paths, f"Expected endpoint path '{path}' missing from OpenAPI schema")


if __name__ == "__main__":
    unittest.main()
