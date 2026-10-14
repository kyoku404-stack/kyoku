"""KEEP Enterprise Platform — AI Assistant Query Endpoints (`/api/v1/ai`).

Serves streaming AI assistant queries over Server-Sent Events (SSE) with token rate limiting.
Derived from devdocs/p1/p1.7.txt and docs/API/api-contract.md Section 5.7.
"""

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
)
from backend.app.schemas.dashboard import AIQueryRequest
from backend.app.services.ai_query_service import AIQueryService
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/ai", tags=["AI Assistant"])
ai_query_service = AIQueryService()


@router.post(
    "/query",
    status_code=status.HTTP_200_OK,
    summary="Submit AI assistant query (SSE stream)",
    description="Submits an organizational question to the AI assistant and streams back responses via Server-Sent Events. Rate limited to 60 req/hr per user.",
)
async def query_ai(
    request: AIQueryRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> StreamingResponse:
    """Streams token events and document sources over SSE."""
    generator = ai_query_service.execute_query_stream(
        request=request,
        current_user=current_user,
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
