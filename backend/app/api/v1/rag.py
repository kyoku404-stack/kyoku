"""KEEP Enterprise Platform — RAG & Semantic Search API Router (Phase 2.2).

Exposes RESTful endpoints for submitting natural language AI queries,
inspecting conversational history, viewing citation details, submitting
feedback, and querying RAG engine performance analytics.
Specification: docs/api/api-contract.md Section 9 & devdocs/p2/p2.2.txt Chapters 1-20
Owner: Member 2 (Backend Lead)
"""

from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
)
from backend.app.api.dependencies.database import get_db
from backend.app.api.dependencies.tenant import TenantContext, get_tenant_context
from backend.app.core.constants import ErrorCode
from backend.app.core.exceptions import NotFoundException
from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.rag import (
    ChatMessageItem,
    ChatSessionItem,
    RAGCitationDetailResponse,
    RAGCitationResponse,
    RAGFeedbackRequest,
    RAGFeedbackResponse,
    RAGHistoryResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGRetrievalMetricsResponse,
    RAGStatisticsResponse,
)
from backend.app.services.rag.contracts import RAGQueryRequestPayload
from backend.app.services.rag.service import RAGService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/rag", tags=["RAG & Semantic Search"])
rag_service = RAGService()


@router.post(
    "/query",
    response_model=ApiResponse[RAGQueryResponse],
    status_code=status.HTTP_200_OK,
    summary="Submit AI question (RAG Query)",
    description="Processes user question through hybrid semantic search, neural reranking, grounding, and citation generation.",
)
async def query_rag(
    request: RAGQueryRequest,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> ApiResponse[RAGQueryResponse]:
    """Executes grounded RAG question answering."""
    payload = RAGQueryRequestPayload(
        query=request.query,
        organization_id=tenant.organization_id,
        user_id=current_user.id,
        session_id=request.session_id,
        department_id=request.department_id,
        project_id=request.project_id,
        hybrid_dense_weight=request.hybrid_dense_weight,
        hybrid_sparse_weight=request.hybrid_sparse_weight,
        top_k=request.top_k,
        stream=request.stream,
    )

    result = await rag_service.answer_query(db, payload)

    citations_resp = [
        RAGCitationResponse(
            citation_id=c.citation_id,
            document_id=c.document_id,
            document_title=c.document_title,
            document_version_id=c.document_version_id,
            page_number=c.page_number,
            section=c.section,
            chunk_id=c.chunk_id,
            similarity_score=c.similarity_score,
            excerpt=c.excerpt,
        )
        for c in result.citations
    ]

    metrics_resp = RAGRetrievalMetricsResponse(
        dense_candidates=result.retrieval_metrics.dense_candidates,
        sparse_candidates=result.retrieval_metrics.sparse_candidates,
        reranked_candidates=result.retrieval_metrics.reranked_candidates,
        latency_retrieval_ms=result.retrieval_metrics.latency_retrieval_ms,
        latency_generation_ms=result.retrieval_metrics.latency_generation_ms,
        tokens_prompt=result.retrieval_metrics.tokens_prompt,
        tokens_completion=result.retrieval_metrics.tokens_completion,
    )

    response_data = RAGQueryResponse(
        query_id=result.query_id,
        session_id=result.session_id,
        query=result.query,
        answer=result.answer,
        confidence_score=result.confidence_score,
        is_grounded=result.is_grounded,
        processing_time_ms=result.processing_time_ms,
        citations=citations_resp,
        retrieval_metrics=metrics_resp,
    )

    return ApiResponse(
        success=True,
        message="Query processed successfully.",
        data=response_data,
    )


@router.get(
    "/history",
    response_model=ApiResponse[RAGHistoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get conversation history",
    description="Retrieves multi-turn conversation sessions and messages for the user.",
)
async def get_history(
    session_id: UUID | None = Query(default=None, description="Optional filter by session ID."),
    page: int = Query(default=1, ge=1, description="Page number."),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page."),
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> ApiResponse[RAGHistoryResponse]:
    """Returns conversation history sessions and messages."""
    sessions_data, total = await rag_service.get_conversation_history(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
        page=page,
        page_size=page_size,
    )

    session_items = [
        ChatSessionItem(
            session_id=s["session_id"],
            title=s["title"],
            created_at=s["created_at"],
            updated_at=s["updated_at"],
            message_count=s["message_count"],
            messages=[
                ChatMessageItem(
                    message_id=m["message_id"],
                    role=m["role"],
                    content=m["content"],
                    citations_json=m["citations_json"],
                    created_at=m["created_at"],
                )
                for m in s["messages"]
            ],
        )
        for s in sessions_data
    ]

    return ApiResponse(
        success=True,
        message="Conversation history retrieved successfully.",
        data=RAGHistoryResponse(
            sessions=session_items,
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.get(
    "/citations/{citation_id}",
    response_model=ApiResponse[RAGCitationDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve citation details",
    description="Inspects source document content and metadata for a specific citation chunk ID.",
)
async def get_citation_detail(
    citation_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> ApiResponse[RAGCitationDetailResponse]:
    """Retrieves deep citation details for a given chunk ID."""
    detail = await rag_service.get_citation_detail(
        db=db,
        chunk_id=citation_id,
        organization_id=tenant.organization_id,
    )
    if not detail:
        raise NotFoundException(
            message=f"Citation chunk with ID '{citation_id}' was not found.",
            code=ErrorCode.NOT_FOUND,
        )

    return ApiResponse(
        success=True,
        message="Citation details retrieved successfully.",
        data=RAGCitationDetailResponse(**detail),
    )


@router.post(
    "/feedback",
    response_model=ApiResponse[RAGFeedbackResponse],
    status_code=status.HTTP_200_OK,
    summary="Submit user feedback",
    description="Records user evaluation, rating, and satisfaction comments for a RAG answer.",
)
async def submit_feedback(
    request: RAGFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> ApiResponse[RAGFeedbackResponse]:
    """Records user satisfaction feedback on generated RAG answers."""
    feedback_id = await rag_service.record_feedback(
        db=db,
        query_id=request.query_id,
        user_id=current_user.id,
        organization_id=tenant.organization_id,
        rating=request.rating,
        is_helpful=request.is_helpful,
        comment=request.comment,
    )

    return ApiResponse(
        success=True,
        message="Feedback submitted successfully.",
        data=RAGFeedbackResponse(feedback_id=str(feedback_id)),
    )


@router.get(
    "/statistics",
    response_model=ApiResponse[RAGStatisticsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get RAG analytics",
    description="Aggregates organizational RAG queries, mean latency, confidence, and feedback ratings.",
)
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> ApiResponse[RAGStatisticsResponse]:
    """Returns organizational RAG engine telemetry."""
    stats = await rag_service.get_statistics(db, tenant.organization_id)

    return ApiResponse(
        success=True,
        message="RAG analytics retrieved successfully.",
        data=RAGStatisticsResponse(
            organization_id=stats.organization_id,
            total_queries=stats.total_queries,
            total_sessions=stats.total_sessions,
            average_latency_ms=stats.average_latency_ms,
            average_confidence_score=stats.average_confidence_score,
            hallucination_refusal_count=stats.hallucination_refusal_count,
            positive_feedback_percentage=stats.positive_feedback_percentage,
            total_citations_rendered=stats.total_citations_rendered,
            cache_hit_ratio=stats.cache_hit_ratio,
        ),
    )
