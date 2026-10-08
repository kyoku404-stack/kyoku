"""Abstract Interfaces and Data Contracts for KEEP RAG, Vector & Persistence Layer.

Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/rag
Specification: devdocs/p1/p1.2.txt (Chapters 10, 11, 12, 19) & devdocs/p1/p1.3.txt (Chapters 6, 7, 14, 19)
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
class RAGSecurityContext:
    """Multi-tenant security context applied to RAG retrieval and citation filtering."""

    user_id: UUID
    organization_id: UUID
    role: str = "Member"
    allowed_document_ids: set[UUID] | None = None
    accessible_project_ids: set[UUID] | None = None

    def can_access_document(self, document_id: UUID) -> bool:
        """Verifies if the user is authorized to read chunks from the document."""
        if self.allowed_document_ids is None:
            return True
        return document_id in self.allowed_document_ids

    def is_in_tenant(self, tenant_id: UUID) -> bool:
        """Enforces hard organizational tenant boundary."""
        return self.organization_id == tenant_id


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
    allowed_document_ids: list[UUID] | None = None
    security_context: RAGSecurityContext | None = None


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


# ---------------------------------------------------------------------------
# Persistence & Vector / Chunk / Graph Data Contracts (Phase 1.3 Baseline)
# ---------------------------------------------------------------------------


@dataclass
class VectorRecord:
    """Represents a vector embedding entry for vector stores (pgvector / Qdrant)."""

    id: UUID
    vector: list[float]
    payload: dict[str, Any]
    organization_id: UUID
    document_id: UUID | None = None


@dataclass
class VectorFilter:
    """Multi-tenant filter criteria for vector similarity search."""

    organization_id: UUID
    document_id: UUID | None = None
    allowed_document_ids: list[UUID] | None = None
    user_role: str | None = None
    metadata_filters: dict[str, Any] | None = None


@dataclass
class DocumentChunkRecord:
    """Represents a persistent document chunk record."""

    id: UUID
    organization_id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    token_count: int = 0
    page_number: int | None = None
    section_title: str | None = None
    embedding: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class KGEntityRecord:
    """Represents a persistent Knowledge Graph entity (node)."""

    id: UUID
    organization_id: UUID
    name: str
    entity_type: str
    description: str | None = None
    source_document_id: UUID | None = None
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class KGRelationshipRecord:
    """Represents a persistent Knowledge Graph relationship (directed edge)."""

    id: UUID
    organization_id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    relation_type: str
    weight: float = 1.0
    confidence_score: float = 1.0
    source_document_id: UUID | None = None
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatMessageRecord:
    """Represents a persistent chat message with metadata and citations."""

    id: UUID
    session_id: UUID
    role: str
    content: str
    model_name: str | None = None
    tokens_prompt: int = 0
    tokens_completion: int = 0
    latency_ms: float = 0.0
    citations: list[CitationMetadata] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ChatSessionRecord:
    """Represents a persistent conversational chat session."""

    id: UUID
    organization_id: UUID
    user_id: UUID
    title: str = "New Conversation"
    is_archived: bool = False
    messages: list[ChatMessageRecord] = field(default_factory=list)


@dataclass
class AIQueryLogRecord:
    """Audit log entry for AI query executions."""

    id: UUID
    organization_id: UUID
    user_id: UUID
    query: str
    response: str
    tokens_used: int
    latency_ms: float
    model_name: str
    citations_count: int = 0


# ---------------------------------------------------------------------------
# Abstract Service & Repository Interfaces
# ---------------------------------------------------------------------------


class BaseVectorStore(ABC):
    """Abstract interface for dense vector persistence and ANN similarity search."""

    @abstractmethod
    async def upsert_vectors(self, vectors: list[VectorRecord]) -> int:
        """Upserts a batch of vector embeddings with payloads."""

    @abstractmethod
    async def similarity_search(
        self,
        query_vector: list[float],
        top_k: int,
        filter_criteria: VectorFilter,
    ) -> list[RetrievalResult]:
        """Executes tenant-filtered approximate nearest neighbor search."""

    @abstractmethod
    async def delete_vectors(
        self,
        vector_ids: list[UUID],
        organization_id: UUID,
    ) -> int:
        """Deletes vector embeddings by ID scoped to tenant."""

    @abstractmethod
    async def delete_vectors_by_document(
        self,
        document_id: UUID,
        organization_id: UUID,
    ) -> int:
        """Deletes all vector embeddings associated with a document."""


class BaseChunkRepository(ABC):
    """Abstract interface for managing document chunk persistence."""

    @abstractmethod
    async def create_chunks(
        self,
        chunks: list[DocumentChunkRecord],
    ) -> list[DocumentChunkRecord]:
        """Persists a batch of text chunks."""

    @abstractmethod
    async def get_chunks_by_document(
        self,
        document_id: UUID,
        organization_id: UUID,
    ) -> list[DocumentChunkRecord]:
        """Retrieves all chunks belonging to a document in sequential order."""

    @abstractmethod
    async def get_chunk_by_id(
        self,
        chunk_id: UUID,
        organization_id: UUID,
    ) -> DocumentChunkRecord | None:
        """Retrieves a single chunk by ID."""

    @abstractmethod
    async def delete_chunks_by_document(
        self,
        document_id: UUID,
        organization_id: UUID,
    ) -> int:
        """Deletes all chunks belonging to a document."""


class BaseKnowledgeGraphStore(ABC):
    """Abstract interface for Knowledge Graph entity and relationship persistence."""

    @abstractmethod
    async def upsert_entity(self, entity: KGEntityRecord) -> KGEntityRecord:
        """Creates or updates a knowledge graph entity node."""

    @abstractmethod
    async def upsert_relationship(
        self,
        relationship: KGRelationshipRecord,
    ) -> KGRelationshipRecord:
        """Creates or updates a directed knowledge graph relationship edge."""

    @abstractmethod
    async def get_entity_neighbors(
        self,
        entity_id: UUID,
        organization_id: UUID,
        max_depth: int = 1,
    ) -> dict[str, Any]:
        """Traverses interconnected neighbors up to max_depth hops."""

    @abstractmethod
    async def find_entity_by_name(
        self,
        name: str,
        entity_type: str,
        organization_id: UUID,
    ) -> KGEntityRecord | None:
        """Looks up an entity node by normalized name and type within tenant."""


class BaseChatHistoryRepository(ABC):
    """Abstract interface for conversational session and message persistence."""

    @abstractmethod
    async def create_session(self, session: ChatSessionRecord) -> ChatSessionRecord:
        """Creates a new conversational chat session."""

    @abstractmethod
    async def get_session(
        self,
        session_id: UUID,
        organization_id: UUID,
    ) -> ChatSessionRecord | None:
        """Retrieves a chat session by ID scoped to tenant."""

    @abstractmethod
    async def list_user_sessions(
        self,
        user_id: UUID,
        organization_id: UUID,
        limit: int = 50,
    ) -> list[ChatSessionRecord]:
        """Lists chat sessions belonging to a user."""

    @abstractmethod
    async def add_message(self, message: ChatMessageRecord) -> ChatMessageRecord:
        """Appends a new message to an existing chat session."""

    @abstractmethod
    async def get_session_messages(
        self,
        session_id: UUID,
        limit: int = 100,
    ) -> list[ChatMessageRecord]:
        """Retrieves chronological messages for a session."""

    @abstractmethod
    async def delete_session(
        self,
        session_id: UUID,
        organization_id: UUID,
    ) -> bool:
        """Soft-deletes or archives a chat session."""


class BaseAIQueryLogRepository(ABC):
    """Abstract interface for AI inference audit trail persistence."""

    @abstractmethod
    async def log_query(self, log_entry: AIQueryLogRecord) -> None:
        """Appends an AI query audit log entry."""

    @abstractmethod
    async def get_organization_usage(
        self,
        organization_id: UUID,
    ) -> dict[str, Any]:
        """Calculates token usage metrics and query count for tenant."""


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
        """Retrieves top-k relevant document chunks scoped to a tenant organization."""


class BaseReranker(ABC):
    """Abstract interface for cross-encoder or neural reranking models."""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
        top_n: int = 5,
    ) -> list[RetrievalResult]:
        """Reranks retrieved candidate chunks based on deep relevance scoring."""


class BaseContextBuilder(ABC):
    """Abstract interface for token-budget-aware context assembly."""

    @abstractmethod
    def build_context(
        self,
        candidates: list[RetrievalResult],
        max_context_tokens: int = 4096,
    ) -> list[ContextBlock]:
        """Assembles and truncates context blocks within LLM prompt token budget."""


class BaseCitationFormatter(ABC):
    """Abstract interface for formatting and linking citations in generated responses."""

    @abstractmethod
    def format_citations(
        self,
        answer: str,
        context_blocks: list[ContextBlock],
    ) -> list[CitationMetadata]:
        """Extracts and formats verified citations mapped to cited sources."""


class BaseHybridSearchService(ABC):
    """Abstract interface for hybrid (dense vector + sparse BM25) search orchestration."""

    @abstractmethod
    async def search(self, search_query: SearchQuery) -> SearchResultSet:
        """Executes hybrid retrieval, rank fusion, and filtering."""


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

    @abstractmethod
    async def stream_answer(
        self,
        query: str,
        organization_id: UUID,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """Streams generated tokens and citations in real-time via typed stream events."""


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

    @abstractmethod
    async def stream_question(
        self,
        query: str,
        organization_id: UUID,
        user_id: UUID,
        conversation_id: UUID | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """High-level entry point for streaming Q&A requests."""


class BaseRAGAccessController(ABC):
    """Abstract interface for RAG document gating, candidate pruning, and KG security."""

    @abstractmethod
    def filter_retrieval_candidates(
        self,
        candidates: list[RetrievalResult],
        security_context: RAGSecurityContext,
    ) -> list[RetrievalResult]:
        """Prunes candidate document chunks not authorized for the requesting user."""

    @abstractmethod
    def verify_document_access(
        self,
        document_id: UUID,
        security_context: RAGSecurityContext,
    ) -> bool:
        """Checks if a user is permitted to retrieve content from a specific document."""

    @abstractmethod
    def verify_graph_node_access(
        self,
        entity: KGEntityRecord,
        security_context: RAGSecurityContext,
    ) -> bool:
        """Checks if a user is permitted to view or traverse an entity node."""

