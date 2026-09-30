"""KEEP Enterprise Platform — Chat & RAG Schemas."""

from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ChatCitation(BaseModel):
    """Citation reference back to ingested enterprise document."""

    document_id: UUID = Field(..., description="Referenced document ID")
    filename: str = Field(..., description="Source document filename")
    page_number: int | None = Field(default=None, description="Page number of citation")
    chunk_index: int | None = Field(default=None, description="Index of referenced chunk")
    snippet: str = Field(..., description="Extracted contextual snippet")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")


class ChatQueryRequest(BaseModel):
    """Payload for synchronous RAG question answering."""

    query: str = Field(..., min_length=1, max_length=2000, description="User question or prompt")
    conversation_id: UUID | None = Field(default=None, description="Existing conversation session ID")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of context chunks to retrieve")
    include_citations: bool = Field(default=True, description="Whether to include source citations")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What is the annual home office stipend?",
                "conversation_id": "55a85f64-5717-4562-b3fc-2c963f66af55",
                "top_k": 5,
                "include_citations": True,
            }
        }
    )


class ChatQueryResponse(BaseModel):
    """Payload returned by synchronous RAG question answering."""

    query: str = Field(..., description="Original user prompt")
    answer: str = Field(..., description="Generated answer with attribution")
    conversation_id: UUID = Field(..., description="Conversation identifier")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence rating")
    model_name: str = Field(default="gpt-4o", description="Underlying model identifier")
    tokens_used: int = Field(default=0, description="Total tokens consumed")
    citations: list[ChatCitation] = Field(default_factory=list, description="Grounding source citations")


class ChatStreamRequest(BaseModel):
    """Payload for SSE streaming RAG query."""

    query: str = Field(..., min_length=1, max_length=2000, description="User question or prompt")
    conversation_id: UUID | None = Field(default=None, description="Conversation session ID")
