"""Security Headers Middleware for Production Hardening.

Owner: Member 2 (Backend Lead)
Domain: /backend/app/api/middleware/security_headers.py
Specification: devdocs/p1/p1.10.txt (Chapters 8, 11) & ADR-029
Phase: 1.10 — Deployment, Infrastructure & Production Readiness
"""

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces enterprise security headers on all HTTP responses.

    Acts as defense-in-depth behind reverse proxy (Nginx).
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)

        # Baseline security headers
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), camera=(), microphone=()"
        )

        # HSTS in production or staging
        if settings.is_production or settings.is_staging:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=63072000; includeSubDomains; preload",
            )

        return response
