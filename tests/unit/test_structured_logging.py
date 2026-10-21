"""Unit Test Suite for Centralized Structured Logging & Distributed TraceContext.

Specification Source: devdocs/p1/p1.9.txt (Chapter 4, 5, 6, 11) & ADR-026
Phase: 1.9 — Logging, Monitoring & System Observability
Role: Member 2 (Backend & Database Lead)
"""

from __future__ import annotations

import json
import logging
import unittest

from backend.app.api.middleware.logging_middleware import normalize_handler_path
from backend.app.core.logging import (
    JSONLogFormatter,
    clear_request_context,
    get_request_context,
    set_request_context,
)


class TestStructuredLoggingUnit(unittest.TestCase):
    """Tests canonical JSON log formatter, contextvars propagation, and redaction filters."""

    def setUp(self) -> None:
        clear_request_context()
        self.formatter = JSONLogFormatter()

    def tearDown(self) -> None:
        clear_request_context()

    def test_contextvars_lifecycle(self) -> None:
        """Verifies contextvars set, get, and clear operations."""
        self.assertIsNone(get_request_context()["request_id"])
        self.assertIsNone(get_request_context()["trace_id"])

        set_request_context(
            request_id="req-test-123",
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            user_id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
            organization_id="7ca38f12-2111-4b12-a1b2-1c2d3e4f5a6b",
        )

        ctx = get_request_context()
        self.assertEqual(ctx["request_id"], "req-test-123")
        self.assertEqual(ctx["trace_id"], "4bf92f3577b34da6a3ce929d0e0e4736")
        self.assertEqual(ctx["user_id"], "3fa85f64-5717-4562-b3fc-2c963f66afa6")
        self.assertEqual(ctx["organization_id"], "7ca38f12-2111-4b12-a1b2-1c2d3e4f5a6b")

        clear_request_context()
        self.assertIsNone(get_request_context()["request_id"])
        self.assertIsNone(get_request_context()["trace_id"])

    def test_json_formatter_canonical_schema(self) -> None:
        """Verifies JSONLogFormatter produces all mandatory fields from devdocs Chapter 6."""
        set_request_context(
            request_id="req-98f24a1b-312c-47ea-8d19-bca128f73110",
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            user_id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
            organization_id="7ca38f12-2111-4b12-a1b2-1c2d3e4f5a6b",
        )

        record = logging.LogRecord(
            name="keep.document_service",
            level=logging.INFO,
            pathname="document_service.py",
            lineno=42,
            msg="Document version 1 created successfully",
            args=(),
            exc_info=None,
        )
        record.action = "document_upload_completed"  # type: ignore[attr-defined]
        record.module_name = "document_service"  # type: ignore[attr-defined]
        record.status = "success"  # type: ignore[attr-defined]
        record.execution_time_ms = 14.82  # type: ignore[attr-defined]
        record.ip_address = "192.168.1.105"  # type: ignore[attr-defined]
        record.metadata = {  # type: ignore[attr-defined]
            "document_id": "e8b23f11-9a1c-4b62-9e22-83bfa99321e1",
            "filename": "quarterly_financials_2026.pdf",
            "file_size_bytes": 1048576,
        }

        output_str = self.formatter.format(record)
        data = json.loads(output_str)

        # Mandatory fields
        self.assertIn("timestamp", data)
        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["module"], "document_service")
        self.assertEqual(data["action"], "document_upload_completed")
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["user_id"], "3fa85f64-5717-4562-b3fc-2c963f66afa6")
        self.assertEqual(data["organization_id"], "7ca38f12-2111-4b12-a1b2-1c2d3e4f5a6b")
        self.assertEqual(data["request_id"], "req-98f24a1b-312c-47ea-8d19-bca128f73110")
        self.assertEqual(data["trace_id"], "4bf92f3577b34da6a3ce929d0e0e4736")
        self.assertEqual(data["execution_time_ms"], 14.82)
        self.assertEqual(data["ip_address"], "192.168.1.105")
        self.assertEqual(data["message"], "Document version 1 created successfully")
        self.assertEqual(data["metadata"]["filename"], "quarterly_financials_2026.pdf")
        self.assertEqual(data["metadata"]["file_size_bytes"], 1048576)

    def test_sensitive_data_redaction_in_messages_and_metadata(self) -> None:
        """Verifies that passwords, tokens, and authorization secrets are masked in logs."""
        record = logging.LogRecord(
            name="keep.auth",
            level=logging.WARNING,
            pathname="auth.py",
            lineno=101,
            msg="Failed login attempt with password: SuperSecretPassword123! and token: eyJhbGciOi...",
            args=(),
            exc_info=None,
        )
        record.metadata = {  # type: ignore[attr-defined]
            "user_email": "attacker@example.com",
            "raw_password": "PlainPasswordToMask",
            "access_token": "SecretJwtToken",
            "nested": {
                "bearer_token": "Bearer 123456789",
                "normal_field": "public_value",
            },
        }

        output_str = self.formatter.format(record)
        data = json.loads(output_str)

        self.assertNotIn("SuperSecretPassword123!", data["message"])
        self.assertIn("***REDACTED***", data["message"])
        self.assertEqual(data["metadata"]["raw_password"], "***REDACTED***")
        self.assertEqual(data["metadata"]["access_token"], "***REDACTED***")
        self.assertEqual(data["metadata"]["nested"]["bearer_token"], "***REDACTED***")
        self.assertEqual(data["metadata"]["nested"]["normal_field"], "public_value")

    def test_exception_stack_trace_formatting(self) -> None:
        """Verifies that uncaught exceptions include formatted stack traces and error types."""
        try:
            raise ValueError("Database connection dropped unexpectedly")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="keep.db",
            level=logging.ERROR,
            pathname="db.py",
            lineno=75,
            msg="Database query failure",
            args=(),
            exc_info=exc_info,
        )

        output_str = self.formatter.format(record)
        data = json.loads(output_str)

        self.assertEqual(data["status"], "failure")
        self.assertEqual(data["metadata"]["exception_type"], "ValueError")
        self.assertEqual(data["metadata"]["exception_message"], "Database connection dropped unexpectedly")
        self.assertIsInstance(data["metadata"]["stack_trace"], list)
        self.assertTrue(len(data["metadata"]["stack_trace"]) > 0)

    def test_normalize_handler_path(self) -> None:
        """Verifies UUID path segments are mapped to static template placeholders."""
        self.assertEqual(
            normalize_handler_path("/api/v1/documents/e8b23f11-9a1c-4b62-9e22-83bfa99321e1"),
            "/api/v1/documents/{id}",
        )
        self.assertEqual(
            normalize_handler_path("/api/v1/documents/e8b23f11-9a1c-4b62-9e22-83bfa99321e1/download"),
            "/api/v1/documents/{id}/download",
        )
        self.assertEqual(
            normalize_handler_path("/health/database"),
            "/health/database",
        )


if __name__ == "__main__":
    unittest.main()
