"""KEEP Enterprise Platform — Centralized Structured Logging Configuration.

Specification Source: devdocs/p1/p1.9.txt (Chapter 4, 5, 6, 11)
Phase: 1.9 — Logging, Monitoring & System Observability
Role: Member 2 (Backend & Database Lead)

Implements canonical JSON structured logging, sensitive data redaction,
W3C distributed trace correlation, and contextvars request tracking.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import traceback
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Context variables for asynchronous request context propagation
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
trace_id_ctx: ContextVar[str | None] = ContextVar("trace_id", default=None)
user_id_ctx: ContextVar[str | None] = ContextVar("user_id", default=None)
organization_id_ctx: ContextVar[str | None] = ContextVar("organization_id", default=None)


def set_request_context(
    request_id: str | None = None,
    trace_id: str | None = None,
    user_id: str | None = None,
    organization_id: str | None = None,
) -> None:
    """Sets asynchronous context variables for the current execution context."""
    if request_id is not None:
        request_id_ctx.set(request_id)
    if trace_id is not None:
        trace_id_ctx.set(trace_id)
    if user_id is not None:
        user_id_ctx.set(user_id)
    if organization_id is not None:
        organization_id_ctx.set(organization_id)


def get_request_context() -> dict[str, str | None]:
    """Retrieves current request context variables."""
    return {
        "request_id": request_id_ctx.get(),
        "trace_id": trace_id_ctx.get(),
        "user_id": user_id_ctx.get(),
        "organization_id": organization_id_ctx.get(),
    }


def clear_request_context() -> None:
    """Clears all asynchronous request context variables."""
    request_id_ctx.set(None)
    trace_id_ctx.set(None)
    user_id_ctx.set(None)
    organization_id_ctx.set(None)


class SensitiveDataFilter(logging.Filter):
    """Filter and sanitizer to prevent accidental logging of credentials, tokens, and secrets."""

    SENSITIVE_KEYS = (
        "password",
        "hashed_password",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "secret_key",
        "authorization",
        "bearer",
        "cookie",
    )

    # Regex pattern to match sensitive key-value patterns in strings
    _PATTERN = re.compile(
        r'(?i)(password|token|secret|authorization|bearer|cookie)["\']?\s*[:=]\s*["\']?([^"\'\s,;]+)',
        re.IGNORECASE,
    )

    @classmethod
    def mask_text(cls, text: str) -> str:
        """Redacts sensitive values found in raw text."""
        return cls._PATTERN.sub(r"\1=***REDACTED***", text)

    @classmethod
    def sanitize_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively redacts sensitive dictionary keys."""
        sanitized: dict[str, Any] = {}
        for key, value in data.items():
            key_lower = str(key).lower()
            if any(s in key_lower for s in cls.SENSITIVE_KEYS):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.sanitize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, str):
                sanitized[key] = cls.mask_text(value)
            else:
                sanitized[key] = value
        return sanitized

    def filter(self, record: logging.LogRecord) -> bool:
        """Sanitizes the record message before emission."""
        if isinstance(record.msg, str):
            record.msg = self.mask_text(record.msg)
        return True


class JSONLogFormatter(logging.Formatter):
    """Canonical JSON Log Formatter conforming strictly to devdocs Chapter 6 specification.

    Output Schema:
        timestamp: ISO-8601 UTC string (e.g. 2026-10-21T21:45:00.123456Z)
        level: Severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        module: Source module identifier
        action: Event performed or HTTP method + path
        status: Success / Failure / Degraded / Quarantined
        user_id: Authenticated user UUID or None
        organization_id: Tenant UUID or None
        request_id: Correlated request ID
        trace_id: W3C Trace identifier
        execution_time_ms: Elapsed execution duration in milliseconds
        ip_address: Client IP address or None
        message: Human-readable message
        metadata: Domain-specific contextual attributes
    """

    def format(self, record: logging.LogRecord) -> str:
        # 1. Format timestamp to ISO-8601 with microsecond precision in UTC
        utc_dt = datetime.fromtimestamp(record.created, tz=UTC)
        timestamp_str = utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # 2. Extract correlation context from record or active contextvars
        context = get_request_context()
        request_id = getattr(record, "request_id", None) or context["request_id"] or "req-unknown"
        trace_id = getattr(record, "trace_id", None) or context["trace_id"]
        user_id = getattr(record, "user_id", None) or context["user_id"]
        organization_id = getattr(record, "organization_id", None) or context["organization_id"]

        # 3. Resolve module, action, and status
        module_name = getattr(record, "module_name", None) or getattr(record, "module", record.name)
        action_name = getattr(record, "action", record.funcName)
        status_name = getattr(record, "status", "success" if record.levelno < logging.ERROR else "failure")
        execution_time_ms = getattr(record, "execution_time_ms", 0.0)
        ip_address = getattr(record, "ip_address", None)

        # 4. Extract message and sanitize
        raw_msg = record.getMessage()
        sanitized_msg = SensitiveDataFilter.mask_text(raw_msg)

        # 5. Extract domain metadata
        metadata = getattr(record, "metadata", {})
        if not isinstance(metadata, dict):
            metadata = {"raw_metadata": str(metadata)}
        metadata = SensitiveDataFilter.sanitize_dict(dict(metadata))

        # 6. Handle exception tracebacks if present
        if record.exc_info:
            metadata["exception_type"] = record.exc_info[0].__name__ if record.exc_info[0] else "Exception"
            metadata["exception_message"] = str(record.exc_info[1])
            metadata["stack_trace"] = traceback.format_exception(*record.exc_info)

        # 7. Assemble canonical payload
        payload: dict[str, Any] = {
            "timestamp": timestamp_str,
            "level": record.levelname,
            "module": module_name,
            "action": action_name,
            "status": status_name,
            "user_id": user_id,
            "organization_id": organization_id,
            "request_id": request_id,
            "trace_id": trace_id,
            "execution_time_ms": round(float(execution_time_ms), 3),
            "ip_address": ip_address,
            "message": sanitized_msg,
            "metadata": metadata,
        }

        return json.dumps(payload, default=str)


def setup_logging(log_level: str = "INFO", force_json: bool | None = None) -> None:
    """Configures root logger and subsystem handlers."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Determine whether to use JSON formatting
    use_json = force_json
    if use_json is None:
        use_json = os.environ.get("LOG_FORMAT", "").lower() == "json" or os.environ.get("ENVIRONMENT", "").lower() in ("production", "staging")

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(SensitiveDataFilter())

    if use_json:
        handler.setFormatter(JSONLogFormatter())
    else:
        log_format = "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers = [handler]

    # Adjust third-party library log levels for cleanliness
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Returns a namespaced logger instance."""
    return logging.getLogger(f"keep.{name}")
