"""Unit tests for Phase 2.2 RAG and Hybrid Search Services.

Owner: Member 2 (Backend & Database Lead)
Domain: /tests/unit
Specification: devdocs/p2/p2.2.txt (Chapters 1-20)
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.app.models.document import Document
from backend.app.models.knowledge import DocumentChunk
from backend.app.services.rag.contracts import (
    HybridCandidateChunk,
    HybridSearchConfig,
    RAGQueryRequestPayload,
)
from backend.app.services.rag.hybrid_search_service import HybridSearchService
from backend.app.services.rag.service import RAGService


class TestHybridSearchService:
    """Unit tests for HybridSearchService dense + sparse + RRF search."""

    def test_cosine_similarity_edge_cases(self):
        # Identical vectors
        assert pytest.approx(HybridSearchService._cosine_similarity([1.0, 0.0], [1.0, 0.0])) == 1.0
        # Orthogonal vectors
        assert pytest.approx(HybridSearchService._cosine_similarity([1.0, 0.0], [0.0, 1.0])) == 0.0
        # Empty or mismatched vectors
        assert HybridSearchService._cosine_similarity([], []) == 0.0
        assert HybridSearchService._cosine_similarity([1.0], [1.0, 2.0]) == 0.0

    @pytest.mark.asyncio
    async def test_search_with_mock_db(self):
        service = HybridSearchService()
        org_id = uuid4()
        doc_id = uuid4()

        doc = Document(id=doc_id, organization_id=org_id, title="Test Document")
        chunk1 = DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            chunk_index=0,
            content="Enterprise security standards and policies",
            embedding=[0.1] * 1536,
            metadata_json={"page_number": 1, "section_title": "Security"},
        )

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [(chunk1, doc)]
        mock_db.execute.return_value = mock_result

        results = await service.search(
            db=mock_db,
            query="security policies",
            query_vector=[0.1] * 1536,
            organization_id=org_id,
            config=HybridSearchConfig(),
        )

        assert len(results) == 1
        assert results[0].document_title == "Test Document"
        assert results[0].page_number == 1
        assert results[0].section_title == "Security"
        assert results[0].rrf_score > 0.0


class TestRAGService:
    """Unit tests for end-to-end RAGService coordination."""

    @pytest.mark.asyncio
    async def test_answer_query_grounded_response(self):
        org_id = uuid4()
        user_id = uuid4()
        chunk_id = uuid4()
        doc_id = uuid4()

        mock_hybrid = AsyncMock()
        mock_hybrid.search.return_value = [
            HybridCandidateChunk(
                chunk_id=chunk_id,
                document_id=doc_id,
                document_title="HR Policy.pdf",
                document_version_id=uuid4(),
                page_number=4,
                section_title="Leave",
                content="Employees are granted 20 days paid leave annually.",
                dense_similarity=0.92,
                sparse_score=10.0,
                rrf_score=0.03,
            )
        ]

        service = RAGService(hybrid_search=mock_hybrid)
        mock_db = AsyncMock()

        request = RAGQueryRequestPayload(
            query="What is the leave allowance?",
            organization_id=org_id,
            user_id=user_id,
            top_k=3,
        )

        response = await service.answer_query(mock_db, request)

        assert response.is_grounded is True
        assert response.confidence_score > 0.35
        assert "HR Policy.pdf" in [c.document_title for c in response.citations]
        assert len(response.citations) > 0
        assert response.retrieval_metrics.dense_candidates >= 0
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_answer_query_unsupported_topic_circuit_breaker(self):
        org_id = uuid4()
        user_id = uuid4()

        mock_hybrid = AsyncMock()
        mock_hybrid.search.return_value = []  # No chunks retrieved

        service = RAGService(hybrid_search=mock_hybrid)
        mock_db = AsyncMock()

        request = RAGQueryRequestPayload(
            query="What is the recipe for chocolate cake?",
            organization_id=org_id,
            user_id=user_id,
        )

        response = await service.answer_query(mock_db, request)

        assert response.is_grounded is False
        assert "could not find sufficient authoritative information" in response.answer
        assert len(response.citations) == 0
