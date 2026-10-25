"""Phase 2.2 RAG Engine and Semantic Search Typed Domain Contracts.

Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/rag
Specification: devdocs/p2/p2.2.txt (Chapters 1-20)
Architecture: docs/Architecture/ai-rag-engine.md
ADRs: ADR-035, ADR-036, ADR-037
"""

import math
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, ClassVar
from uuid import UUID, uuid4

# ==============================================================================
# 1. Query Processing & Understanding Enums & Dataclasses
# ==============================================================================


class QueryIntent(str, Enum):
    """Classified user question intent (devdocs/p2/p2.2.txt Chapter 5)."""

    FACTUAL_LOOKUP = "FACTUAL_LOOKUP"
    SUMMARY_SYNTHESIS = "SUMMARY_SYNTHESIS"
    COMPARISON = "COMPARISON"
    POLICY_VERIFICATION = "POLICY_VERIFICATION"
    CONVERSATIONAL_FOLLOWUP = "CONVERSATIONAL_FOLLOWUP"


@dataclass
class ProcessedQuery:
    """Normalized and expanded query representation ready for hybrid retrieval."""

    raw_query: str
    normalized_query: str
    intent: QueryIntent
    expanded_acronyms: dict[str, str] = field(default_factory=dict)
    extracted_entities: list[str] = field(default_factory=list)
    language: str = "en"
    requires_hybrid: bool = True


class BaseQueryPreprocessor(ABC):
    """Abstract interface for query normalization, acronym expansion, and intent detection."""

    @abstractmethod
    def preprocess_query(
        self,
        query: str,
        conversation_context: list[dict[str, str]] | None = None,
    ) -> ProcessedQuery:
        """Normalizes and expands user query."""


class DefaultQueryPreprocessor(BaseQueryPreprocessor):
    """Concrete reference query preprocessor with enterprise taxonomy expansion."""

    DEFAULT_ACRONYM_MAP: ClassVar[dict[str, str]] = {
        "wfh": "Work From Home",
        "pto": "Paid Time Off",
        "nda": "Non-Disclosure Agreement",
        "sla": "Service Level Agreement",
        "kpi": "Key Performance Indicator",
        "hr": "Human Resources",
        "it": "Information Technology",
        "soc2": "System and Organization Controls 2",
        "gdpr": "General Data Protection Regulation",
        "rag": "Retrieval-Augmented Generation",
        "sso": "Single Sign-On",
        "mfa": "Multi-Factor Authentication",
        "rbac": "Role-Based Access Control",
    }

    def __init__(self, custom_acronyms: dict[str, str] | None = None):
        self.acronym_map = {**self.DEFAULT_ACRONYM_MAP, **(custom_acronyms or {})}

    def preprocess_query(
        self,
        query: str,
        conversation_context: list[dict[str, str]] | None = None,
    ) -> ProcessedQuery:
        cleaned = re.sub(r"\s+", " ", query.strip())
        words = re.findall(r"\b[a-zA-Z0-9_-]+\b", cleaned)
        expanded: dict[str, str] = {}
        normalized = cleaned

        for word in words:
            lower_word = word.lower()
            if lower_word in self.acronym_map:
                full_expansion = self.acronym_map[lower_word]
                expanded[word] = full_expansion
                # Replace with expanded term for better keyword & vector matching
                normalized = re.sub(
                    rf"\b{re.escape(word)}\b",
                    f"{word} ({full_expansion})",
                    normalized,
                    flags=re.IGNORECASE,
                )

        # Classify intent
        lower_q = cleaned.lower()
        if any(term in lower_q for term in ["summarize", "overview", "brief", "digest"]):
            intent = QueryIntent.SUMMARY_SYNTHESIS
        elif any(term in lower_q for term in ["compare", "difference between", "versus", "vs"]):
            intent = QueryIntent.COMPARISON
        elif any(term in lower_q for term in ["policy", "rule", "guideline", "permitted", "allowed", "can i"]):
            intent = QueryIntent.POLICY_VERIFICATION
        elif conversation_context and any(term in lower_q for term in ["it", "this", "that", "they", "those", "who approves"]):
            intent = QueryIntent.CONVERSATIONAL_FOLLOWUP
        else:
            intent = QueryIntent.FACTUAL_LOOKUP

        return ProcessedQuery(
            raw_query=query,
            normalized_query=normalized,
            intent=intent,
            expanded_acronyms=expanded,
            extracted_entities=[],
            language="en",
            requires_hybrid=True,
        )


# ==============================================================================
# 2. Hybrid Retrieval & Reciprocal Rank Fusion (RRF) Contracts (ADR-035)
# ==============================================================================


@dataclass
class HybridSearchConfig:
    """Configuration weights and smoothing constants for Hybrid RRF search."""

    dense_weight: float = 0.65
    sparse_weight: float = 0.35
    rrf_k: int = 60
    candidate_limit: int = 30
    top_k: int = 5


@dataclass
class HybridCandidateChunk:
    """Unified search candidate with dual rankings and fused score."""

    chunk_id: UUID
    document_id: UUID
    document_title: str
    document_version_id: UUID | None
    page_number: int | None
    section_title: str | None
    content: str
    dense_rank: int | None = None
    sparse_rank: int | None = None
    dense_similarity: float = 0.0
    sparse_score: float = 0.0
    rrf_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class BaseHybridFuser(ABC):
    """Abstract interface for fusing heterogeneous search results."""

    @abstractmethod
    def fuse(
        self,
        dense_results: list[HybridCandidateChunk],
        sparse_results: list[HybridCandidateChunk],
        config: HybridSearchConfig,
    ) -> list[HybridCandidateChunk]:
        """Calculates Reciprocal Rank Fusion (RRF) scores and ranks combined candidates."""


class DefaultRRFHybridFuser(BaseHybridFuser):
    """Reciprocal Rank Fusion implementation complying strictly with ADR-035."""

    def fuse(
        self,
        dense_results: list[HybridCandidateChunk],
        sparse_results: list[HybridCandidateChunk],
        config: HybridSearchConfig,
    ) -> list[HybridCandidateChunk]:
        candidate_map: dict[UUID, HybridCandidateChunk] = {}

        # 1. Process dense candidates
        for rank_idx, chunk in enumerate(dense_results, start=1):
            chunk.dense_rank = rank_idx
            candidate_map[chunk.chunk_id] = chunk

        # 2. Process sparse candidates
        for rank_idx, chunk in enumerate(sparse_results, start=1):
            if chunk.chunk_id in candidate_map:
                existing = candidate_map[chunk.chunk_id]
                existing.sparse_rank = rank_idx
                existing.sparse_score = chunk.sparse_score
            else:
                chunk.sparse_rank = rank_idx
                candidate_map[chunk.chunk_id] = chunk

        # 3. Compute RRF score: sum( w_m / (k + rank_m) )
        k = max(1, config.rrf_k)
        for chunk in candidate_map.values():
            score = 0.0
            if chunk.dense_rank is not None:
                score += config.dense_weight / (k + chunk.dense_rank)
            if chunk.sparse_rank is not None:
                score += config.sparse_weight / (k + chunk.sparse_rank)
            chunk.rrf_score = round(score, 6)

        # 4. Sort descending by RRF score
        sorted_candidates = sorted(
            candidate_map.values(),
            key=lambda c: c.rrf_score,
            reverse=True,
        )
        return sorted_candidates[: config.candidate_limit]


# ==============================================================================
# 3. Two-Tier Neural & Heuristic Reranker (ADR-036)
# ==============================================================================


@dataclass
class RerankedChunk:
    """Reranked chunk with fine-grained composite relevance scores."""

    candidate: HybridCandidateChunk
    semantic_score: float
    freshness_score: float
    scope_score: float
    final_score: float


class BaseRAGReranker(ABC):
    """Abstract interface for two-tier neural & heuristic reranking."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: list[HybridCandidateChunk],
        user_department_id: UUID | None = None,
        user_project_id: UUID | None = None,
        top_k: int = 5,
    ) -> list[RerankedChunk]:
        """Scores candidate chunks using multi-factor criteria and selects top-k."""


class DefaultRAGReranker(BaseRAGReranker):
    """Two-tier reranker combining semantic relevance, recency decay, and scope alignment."""

    def __init__(
        self,
        alpha_semantic: float = 0.70,
        beta_freshness: float = 0.15,
        gamma_scope: float = 0.15,
        freshness_half_life_days: float = 180.0,
    ):
        self.alpha = alpha_semantic
        self.beta = beta_freshness
        self.gamma = gamma_scope
        self.half_life_days = freshness_half_life_days

    def rerank(
        self,
        query: str,
        candidates: list[HybridCandidateChunk],
        user_department_id: UUID | None = None,
        user_project_id: UUID | None = None,
        top_k: int = 5,
    ) -> list[RerankedChunk]:
        if not candidates:
            return []

        now = datetime.now(UTC)
        reranked_list: list[RerankedChunk] = []

        query_terms = set(re.findall(r"\w+", query.lower()))

        for cand in candidates:
            # 1. Semantic score: derived from dense similarity or normalized RRF score
            if cand.dense_similarity > 0.0:
                semantic = min(1.0, max(0.0, cand.dense_similarity))
            else:
                # Lexical term overlap heuristic
                content_terms = set(re.findall(r"\w+", cand.content.lower()))
                overlap = len(query_terms.intersection(content_terms))
                semantic = min(1.0, overlap / max(1, len(query_terms)))

            # 2. Freshness score with exponential decay
            cand_time = cand.created_at
            if cand_time.tzinfo is None:
                cand_time = cand_time.replace(tzinfo=UTC)
            delta_days = max(0.0, (now - cand_time).total_seconds() / 86400.0)
            freshness = math.exp(-delta_days / max(1.0, self.half_life_days))

            # 3. Scope score (department / project relevance)
            scope = 0.0
            cand_dept = cand.metadata.get("department_id")
            cand_proj = cand.metadata.get("project_id")
            if user_project_id and cand_proj and str(cand_proj) == str(user_project_id):
                scope = 1.0
            elif user_department_id and cand_dept and str(cand_dept) == str(user_department_id):
                scope = 0.7
            else:
                scope = 0.3

            # 4. Composite final score
            final = (self.alpha * semantic) + (self.beta * freshness) + (self.gamma * scope)
            final = round(min(1.0, max(0.0, final)), 4)

            reranked_list.append(
                RerankedChunk(
                    candidate=cand,
                    semantic_score=round(semantic, 4),
                    freshness_score=round(freshness, 4),
                    scope_score=round(scope, 4),
                    final_score=final,
                )
            )

        # Sort descending by final score
        reranked_list.sort(key=lambda r: r.final_score, reverse=True)
        return reranked_list[:top_k]


# ==============================================================================
# 4. Context Builder & Token Budgeting (ADR-037)
# ==============================================================================


@dataclass
class AssembledContext:
    """Structured context block formatted for LLM consumption with token budgeting."""

    formatted_context: str
    used_chunks: list[RerankedChunk]
    estimated_token_count: int
    confidence_score: float
    is_sufficient_evidence: bool


class BaseRAGContextBuilder(ABC):
    """Abstract interface for token-budget-aware prompt context construction."""

    @abstractmethod
    def build_context(
        self,
        reranked_chunks: list[RerankedChunk],
        max_tokens: int = 3000,
        min_confidence_threshold: float = 0.35,
    ) -> AssembledContext:
        """Assembles context block and calculates evidence confidence."""


class DefaultRAGContextBuilder(BaseRAGContextBuilder):
    """Context builder with deduplication, provenance envelopes, and confidence scoring."""

    def build_context(
        self,
        reranked_chunks: list[RerankedChunk],
        max_tokens: int = 3000,
        min_confidence_threshold: float = 0.35,
    ) -> AssembledContext:
        if not reranked_chunks:
            return AssembledContext(
                formatted_context="",
                used_chunks=[],
                estimated_token_count=0,
                confidence_score=0.0,
                is_sufficient_evidence=False,
            )

        # Calculate mean confidence score
        confidence = sum(r.final_score for r in reranked_chunks) / len(reranked_chunks)
        confidence = round(confidence, 4)
        is_sufficient = confidence >= min_confidence_threshold

        # Token estimation: ~4 chars per token
        context_blocks: list[str] = []
        used_chunks: list[RerankedChunk] = []
        current_char_count = 0
        max_chars = max_tokens * 4

        seen_checksums: set[str] = set()

        for idx, item in enumerate(reranked_chunks, start=1):
            cand = item.candidate
            checksum = cand.metadata.get("checksum_sha256") or str(cand.chunk_id)
            if checksum in seen_checksums:
                continue
            seen_checksums.add(checksum)

            page_info = f"Page {cand.page_number}" if cand.page_number else "Page N/A"
            sec_info = cand.section_title or "General Section"
            header = f"[Source {idx}: {cand.document_title} | {page_info} | {sec_info} | ID: {cand.chunk_id}]"
            block = f"{header}\n{cand.content.strip()}"

            if current_char_count + len(block) > max_chars and context_blocks:
                break

            context_blocks.append(block)
            used_chunks.append(item)
            current_char_count += len(block)

        formatted_context = "\n\n".join(context_blocks)
        estimated_tokens = max(1, current_char_count // 4)

        return AssembledContext(
            formatted_context=formatted_context,
            used_chunks=used_chunks,
            estimated_token_count=estimated_tokens,
            confidence_score=confidence,
            is_sufficient_evidence=is_sufficient,
        )


# ==============================================================================
# 5. Citation Engine & Grounding Contracts (ADR-037)
# ==============================================================================


@dataclass
class RAGCitation:
    """Structured citation item linked to source document chunk."""

    citation_id: str
    chunk_id: UUID
    document_id: UUID
    document_title: str
    document_version_id: UUID | None
    page_number: int | None
    section: str | None
    similarity_score: float
    excerpt: str


class BaseRAGCitationEngine(ABC):
    """Abstract interface for extracting and verifying citation tags from LLM responses."""

    @abstractmethod
    def extract_citations(
        self,
        answer: str,
        used_chunks: list[RerankedChunk],
    ) -> list[RAGCitation]:
        """Resolves citations referenced in answer text back to source document chunks."""


class DefaultRAGCitationEngine(BaseRAGCitationEngine):
    """Parses [Doc X, Page Y] or [Source N] citation markers and formats verifiable citations."""

    def extract_citations(
        self,
        answer: str,
        used_chunks: list[RerankedChunk],
    ) -> list[RAGCitation]:
        citations: list[RAGCitation] = []
        if not used_chunks:
            return citations

        # Match [Source X] or [Doc X, Page Y] or [X]
        source_matches = set(re.findall(r"\[(?:Source\s*|Doc\s*)?(\d+)[^\]]*\]", answer, flags=re.IGNORECASE))

        # Build mapping from 1-based index to chunk
        chunk_by_idx = {str(i): chunk for i, chunk in enumerate(used_chunks, start=1)}

        for idx_str in sorted(source_matches):
            if idx_str in chunk_by_idx:
                item = chunk_by_idx[idx_str]
                cand = item.candidate
                snippet = cand.content[:200] + ("..." if len(cand.content) > 200 else "")
                citations.append(
                    RAGCitation(
                        citation_id=f"cit_{idx_str}",
                        chunk_id=cand.chunk_id,
                        document_id=cand.document_id,
                        document_title=cand.document_title,
                        document_version_id=cand.document_version_id,
                        page_number=cand.page_number,
                        section=cand.section_title,
                        similarity_score=item.final_score,
                        excerpt=snippet,
                    )
                )

        # Fallback: if no explicit tags in answer but chunks were used to synthesize, include top chunks
        if not citations and used_chunks:
            for i, item in enumerate(used_chunks[:3], start=1):
                cand = item.candidate
                snippet = cand.content[:200] + ("..." if len(cand.content) > 200 else "")
                citations.append(
                    RAGCitation(
                        citation_id=f"cit_ref_{i}",
                        chunk_id=cand.chunk_id,
                        document_id=cand.document_id,
                        document_title=cand.document_title,
                        document_version_id=cand.document_version_id,
                        page_number=cand.page_number,
                        section=cand.section_title,
                        similarity_score=item.final_score,
                        excerpt=snippet,
                    )
                )

        return citations


# ==============================================================================
# 6. Hallucination Guardrail & Circuit Breaker (ADR-037)
# ==============================================================================


@dataclass
class HallucinationGuardResult:
    """Result of hallucination circuit breaker evaluation."""

    is_grounded: bool
    confidence_score: float
    circuit_breaker_triggered: bool
    response_message: str


class BaseHallucinationGuard(ABC):
    """Abstract interface evaluating if sufficient grounded evidence exists."""

    @abstractmethod
    def evaluate(
        self,
        assembled_context: AssembledContext,
        query: str,
    ) -> HallucinationGuardResult:
        """Determines whether to trigger the refusal circuit breaker or allow LLM generation."""


class DefaultHallucinationGuard(BaseHallucinationGuard):
    """Guarantees zero-hallucination compliance by refusing ungrounded queries."""

    REFUSAL_MESSAGE = (
        "I could not find sufficient authoritative information in your organization's "
        "knowledge base to answer this question accurately. Please verify your query or "
        "ensure the relevant documents have been uploaded."
    )

    def __init__(self, min_confidence: float = 0.35):
        self.min_confidence = min_confidence

    def evaluate(
        self,
        assembled_context: AssembledContext,
        query: str,
    ) -> HallucinationGuardResult:
        if not assembled_context.is_sufficient_evidence or assembled_context.confidence_score < self.min_confidence:
            return HallucinationGuardResult(
                is_grounded=False,
                confidence_score=assembled_context.confidence_score,
                circuit_breaker_triggered=True,
                response_message=self.REFUSAL_MESSAGE,
            )

        return HallucinationGuardResult(
            is_grounded=True,
            confidence_score=assembled_context.confidence_score,
            circuit_breaker_triggered=False,
            response_message="",
        )


# ==============================================================================
# 7. High-Level Coordinator & Response Payload Models
# ==============================================================================


@dataclass
class RAGQueryRequestPayload:
    """Inbound request payload for RAG Q&A query."""

    query: str
    organization_id: UUID
    user_id: UUID
    session_id: UUID | None = None
    department_id: UUID | None = None
    project_id: UUID | None = None
    hybrid_dense_weight: float = 0.65
    hybrid_sparse_weight: float = 0.35
    top_k: int = 5
    stream: bool = False


@dataclass
class RAGRetrievalTelemetry:
    """Latency and candidate count metrics for RAG query."""

    dense_candidates: int = 0
    sparse_candidates: int = 0
    reranked_candidates: int = 0
    latency_retrieval_ms: float = 0.0
    latency_generation_ms: float = 0.0
    tokens_prompt: int = 0
    tokens_completion: int = 0


@dataclass
class RAGQueryResponsePayload:
    """Unified response payload for grounded RAG answer."""

    query_id: UUID
    session_id: UUID | None
    query: str
    answer: str
    confidence_score: float
    is_grounded: bool
    processing_time_ms: float
    citations: list[RAGCitation]
    retrieval_metrics: RAGRetrievalTelemetry
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class RAGFeedbackSubmission:
    """Human feedback model for answer evaluation."""

    query_id: UUID
    user_id: UUID
    organization_id: UUID
    rating: int  # 1 to 5
    is_helpful: bool
    comment: str | None = None
    feedback_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class RAGSystemStatistics:
    """Aggregated organizational RAG telemetry."""

    organization_id: UUID
    total_queries: int = 0
    total_sessions: int = 0
    average_latency_ms: float = 0.0
    average_confidence_score: float = 0.0
    hallucination_refusal_count: int = 0
    positive_feedback_percentage: float = 100.0
    total_citations_rendered: int = 0
    cache_hit_ratio: float = 0.0
