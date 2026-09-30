"""KEEP Enterprise Platform — Logging & Timing Middleware.

Calculates request processing duration and logs structured operational data.
"""

import time
from collections.abc import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.core.logging import get_logger

logger = get_logger("api.middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that measures request execution time and records structured logs."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        request_id = getattr(request.state, "request_id", "unknown")

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

            logger.info(
                "[%s] %s %s completed in %.2fms (status %d)",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
                response.status_code,
            )
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "[%s] %s %s failed after %.2fms: %s",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
                str(exc),
                exc_info=exc,
            )
            raise exc
