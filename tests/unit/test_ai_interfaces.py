"""Unit tests for Member 1 AI and RAG data contracts and interfaces.

Verifies instantiation, dataclass fields, and contract conformity.
Supports both unittest discovery and pytest.
"""

import unittest
from uuid import uuid4

from backend.app.services.ai.interfaces import (
    LLMGenerationResult,
    LLMMessage,
    MessageRole,
)
from backend.app.services.rag.interfaces import (
    CitationMetadata,
    RAGResponse,
    RetrievalResult,
)


class TestAIInterfaces(unittest.TestCase):
    """Test suite for AI and RAG data contracts."""

    def test_citation_metadata_creation(self):
        doc_id = uuid4()
        citation = CitationMetadata(
            document_id=doc_id,
            filename="test_report.pdf",
            page_number=3,
            chunk_index=1,
            snippet="Relevant sentence from document.",
            relevance_score=0.92,
        )
        self.assertEqual(citation.document_id, doc_id)
        self.assertEqual(citation.filename, "test_report.pdf")
        self.assertEqual(citation.page_number, 3)
        self.assertEqual(citation.relevance_score, 0.92)

    def test_retrieval_result_creation(self):
        chunk_id = uuid4()
        doc_id = uuid4()
        result = RetrievalResult(
            chunk_id=chunk_id,
            document_id=doc_id,
            content="Sample extracted text chunk.",
            score=0.88,
            metadata={"section": "Financials"},
        )
        self.assertEqual(result.chunk_id, chunk_id)
        self.assertEqual(result.document_id, doc_id)
        self.assertEqual(result.score, 0.88)
        self.assertEqual(result.metadata["section"], "Financials")

    def test_rag_response_creation(self):
        doc_id = uuid4()
        citation = CitationMetadata(
            document_id=doc_id,
            filename="annual_plan.pdf",
            page_number=1,
            snippet="Projected growth is 20%",
            relevance_score=0.95,
        )
        response = RAGResponse(
            query="What is the projected growth?",
            answer="The projected growth is 20% [Doc 1, Page 1].",
            citations=[citation],
            confidence_score=0.98,
            model_name="gpt-4o",
            tokens_used=120,
        )
        self.assertEqual(response.query, "What is the projected growth?")
        self.assertEqual(len(response.citations), 1)
        self.assertEqual(response.citations[0].filename, "annual_plan.pdf")
        self.assertEqual(response.confidence_score, 0.98)

    def test_llm_message_and_generation_result(self):
        msg = LLMMessage(
            role=MessageRole.USER,
            content="Summarize quarterly highlights.",
        )
        self.assertEqual(msg.role, MessageRole.USER)
        self.assertEqual(msg.content, "Summarize quarterly highlights.")

        gen_result = LLMGenerationResult(
            content="Here are the highlights...",
            model_name="gpt-4o",
            tokens_prompt=45,
            tokens_completion=80,
        )
        self.assertEqual(gen_result.model_name, "gpt-4o")
        self.assertEqual(gen_result.tokens_prompt, 45)
        self.assertEqual(gen_result.tokens_completion, 80)


if __name__ == "__main__":
    unittest.main()
