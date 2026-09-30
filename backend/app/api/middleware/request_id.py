"""KEEP Enterprise Platform — Request ID Middleware.

Ensures every incoming HTTP request has a unique X-Request-ID for distributed tracing.
"""

import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that injects or propagates X-Request-ID."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check incoming header or generate new UUID
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
