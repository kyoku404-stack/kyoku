"""Abstract Interfaces and Data Contracts for KEEP RAG & Hybrid Retrieval Engine.

Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/rag
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import UUID


@dataclass
class CitationMetadata:
    """Represents provenanced citation information linked to source documents."""
    document_id: UUID
    filename: str
    page_number: Optional[int] = None
    chunk_index: int = 0
    snippet: str = ""
    relevance_score: float = 0.0
    extra_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """Represents a single retrieved chunk candidate with similarity score."""
    chunk_id: UUID
    document_id: UUID
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGResponse:
    """Represents a complete, citation-backed RAG answer."""
    query: str
    answer: str
    citations: List[CitationMetadata] = field(default_factory=list)
    confidence_score: float = 1.0
    model_name: str = ""
    tokens_used: int = 0


class BaseRetriever(ABC):
    """Abstract interface for dense, sparse, and hybrid retrieval systems."""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        organization_id: UUID,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
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
        candidates: List[RetrievalResult],
        top_n: int = 5,
    ) -> List[RetrievalResult]:
        """Reranks retrieved candidate chunks based on deep relevance scoring.

        Args:
            query: The original user search query.
            candidates: List of initial retrieval candidates from dense/sparse stages.
            top_n: Number of top reranked chunks to return.

        Returns:
            Sorted list of top_n RetrievalResult objects with updated scores.
        """
        pass


class BaseRAGEngine(ABC):
    """Abstract interface for complete end-to-end RAG question-answering workflow."""

    @abstractmethod
    async def generate_answer(
        self,
        query: str,
        organization_id: UUID,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> RAGResponse:
        """Executes full hybrid retrieval, reranking, context assembly, and LLM answer generation.

        Args:
            query: User's question string.
            organization_id: Organization tenant UUID for strict data isolation.
            conversation_history: Optional prior messages in the conversation thread.

        Returns:
            Complete RAGResponse containing synthesized answer and verified citations.
        """
        pass

    @abstractmethod
    async def stream_answer(
        self,
        query: str,
        organization_id: UUID,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncIterator[str]:
        """Streams generated tokens in real-time while capturing citation provenance.

        Args:
            query: User's question string.
            organization_id: Organization tenant UUID.
            conversation_history: Optional prior messages.

        Yields:
            Token chunks as strings.
        """
        pass
