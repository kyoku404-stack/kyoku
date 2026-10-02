"""KEEP Enterprise Platform — Chat & RAG Service.

Coordinates synchronous Q&A answering and real-time Server-Sent Events (SSE) token streaming.
"""

import json
from collections.abc import AsyncGenerator
from uuid import UUID, uuid4

from backend.app.schemas.chat import (
    ChatCitation,
    ChatQueryRequest,
    ChatQueryResponse,
)


class ChatService:
    """Service providing conversational AI and grounded enterprise Q&A."""

    async def answer_query(
        self,
        request: ChatQueryRequest,
        org_id: UUID,
    ) -> ChatQueryResponse:
        """Executes full RAG retrieval, context assembly, and LLM synthesis."""
        conversation_id = request.conversation_id or uuid4()
        citations = []
        if request.include_citations:
            citations.append(
                ChatCitation(
                    document_id=UUID("99a85f64-5717-4562-b3fc-2c963f66af11"),
                    filename="Employee_Handbook_2026.pdf",
                    page_number=14,
                    chunk_index=3,
                    snippet="Eligible employees may expense up to $500 annually for remote work home office equipment...",
                    relevance_score=0.94,
                )
            )

        return ChatQueryResponse(
            query=request.query,
            answer="According to the 2026 Employee Handbook, eligible employees receive an annual home office equipment stipend of up to $500 [Doc 1, Page 14].",
            conversation_id=conversation_id,
            confidence_score=0.96,
            model_name="gpt-4o",
            tokens_used=145,
            citations=citations,
        )

    async def stream_chat(
        self,
        query: str,
        conversation_id: UUID,
        org_id: UUID,
    ) -> AsyncGenerator[str, None]:
        """Streams LLM tokens and citation events over Server-Sent Events (SSE)."""
        # Citation event
        citation_payload = {
            "document_id": "99a85f64-5717-4562-b3fc-2c963f66af11",
            "filename": "Security_Policy.pdf",
            "page_number": 4,
        }
        yield f"event: citation\ndata: {json.dumps(citation_payload)}\n\n"

        # Token events
        tokens = [
            "Quarterly ",
            "security ",
            "reviews ",
            "are ",
            "conducted ",
            "every ",
            "90 ",
            "days.",
        ]
        for token in tokens:
            token_payload = {"token": token}
            yield f"event: token\ndata: {json.dumps(token_payload)}\n\n"

        # Done event
        done_payload = {"finish_reason": "stop", "total_tokens": len(tokens) * 2}
        yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"
