"""KEEP Enterprise Platform — AI Query Assistant Service.

Coordinates AI assistant queries, request sanitization, token-bucket rate limiting,
and Server-Sent Events (SSE) stub streaming for Phase 1.7.
Derived from devdocs/p1/p1.7.txt and docs/Architecture/dashboard-architecture.md Section 5.
"""

import json
import re
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.core.cache import cache
from backend.app.core.constants import ErrorCode
from backend.app.core.exceptions import (
    RateLimitExceededException,
    ValidationException,
)
from backend.app.schemas.dashboard import AIQueryRequest


class AIQueryService:
    """Service handling lightweight AI assistant interactions and stub SSE streaming."""

    @staticmethod
    def sanitize_query(query: str) -> str:
        """Strips non-printable control characters from input string."""
        if not query:
            return ""
        # Remove ASCII control characters except newline and tab
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", query)
        return sanitized.strip()

    async def execute_query_stream(
        self,
        request: AIQueryRequest,
        current_user: AuthenticatedUser,
    ) -> AsyncGenerator[str, None]:
        """Validates query, enforces rate limiting, and streams SSE tokens."""
        # 1. Validation & Sanitization
        sanitized_query = self.sanitize_query(request.query)
        if len(sanitized_query) > 4096:
            raise ValidationException(
                message="AI query exceeds maximum allowed length of 4096 characters.",
                code=ErrorCode.AI_QUERY_TOO_LONG,
                details={"max_length": 4096, "current_length": len(sanitized_query)},
            )

        if not sanitized_query:
            raise ValidationException(
                message="Query cannot be empty or contain only control characters.",
                code=ErrorCode.VALIDATION_ERROR,
            )

        # 2. Rate Limiting (60 requests/hour per user)
        rate_key = f"ai_query:{current_user.id}"
        is_allowed, remaining = await cache.check_rate_limit(
            rate_key, limit=60, window_seconds=3600
        )
        if not is_allowed:
            raise RateLimitExceededException(
                message="Rate limit of 60 AI queries per hour exceeded.",
                code=ErrorCode.AI_RATE_LIMIT_EXCEEDED,
                details={"limit": 60, "remaining": 0, "window": "1h"},
            )

        # 3. Increment daily org counter for dashboard KPI
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        counter_key = f"ai_queries_today:{current_user.organization_id}:{today_str}"
        await cache.incr(counter_key, ttl=86400)

        query_id = uuid4()

        # 4. Stream response tokens (Phase 1.7 Stub contract)
        tokens = [
            "Here is a summary of this week's ",
            "organizational activity: ",
            "[stub response — ",
            "AI engine activates in Phase 2.2].",
        ]

        for token in tokens:
            token_payload = {"token": token}
            yield f"event: token\ndata: {json.dumps(token_payload)}\n\n"

        # Done event with sources list and query ID
        sources: list[dict[str, Any]] = []
        done_payload: dict[str, Any] = {
            "sources": sources,
            "query_id": str(query_id),
        }
        yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"
