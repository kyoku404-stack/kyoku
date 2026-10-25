from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RAGQueryRequest(BaseModel):
    """Request payload for submitting a natural language RAG query."""

    model_config = ConfigDict(from_attributes=True)

    query: str = Field(..., min_length=1, max_length=2000, description="User question in natural language.")
    session_id: UUID | None = Field(default=None, description="Optional conversational session ID for multi-turn context.")
    department_id: UUID | None = Field(default=None, description="Optional department filter for retrieval scoping.")
    project_id: UUID | None = Field(default=None, description="Optional project filter for retrieval scoping.")
    hybrid_dense_weight: float = Field(default=0.65, ge=0.0, le=1.0, description="RRF weight for dense vector search.")
    hybrid_sparse_weight: float = Field(default=0.35, ge=0.0, le=1.0, description="RRF weight for sparse full-text search.")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of top chunks to feed into LLM context.")
    stream: bool = Field(default=False, description="Whether to stream response tokens via SSE.")


class RAGCitationResponse(BaseModel):
    """Citation provenance linked to retrieved source document chunks."""

    model_config = ConfigDict(from_attributes=True)

    citation_id: str
    document_id: UUID
    document_title: str
    document_version_id: UUID | None = None
    page_number: int | None = None
    section: str | None = None
    chunk_id: UUID
    similarity_score: float
    excerpt: str


class RAGRetrievalMetricsResponse(BaseModel):
    """Diagnostic latency and candidate count profiling for RAG execution."""

    model_config = ConfigDict(from_attributes=True)

    dense_candidates: int = 0
    sparse_candidates: int = 0
    reranked_candidates: int = 0
    latency_retrieval_ms: float = 0.0
    latency_generation_ms: float = 0.0
    tokens_prompt: int = 0
    tokens_completion: int = 0


class RAGQueryResponse(BaseModel):
    """Grounded AI answer payload with full citations and diagnostic telemetry."""

    model_config = ConfigDict(from_attributes=True)

    query_id: UUID
    session_id: UUID | None
    query: str
    answer: str
    confidence_score: float
    is_grounded: bool
    processing_time_ms: float
    citations: list[RAGCitationResponse] = []
    retrieval_metrics: RAGRetrievalMetricsResponse


class ChatMessageItem(BaseModel):
    """Item representation of an exchange message in a conversation session."""

    model_config = ConfigDict(from_attributes=True)

    message_id: str
    role: str
    content: str
    citations_json: str | None = None
    created_at: datetime


class ChatSessionItem(BaseModel):
    """Summary and messages list for a conversational session."""

    model_config = ConfigDict(from_attributes=True)

    session_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    messages: list[ChatMessageItem] = []


class RAGHistoryResponse(BaseModel):
    """Paginated conversation history sessions."""

    model_config = ConfigDict(from_attributes=True)

    sessions: list[ChatSessionItem]
    total: int
    page: int
    page_size: int


class RAGCitationDetailResponse(BaseModel):
    """Deep inspection data for a specific citation chunk."""

    model_config = ConfigDict(from_attributes=True)

    citation_id: str
    chunk_id: UUID
    document_id: UUID
    document_title: str
    document_version_id: UUID | None = None
    chunk_index: int = 0
    page_number: int | None = None
    section: str | None = None
    full_content: str
    metadata: dict[str, Any] = {}


class RAGFeedbackRequest(BaseModel):
    """User answer satisfaction feedback submission."""

    model_config = ConfigDict(from_attributes=True)

    query_id: UUID
    rating: int | None = Field(default=None, ge=1, le=5, description="1 to 5 star rating.")
    is_helpful: bool = Field(default=True, description="Binary helpfulness flag.")
    comment: str | None = Field(default=None, max_length=1000, description="Optional feedback comment.")


class RAGFeedbackResponse(BaseModel):
    """Confirmation payload for recorded user feedback."""

    model_config = ConfigDict(from_attributes=True)

    feedback_id: str
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RAGStatisticsResponse(BaseModel):
    """Aggregated organizational RAG engine analytics and KPI metrics."""

    model_config = ConfigDict(from_attributes=True)

    organization_id: UUID
    total_queries: int = 0
    total_sessions: int = 0
    average_latency_ms: float = 0.0
    average_confidence_score: float = 0.0
    hallucination_refusal_count: int = 0
    positive_feedback_percentage: float = 100.0
    total_citations_rendered: int = 0
    cache_hit_ratio: float = 0.0
