"""Unit tests for Member 1 AI and RAG data contracts and interfaces.

Verifies instantiation, dataclass fields, and contract conformity.
Supports both unittest discovery and pytest.
"""

import unittest
from uuid import uuid4

from backend.app.services.ai.interfaces import (
    AIExecutionContext,
    LLMGenerationResult,
    LLMMessage,
    MessageRole,
    PromptTemplate,
    TokenUsage,
    ToolCallResult,
    ToolDefinition,
)
from backend.app.services.rag.interfaces import (
    CitationMetadata,
    ContextBlock,
    RAGResponse,
    RetrievalResult,
    SearchQuery,
    SearchResultSet,
    StreamEvent,
    StreamEventType,
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
            filename="test.pdf",
            page_number=1,
            metadata={"section": "Financials"},
        )
        self.assertEqual(result.chunk_id, chunk_id)
        self.assertEqual(result.document_id, doc_id)
        self.assertEqual(result.score, 0.88)
        self.assertEqual(result.filename, "test.pdf")
        self.assertEqual(result.metadata["section"], "Financials")

    def test_search_query_and_result_set(self):
        org_id = uuid4()
        chunk_id = uuid4()
        doc_id = uuid4()
        query = SearchQuery(
            query="quarterly revenue",
            organization_id=org_id,
            top_k=5,
            dense_weight=0.6,
            sparse_weight=0.4,
        )
        self.assertEqual(query.query, "quarterly revenue")
        self.assertEqual(query.top_k, 5)
        self.assertEqual(query.dense_weight, 0.6)

        result = RetrievalResult(
            chunk_id=chunk_id,
            document_id=doc_id,
            content="Revenue increased by 15%",
            score=0.91,
        )
        result_set = SearchResultSet(
            query=query.query,
            total_results=1,
            results=[result],
            execution_time_ms=45.2,
        )
        self.assertEqual(result_set.total_results, 1)
        self.assertEqual(len(result_set.results), 1)
        self.assertEqual(result_set.execution_time_ms, 45.2)

    def test_context_block_creation(self):
        chunk_id = uuid4()
        doc_id = uuid4()
        block = ContextBlock(
            index=1,
            chunk_id=chunk_id,
            document_id=doc_id,
            filename="handbook.pdf",
            content="Section 4: Remote Work Policy",
            page_number=12,
            score=0.95,
        )
        self.assertEqual(block.index, 1)
        self.assertEqual(block.filename, "handbook.pdf")
        self.assertEqual(block.page_number, 12)

    def test_stream_event_creation(self):
        event = StreamEvent(
            event=StreamEventType.TOKEN,
            data={"token": "Hello "},
        )
        self.assertEqual(event.event, StreamEventType.TOKEN)
        self.assertEqual(event.data["token"], "Hello ")

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
            latency_ms=310.5,
        )
        self.assertEqual(response.query, "What is the projected growth?")
        self.assertEqual(len(response.citations), 1)
        self.assertEqual(response.citations[0].filename, "annual_plan.pdf")
        self.assertEqual(response.confidence_score, 0.98)
        self.assertEqual(response.latency_ms, 310.5)

    def test_llm_message_and_generation_result(self):
        msg = LLMMessage(
            role=MessageRole.USER,
            content="Summarize quarterly highlights.",
        )
        self.assertEqual(msg.role, MessageRole.USER)
        self.assertEqual(msg.content, "Summarize quarterly highlights.")

        usage = TokenUsage(
            prompt_tokens=45,
            completion_tokens=80,
            total_tokens=125,
            estimated_cost_usd=0.002,
        )
        gen_result = LLMGenerationResult(
            content="Here are the highlights...",
            model_name="gpt-4o",
            tokens_prompt=45,
            tokens_completion=80,
            usage=usage,
        )
        self.assertEqual(gen_result.model_name, "gpt-4o")
        self.assertEqual(gen_result.tokens_prompt, 45)
        self.assertEqual(gen_result.tokens_completion, 80)
        self.assertEqual(gen_result.usage.total_tokens, 125)

    def test_ai_execution_context(self):
        org_id = uuid4()
        user_id = uuid4()
        context = AIExecutionContext(
            organization_id=org_id,
            user_id=user_id,
            session_id="sess_123",
            model_name="gpt-4o",
            temperature=0.0,
            max_tokens=1024,
            enable_cache=True,
        )
        self.assertEqual(context.organization_id, org_id)
        self.assertEqual(context.user_id, user_id)
        self.assertEqual(context.temperature, 0.0)
        self.assertTrue(context.enable_cache)

    def test_prompt_template_and_tools(self):
        template = PromptTemplate(
            name="rag_qa_system",
            version="1.0.0",
            template="Answer the query: {query} based on: {context}",
            system_instruction="You are a helpful enterprise assistant.",
            input_variables=["query", "context"],
        )
        self.assertEqual(template.name, "rag_qa_system")
        self.assertEqual(len(template.input_variables), 2)

        tool = ToolDefinition(
            name="search_documents",
            description="Searches tenant knowledge documents",
            parameters_schema={"type": "object", "properties": {"query": {"type": "string"}}},
        )
        self.assertEqual(tool.name, "search_documents")

        tool_result = ToolCallResult(
            tool_name="search_documents",
            call_id="call_999",
            output={"results_count": 3},
            is_error=False,
        )
        self.assertEqual(tool_result.tool_name, "search_documents")
        self.assertFalse(tool_result.is_error)


if __name__ == "__main__":
    unittest.main()
