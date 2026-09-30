"""Abstract Interfaces and Data Contracts for KEEP RAG & Hybrid Retrieval Engine.

Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/rag
Specification: devdocs/p1/p1.2.txt (Chapters 10, 11, 12, 19)
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID


class StreamEventType(str, Enum):
    """Event types for SSE streaming responses."""

    TOKEN = "token"
    CITATION = "citation"
    ERROR = "error"
    DONE = "done"


@dataclass
class StreamEvent:
    """Represents a single typed SSE stream event."""

    event: StreamEventType
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class CitationMetadata:
    """Represents provenanced citation information linked to source documents."""

    document_id: UUID
    filename: str
    page_number: int | None = None
    chunk_index: int = 0
    snippet: str = ""
    relevance_score: float = 0.0
    extra_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """Represents a single retrieved chunk candidate with similarity score."""

    chunk_id: UUID
    document_id: UUID
    content: str
    score: float
    filename: str = ""
    page_number: int | None = None
    chunk_index: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchQuery:
    """Structured parameters for hybrid and vector search requests."""

    query: str
    organization_id: UUID
    top_k: int = 10
    dense_weight: float = 0.7
    sparse_weight: float = 0.3
    filters: dict[str, Any] | None = None
    min_score_threshold: float = 0.0


@dataclass
class SearchResultSet:
    """Complete results container for search queries."""

    query: str
    total_results: int
    results: list[RetrievalResult] = field(default_factory=list)
    execution_time_ms: float = 0.0


@dataclass
class ContextBlock:
    """Formatted context chunk ready for prompt assembly."""

    index: int
    chunk_id: UUID
    document_id: UUID
    filename: str
    content: str
    page_number: int | None = None
    score: float = 0.0


@dataclass
class RAGResponse:
    """Represents a complete, citation-backed RAG answer."""

    query: str
    answer: str
    citations: list[CitationMetadata] = field(default_factory=list)
    confidence_score: float = 1.0
    model_name: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0


class BaseRetriever(ABC):
    """Abstract interface for dense, sparse, and hybrid retrieval systems."""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        organization_id: UUID,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Retrieves top-k relevant document chunks scoped to a tenant organization.

        Args:
            query: The user search or question string.
            organization_id: Multi-tenant boundary UUID.
            top_k: Maximum candidate chunks to retrieve.
            filters: Optional metadata filters (e.g. document_id, tags).

        Returns:
            List of scored RetrievalResult candidates.
        """
        pass


class BaseReranker(ABC):
    """Abstract interface for cross-encoder or neural reranking models."""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
        top_n: int = 5,
    ) -> list[RetrievalResult]:
        """Reranks retrieved candidate chunks based on deep relevance scoring.

        Args:
            query: The original user search query.
            candidates: List of initial retrieval candidates from dense/sparse stages.
            top_n: Number of top reranked chunks to return.

        Returns:
            Sorted list of top_n RetrievalResult objects with updated scores.
        """
        pass


class BaseContextBuilder(ABC):
    """Abstract interface for token-budget-aware context assembly."""

    @abstractmethod
    def build_context(
        self,
        candidates: list[RetrievalResult],
        max_context_tokens: int = 4096,
    ) -> list[ContextBlock]:
        """Assembles and truncates context blocks within LLM prompt token budget."""
        pass


class BaseCitationFormatter(ABC):
    """Abstract interface for formatting and linking citations in generated responses."""

    @abstractmethod
    def format_citations(
        self,
        answer: str,
        context_blocks: list[ContextBlock],
    ) -> list[CitationMetadata]:
        """Extracts and formats verified citations mapped to cited sources."""
        pass


class BaseHybridSearchService(ABC):
    """Abstract interface for hybrid (dense vector + sparse BM25) search orchestration."""

    @abstractmethod
    async def search(self, search_query: SearchQuery) -> SearchResultSet:
        """Executes hybrid retrieval, rank fusion, and filtering."""
        pass


class BaseKnowledgeGraphQueryService(ABC):
    """Abstract interface for knowledge graph entity and relation traversal."""

    @abstractmethod
    async def query_entities(
        self,
        query: str,
        organization_id: UUID,
        entity_types: list[str] | None = None,
        max_depth: int = 2,
    ) -> list[dict[str, Any]]:
        """Queries interconnected entities and relationships from graph store."""
        pass


class BaseRAGEngine(ABC):
    """Abstract interface for complete end-to-end RAG question-answering workflow."""

    @abstractmethod
    async def generate_answer(
        self,
        query: str,
        organization_id: UUID,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> RAGResponse:
        """Executes full hybrid retrieval, reranking, context assembly, and LLM answer generation."""
        pass

    @abstractmethod
    async def stream_answer(
        self,
        query: str,
        organization_id: UUID,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """Streams generated tokens and citations in real-time via typed stream events."""
        pass


class BaseRAGService(ABC):
    """High-level service interface for orchestrating RAG operations across the backend."""

    @abstractmethod
    async def answer_question(
        self,
        query: str,
        organization_id: UUID,
        user_id: UUID,
        conversation_id: UUID | None = None,
    ) -> RAGResponse:
        """High-level entry point for Q&A requests."""
        pass

    @abstractmethod
    async def stream_question(
        self,
        query: str,
        organization_id: UUID,
        user_id: UUID,
        conversation_id: UUID | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """High-level entry point for streaming Q&A requests."""
        pass
