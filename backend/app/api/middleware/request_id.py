"""KEEP Enterprise Platform — Request ID & Distributed TraceContext Middleware.

Specification Source: devdocs/p1/p1.9.txt (Chapter 6, 11) & ADR-026
Phase: 1.9 — Logging, Monitoring & System Observability
Role: Member 2 (Backend & Database Lead)

Extracts and propagates X-Request-ID and W3C TraceContext (traceparent)
correlation identifiers across asynchronous execution pipelines.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Callable

from backend.app.core.logging import (
    clear_request_context,
    set_request_context,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"
TRACE_ID_HEADER = "X-Trace-ID"
W3C_TRACEPARENT_HEADER = "traceparent"

# Regex validator for W3C Traceparent: version-trace_id-parent_id-flags
W3C_TRACEPARENT_REGEX = re.compile(
    r"^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$",
    re.IGNORECASE,
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that injects, validates, and propagates distributed correlation identifiers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Resolve or generate Request ID (must be standard UUID)
        raw_request_id = request.headers.get(REQUEST_ID_HEADER)
        if raw_request_id and raw_request_id.strip():
            request_id = raw_request_id.strip()
        else:
            request_id = str(uuid.uuid4())

        # 2. Resolve or generate W3C TraceContext (trace_id & span_id)
        traceparent_raw = request.headers.get(W3C_TRACEPARENT_HEADER)
        trace_id: str | None = None
        span_id = uuid.uuid4().hex[:16]

        if traceparent_raw:
            match = W3C_TRACEPARENT_REGEX.match(traceparent_raw.strip())
            if match:
                trace_id = match.group(2).lower()

        # Fallback to X-Trace-ID if traceparent was not present or valid
        if not trace_id:
            raw_trace_id = request.headers.get(TRACE_ID_HEADER)
            if raw_trace_id and len(raw_trace_id.strip()) == 32:
                trace_id = raw_trace_id.strip().lower()
            else:
                trace_id = uuid.uuid4().hex

        w3c_traceparent = f"00-{trace_id}-{span_id}-01"

        # 3. Store in request state for access in endpoints & downstream middleware
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        request.state.w3c_traceparent = w3c_traceparent

        # 4. Bind to contextvars for automatic logger context enrichment
        set_request_context(request_id=request_id, trace_id=trace_id)

        try:
            response = await call_next(request)
            # 5. Inject correlation headers into HTTP response
            response.headers[REQUEST_ID_HEADER] = request_id
            response.headers[TRACE_ID_HEADER] = trace_id
            response.headers[W3C_TRACEPARENT_HEADER] = w3c_traceparent
            return response
        finally:
            clear_request_context()
