"""Unit Tests for Phase 2.2 AI RAG Engine & Semantic Search Contracts.

Owner: Member 1 (Project Lead & AI Architect)
Domain: /tests/unit
Specification: devdocs/p2/p2.2.txt (Chapters 1-20)
Architecture: docs/Architecture/ai-rag-engine.md
ADRs: ADR-035, ADR-036, ADR-037
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.app.services.rag.contracts import (
    DefaultHallucinationGuard,
    DefaultQueryPreprocessor,
    DefaultRAGCitationEngine,
    DefaultRAGContextBuilder,
    DefaultRAGReranker,
    DefaultRRFHybridFuser,
    HybridCandidateChunk,
    HybridSearchConfig,
    QueryIntent,
)


class TestQueryPreprocessor:
    """Tests for query normalization, acronym expansion, and intent detection."""

    def test_query_normalization_and_acronym_expansion(self):
        preprocessor = DefaultQueryPreprocessor()
        raw = "   What is the  WFH and PTO   policy for Q4?   "
        result = preprocessor.preprocess_query(raw)

        assert result.raw_query == raw
        assert "WFH (Work From Home)" in result.normalized_query
        assert "PTO (Paid Time Off)" in result.normalized_query
        assert "wfh" in [k.lower() for k in result.expanded_acronyms]
        assert "pto" in [k.lower() for k in result.expanded_acronyms]

    @pytest.mark.parametrize(
        "query,expected_intent",
        [
            ("What is our leave policy?", QueryIntent.POLICY_VERIFICATION),
            ("Summarize the cybersecurity handbook", QueryIntent.SUMMARY_SYNTHESIS),
            ("Compare plan A versus plan B", QueryIntent.COMPARISON),
            ("Who approves it?", QueryIntent.CONVERSATIONAL_FOLLOWUP),
            ("What is the server IP address?", QueryIntent.FACTUAL_LOOKUP),
        ],
    )
    def test_intent_classification(self, query: str, expected_intent: QueryIntent):
        preprocessor = DefaultQueryPreprocessor()
        ctx = [{"role": "user", "content": "Tell me about leave"}] if expected_intent == QueryIntent.CONVERSATIONAL_FOLLOWUP else None
        result = preprocessor.preprocess_query(query, conversation_context=ctx)
        assert result.intent == expected_intent


class TestRRFHybridFuser:
    """Tests for Reciprocal Rank Fusion (ADR-035)."""

    def test_rrf_fusion_ordering_and_weights(self):
        fuser = DefaultRRFHybridFuser()
        config = HybridSearchConfig(dense_weight=0.65, sparse_weight=0.35, rrf_k=60, top_k=5)

        chunk1 = HybridCandidateChunk(
            chunk_id=uuid4(),
            document_id=uuid4(),
            document_title="Doc A",
            document_version_id=uuid4(),
            page_number=1,
            section_title="Intro",
            content="Alpha content",
            dense_similarity=0.92,
        )
        chunk2 = HybridCandidateChunk(
            chunk_id=uuid4(),
            document_id=uuid4(),
            document_title="Doc B",
            document_version_id=uuid4(),
            page_number=2,
            section_title="Body",
            content="Beta content",
            dense_similarity=0.85,
        )
        chunk3 = HybridCandidateChunk(
            chunk_id=uuid4(),
            document_id=uuid4(),
            document_title="Doc C",
            document_version_id=uuid4(),
            page_number=3,
            section_title="Conclusion",
            content="Gamma content",
            sparse_score=15.4,
        )

        dense_list = [chunk1, chunk2]
        sparse_list = [chunk3, chunk1]  # chunk1 appears in both!

        fused = fuser.fuse(dense_list, sparse_list, config)

        assert len(fused) == 3
        # Chunk 1 appears in both dense (rank 1) and sparse (rank 2), so it must have highest RRF score
        assert fused[0].chunk_id == chunk1.chunk_id
        assert fused[0].dense_rank == 1
        assert fused[0].sparse_rank == 2
        assert fused[0].rrf_score > fused[1].rrf_score

    def test_rrf_fusion_empty_inputs(self):
        fuser = DefaultRRFHybridFuser()
        config = HybridSearchConfig()
        fused = fuser.fuse([], [], config)
        assert fused == []


class TestRAGReranker:
    """Tests for two-tier neural & heuristic reranking (ADR-036)."""

    def test_reranker_scores_and_freshness_decay(self):
        reranker = DefaultRAGReranker(alpha_semantic=0.70, beta_freshness=0.15, gamma_scope=0.15)
        now = datetime.now(UTC)
        dept_id = uuid4()

        recent_chunk = HybridCandidateChunk(
            chunk_id=uuid4(),
            document_id=uuid4(),
            document_title="Recent Policy",
            document_version_id=uuid4(),
            page_number=1,
            section_title="Security",
            content="Employees must use password managers",
            dense_similarity=0.88,
            created_at=now - timedelta(days=2),
            metadata={"department_id": str(dept_id)},
        )
        old_chunk = HybridCandidateChunk(
            chunk_id=uuid4(),
            document_id=uuid4(),
            document_title="Ancient Policy",
            document_version_id=uuid4(),
            page_number=1,
            section_title="Old Security",
            content="Employees must change password monthly",
            dense_similarity=0.88,
            created_at=now - timedelta(days=400),
            metadata={"department_id": str(uuid4())},
        )

        results = reranker.rerank(
            query="password policy",
            candidates=[old_chunk, recent_chunk],
            user_department_id=dept_id,
            top_k=2,
        )

        assert len(results) == 2
        assert results[0].candidate.chunk_id == recent_chunk.chunk_id
        assert results[0].freshness_score > results[1].freshness_score
        assert results[0].scope_score > results[1].scope_score
        assert results[0].final_score > results[1].final_score


class TestContextBuilder:
    """Tests for context assembly, deduplication, and confidence scoring (ADR-037)."""

    def test_context_assembly_and_token_budgeting(self):
        builder = DefaultRAGContextBuilder()
        reranker = DefaultRAGReranker()

        cand1 = HybridCandidateChunk(
            chunk_id=uuid4(),
            document_id=uuid4(),
            document_title="Handbook",
            document_version_id=uuid4(),
            page_number=5,
            section_title="Leave",
            content="Annual leave is 20 days.",
            dense_similarity=0.90,
            metadata={"checksum_sha256": "hash_1"},
        )
        # Duplicate content chunk
        cand2 = HybridCandidateChunk(
            chunk_id=uuid4(),
            document_id=uuid4(),
            document_title="Handbook Copy",
            document_version_id=uuid4(),
            page_number=5,
            section_title="Leave",
            content="Annual leave is 20 days.",
            dense_similarity=0.89,
            metadata={"checksum_sha256": "hash_1"},
        )

        reranked = reranker.rerank("leave days", [cand1, cand2], top_k=2)
        assembled = builder.build_context(reranked, max_tokens=1000)

        # cand2 should be pruned due to duplicate checksum
        assert len(assembled.used_chunks) == 1
        assert "[Source 1: Handbook | Page 5 | Leave" in assembled.formatted_context
        assert assembled.confidence_score > 0.0
        assert assembled.is_sufficient_evidence is True


class TestCitationEngine:
    """Tests for citation extraction and mapping to source documents."""

    def test_extract_citations_from_bracketed_answer(self):
        engine = DefaultRAGCitationEngine()
        builder = DefaultRAGContextBuilder()
        reranker = DefaultRAGReranker()

        cand = HybridCandidateChunk(
            chunk_id=uuid4(),
            document_id=uuid4(),
            document_title="Employee Handbook.pdf",
            document_version_id=uuid4(),
            page_number=18,
            section_title="Section 4.2",
            content="All full-time employees are entitled to 20 days of paid annual leave.",
            dense_similarity=0.95,
        )

        reranked = reranker.rerank("leave policy", [cand], top_k=1)
        assembled = builder.build_context(reranked)

        answer = "Employees receive 20 days of annual leave [Source 1]."
        citations = engine.extract_citations(answer, assembled.used_chunks)

        assert len(citations) == 1
        cit = citations[0]
        assert cit.document_title == "Employee Handbook.pdf"
        assert cit.page_number == 18
        assert cit.section == "Section 4.2"
        assert "20 days" in cit.excerpt


class TestHallucinationGuard:
    """Tests for hallucination prevention and low-confidence circuit breaking."""

    def test_circuit_breaker_triggered_on_low_confidence(self):
        guard = DefaultHallucinationGuard(min_confidence=0.35)
        builder = DefaultRAGContextBuilder()

        # Empty chunks yield 0 confidence
        context = builder.build_context([])
        guard_result = guard.evaluate(context, "Nonexistent topic")

        assert guard_result.circuit_breaker_triggered is True
        assert guard_result.is_grounded is False
        assert "could not find sufficient authoritative information" in guard_result.response_message
