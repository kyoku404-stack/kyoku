"""KEEP Enterprise Platform — Chat & RAG Endpoints (`/api/v1/chat`)."""

from uuid import uuid4

from backend.app.api.dependencies.auth import AuthenticatedUser, get_current_user
from backend.app.api.dependencies.tenant import TenantContext, get_tenant_context
from backend.app.schemas.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    ChatStreamRequest,
)
from backend.app.schemas.envelope import ApiResponse
from backend.app.services.chat_service import ChatService
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/chat", tags=["Chat"])
chat_service = ChatService()


@router.post(
    "/query",
    response_model=ApiResponse[ChatQueryResponse],
    status_code=status.HTTP_200_OK,
    summary="Synchronous RAG Q&A query",
    description="Processes question answering with retrieved enterprise context and source citations.",
)
async def chat_query(
    request: ChatQueryRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ApiResponse[ChatQueryResponse]:
    """Generates grounded answer with source citations."""
    response = await chat_service.answer_query(
        request=request,
        org_id=tenant.organization_id,
    )
    return ApiResponse(
        success=True,
        message="Answer generated successfully.",
        data=response,
    )


@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
    summary="Streaming RAG token stream (SSE)",
    description="Streams real-time token events and citations via Server-Sent Events (SSE).",
)
async def chat_stream(
    request: ChatStreamRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StreamingResponse:
    """Streams token events over Server-Sent Events."""
    conversation_id = request.conversation_id or uuid4()
    generator = chat_service.stream_chat(
        query=request.query,
        conversation_id=conversation_id,
        org_id=tenant.organization_id,
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
