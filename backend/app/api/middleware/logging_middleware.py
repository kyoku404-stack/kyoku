"""KEEP Enterprise Platform — Structured Logging & Latency Tracking Middleware.

Specification Source: devdocs/p1/p1.9.txt (Chapter 4, 6, 8) & ADR-026
Phase: 1.9 — Logging, Monitoring & System Observability
Role: Member 2 (Backend & Database Lead)

Measures request latency, records Prometheus HTTP metrics, and emits
canonical structured JSON operational logs with distributed trace correlation.
"""

from __future__ import annotations

import re
import time

from backend.app.core.logging import get_logger
from backend.app.core.metrics import metrics_registry
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = get_logger("api.middleware")

# Regex to normalize UUID path parameters for Prometheus metrics to prevent label cardinality explosion
UUID_PATH_REGEX = re.compile(
    r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


def normalize_handler_path(path: str) -> str:
    """Normalizes dynamic path segments to static templates to control metric cardinality."""
    return UUID_PATH_REGEX.sub("/{id}", path)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware measuring request execution time, updating metrics, and emitting structured logs."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        request_id = getattr(request.state, "request_id", "req-unknown")
        trace_id = getattr(request.state, "trace_id", None)
        client_ip = request.client.host if request.client else None
        handler_path = normalize_handler_path(request.url.path)

        metrics_registry.increment_in_progress()

        try:
            response = await call_next(request)
            elapsed = time.perf_counter() - start_time
            duration_ms = elapsed * 1000.0

            # Attach response header
            response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

            # Record Prometheus metrics
            metrics_registry.record_request(
                method=request.method,
                handler=handler_path,
                status_code=response.status_code,
                duration_seconds=elapsed,
            )

            # Determine log status and level
            is_success = response.status_code < 400
            log_level = logger.info if is_success else logger.warning

            log_level(
                "[%s] %s %s completed in %.2fms (status %d)",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
                response.status_code,
                extra={
                    "module_name": "api",
                    "action": f"{request.method} {request.url.path}",
                    "status": "success" if is_success else "failure",
                    "execution_time_ms": duration_ms,
                    "ip_address": client_ip,
                    "request_id": request_id,
                    "trace_id": trace_id,
                    "metadata": {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                    },
                },
            )
            return response

        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            duration_ms = elapsed * 1000.0

            metrics_registry.record_request(
                method=request.method,
                handler=handler_path,
                status_code=500,
                duration_seconds=elapsed,
            )

            logger.error(
                "[%s] %s %s failed after %.2fms: %s",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
                str(exc),
                exc_info=exc,
                extra={
                    "module_name": "api",
                    "action": f"{request.method} {request.url.path}",
                    "status": "failure",
                    "execution_time_ms": duration_ms,
                    "ip_address": client_ip,
                    "request_id": request_id,
                    "trace_id": trace_id,
                    "metadata": {
                        "method": request.method,
                        "path": request.url.path,
                        "error": str(exc),
                    },
                },
            )
            raise
        finally:
            metrics_registry.decrement_in_progress()
