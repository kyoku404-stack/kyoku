"""Abstract Interfaces and Data Contracts for KEEP RAG, Vector & Persistence Layer.

Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/rag
Specification: devdocs/p1/p1.2.txt (Chapters 10, 11, 12, 19) & devdocs/p1/p1.3.txt (Chapters 6, 7, 14, 19)
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
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


class WorkspaceMemoryScope(str, Enum):
    """Hierarchical memory scopes for RAG retrieval routing."""

    ORG_WIDE = "org_wide"
    DEPARTMENT_WIDE = "department_wide"
    TEAM_WIDE = "team_wide"
    PROJECT_LOCAL = "project_local"


@dataclass
class RetrievalResult:
    """Represents a single retrieved chunk candidate with similarity score and hierarchy context."""

    chunk_id: UUID
    document_id: UUID
    content: str
    score: float
    filename: str = ""
    page_number: int | None = None
    chunk_index: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    organization_id: UUID | None = None
    department_id: UUID | None = None
    team_id: UUID | None = None
    project_id: UUID | None = None


@dataclass
class RAGSecurityContext:
    """Multi-tenant security context applied to RAG retrieval and citation filtering."""

    user_id: UUID
    organization_id: UUID
    role: str = "Member"
    allowed_document_ids: set[UUID] | None = None
    accessible_project_ids: set[UUID] | None = None
    department_id: UUID | None = None
    team_ids: set[UUID] = field(default_factory=set)

    def can_access_document(self, document_id: UUID) -> bool:
        """Verifies if the user is authorized to read chunks from the document."""
        if self.allowed_document_ids is None:
            return True
        return document_id in self.allowed_document_ids

    def can_access_project(self, project_id: UUID) -> bool:
        """Verifies if the user is authorized to retrieve knowledge scoped to the project."""
        if self.accessible_project_ids is None:
            return True
        return project_id in self.accessible_project_ids

    def can_access_department(self, department_id: UUID) -> bool:
        """Verifies if the user is authorized to retrieve knowledge from the department."""
        if self.department_id is None:
            return True
        return self.department_id == department_id

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
    trace_id: str | None = None
    request_id: str | None = None
    cost_usd: float = 0.0


@dataclass
class RAGObservabilityTelemetry:
    """End-to-end telemetry profile for a hybrid RAG query execution."""

    query: str
    trace_id: str | None = None
    request_id: str | None = None
    organization_id: UUID | None = None
    user_id: UUID | None = None
    model_name: str = "gpt-4o"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    embedding_latency_ms: float = 0.0
    retrieval_latency_ms: float = 0.0
    rerank_latency_ms: float = 0.0
    generation_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    candidate_chunks_count: int = 0
    reranked_chunks_count: int = 0
    top_similarity_score: float = 0.0
    citation_count: int = 0
    is_cached: bool = False
    status: str = "success"
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serializes telemetry profile to a dictionary."""
        return {
            "query": self.query,
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "model_name": self.model_name,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "embedding_latency_ms": round(self.embedding_latency_ms, 2),
            "retrieval_latency_ms": round(self.retrieval_latency_ms, 2),
            "rerank_latency_ms": round(self.rerank_latency_ms, 2),
            "generation_latency_ms": round(self.generation_latency_ms, 2),
            "total_latency_ms": round(self.total_latency_ms, 2),
            "candidate_chunks_count": self.candidate_chunks_count,
            "reranked_chunks_count": self.reranked_chunks_count,
            "top_similarity_score": round(self.top_similarity_score, 4),
            "citation_count": self.citation_count,
            "is_cached": self.is_cached,
            "status": self.status,
            "error_message": self.error_message,
        }


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


class BaseWorkspaceMemoryRouter(ABC):
    """Abstract interface for routing RAG retrieval across organizational memory spaces."""

    @abstractmethod
    def route_query_scopes(
        self,
        query: str,
        security_context: RAGSecurityContext,
        requested_scope: WorkspaceMemoryScope | None = None,
    ) -> list[WorkspaceMemoryScope]:
        """Determines which hierarchical memory spaces to query based on user intent and active context."""

    @abstractmethod
    def filter_candidates_by_workspace(
        self,
        candidates: list[RetrievalResult],
        security_context: RAGSecurityContext,
    ) -> list[RetrievalResult]:
        """Prunes candidate document chunks not authorized for the requesting user's workspace scope."""


class BaseAIAuthorizationFilter(ABC):
    """Abstract interface for authorization-aware AI retrieval filtering.

    Enforces resource-level permissions and tenant boundary on RAG candidates
    and Knowledge Graph entity traversals before context assembly (devdocs/p1/p1.6.txt Ch 14).
    """

    @abstractmethod
    def filter_knowledge_candidates(
        self,
        candidates: list[RetrievalResult],
        security_context: RAGSecurityContext,
    ) -> list[RetrievalResult]:
        """Prunes RAG candidates to only those authorized for the caller."""

    @abstractmethod
    def authorize_kg_traversal(
        self,
        entities: list[KGEntityRecord],
        security_context: RAGSecurityContext,
    ) -> list[KGEntityRecord]:
        """Filters KG entities to only those from caller-accessible documents."""


# ==============================================================================
# Phase 1.8 Document Upload, File Management & Storage System Contracts
# Specification: devdocs/p1/p1.8.txt (Chapters 1–21)
# Architecture: docs/Architecture/document-management-architecture.md
# ADRs: ADR-023, ADR-024, ADR-025
# ==============================================================================


class DocumentProcessingState(str, Enum):
    """Explicit 9-state processing and ingestion state machine.

    Ref: devdocs/p1/p1.8.txt Chapter 16 and docs/Architecture/document-management-architecture.md
    """

    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    AWAITING_PROCESSING = "AWAITING_PROCESSING"
    QUEUED = "QUEUED"
    EXTRACTING = "EXTRACTING"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    READY_FOR_AI = "READY_FOR_AI"
    UPDATED = "UPDATED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"

    def is_terminal(self) -> bool:
        """Returns True if the state represents a terminal lifecycle point."""
        return self in {DocumentProcessingState.FAILED, DocumentProcessingState.DELETED}

    def is_ai_ready(self) -> bool:
        """Returns True if document chunks are indexed and ready for semantic RAG search."""
        return self == DocumentProcessingState.READY_FOR_AI

    def can_transition_to(self, target: "DocumentProcessingState") -> bool:
        """Evaluates whether transitioning to target state is legally permissible."""
        valid_transitions: dict[DocumentProcessingState, set[DocumentProcessingState]] = {
            DocumentProcessingState.PENDING: {
                DocumentProcessingState.VALIDATED,
                DocumentProcessingState.FAILED,
            },
            DocumentProcessingState.VALIDATED: {
                DocumentProcessingState.AWAITING_PROCESSING,
                DocumentProcessingState.FAILED,
            },
            DocumentProcessingState.AWAITING_PROCESSING: {
                DocumentProcessingState.QUEUED,
                DocumentProcessingState.FAILED,
                DocumentProcessingState.ARCHIVED,
                DocumentProcessingState.DELETED,
            },
            DocumentProcessingState.QUEUED: {
                DocumentProcessingState.EXTRACTING,
                DocumentProcessingState.FAILED,
            },
            DocumentProcessingState.EXTRACTING: {
                DocumentProcessingState.CHUNKING,
                DocumentProcessingState.FAILED,
            },
            DocumentProcessingState.CHUNKING: {
                DocumentProcessingState.EMBEDDING,
                DocumentProcessingState.FAILED,
            },
            DocumentProcessingState.EMBEDDING: {
                DocumentProcessingState.READY_FOR_AI,
                DocumentProcessingState.FAILED,
            },
            DocumentProcessingState.READY_FOR_AI: {
                DocumentProcessingState.UPDATED,
                DocumentProcessingState.ARCHIVED,
                DocumentProcessingState.DELETED,
            },
            DocumentProcessingState.UPDATED: {
                DocumentProcessingState.QUEUED,
                DocumentProcessingState.ARCHIVED,
                DocumentProcessingState.DELETED,
            },
            DocumentProcessingState.FAILED: {
                DocumentProcessingState.AWAITING_PROCESSING,  # Retry
                DocumentProcessingState.DELETED,
            },
            DocumentProcessingState.ARCHIVED: {
                DocumentProcessingState.AWAITING_PROCESSING,  # Un-archive / restore
                DocumentProcessingState.DELETED,
            },
            DocumentProcessingState.DELETED: set(),  # Terminal
        }
        return target in valid_transitions.get(self, set())


class DocumentCategory(str, Enum):
    """Canonical 10 enterprise document categories.

    Ref: devdocs/p1/p1.8.txt Chapter 10.
    """

    POLICIES = "POLICIES"
    REPORTS = "REPORTS"
    MEETING_MINUTES = "MEETING_MINUTES"
    RESEARCH = "RESEARCH"
    LEGAL = "LEGAL"
    FINANCE = "FINANCE"
    HR = "HR"
    TECHNICAL_DOCUMENTATION = "TECHNICAL_DOCUMENTATION"
    PRESENTATIONS = "PRESENTATIONS"
    TRAINING_MATERIALS = "TRAINING_MATERIALS"


class SupportedFileType(str, Enum):
    """Supported file extensions and document formats.

    Ref: devdocs/p1/p1.8.txt Chapter 4.
    """

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    RTF = "rtf"
    PPTX = "pptx"
    XLSX = "xlsx"
    CSV = "csv"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    WEBP = "webp"


# Canonical MIME types mapping
FILE_TYPE_MIME_MAP: dict[SupportedFileType, str] = {
    SupportedFileType.PDF: "application/pdf",
    SupportedFileType.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    SupportedFileType.TXT: "text/plain",
    SupportedFileType.MD: "text/markdown",
    SupportedFileType.RTF: "application/rtf",
    SupportedFileType.PPTX: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    SupportedFileType.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    SupportedFileType.CSV: "text/csv",
    SupportedFileType.PNG: "image/png",
    SupportedFileType.JPG: "image/jpeg",
    SupportedFileType.JPEG: "image/jpeg",
    SupportedFileType.WEBP: "image/webp",
}

# Maximum file sizes in bytes (devdocs Chapter 6)
MAX_FILE_SIZES: dict[SupportedFileType, int] = {
    SupportedFileType.PDF: 100 * 1024 * 1024,  # 100 MB
    SupportedFileType.DOCX: 50 * 1024 * 1024,  # 50 MB
    SupportedFileType.TXT: 20 * 1024 * 1024,  # 20 MB
    SupportedFileType.MD: 20 * 1024 * 1024,  # 20 MB
    SupportedFileType.RTF: 20 * 1024 * 1024,  # 20 MB
    SupportedFileType.PPTX: 100 * 1024 * 1024,  # 100 MB
    SupportedFileType.XLSX: 50 * 1024 * 1024,  # 50 MB
    SupportedFileType.CSV: 20 * 1024 * 1024,  # 20 MB
    SupportedFileType.PNG: 20 * 1024 * 1024,  # 20 MB
    SupportedFileType.JPG: 20 * 1024 * 1024,  # 20 MB
    SupportedFileType.JPEG: 20 * 1024 * 1024,  # 20 MB
    SupportedFileType.WEBP: 20 * 1024 * 1024,  # 20 MB
}

# Magic bytes signature prefixes for content validation
MAGIC_BYTE_SIGNATURES: dict[SupportedFileType, list[bytes]] = {
    SupportedFileType.PDF: [b"%PDF-"],
    SupportedFileType.DOCX: [b"PK\x03\x04"],
    SupportedFileType.PPTX: [b"PK\x03\x04"],
    SupportedFileType.XLSX: [b"PK\x03\x04"],
    SupportedFileType.PNG: [b"\x89PNG\r\n\x1a\n"],
    SupportedFileType.JPG: [b"\xff\xd8\xff"],
    SupportedFileType.JPEG: [b"\xff\xd8\xff"],
    SupportedFileType.WEBP: [b"RIFF"],
    SupportedFileType.RTF: [b"{\\rtf"],
}


@dataclass
class DocumentMetadata:
    """Core document metadata record matching Chapter 9."""

    document_id: UUID
    organization_id: UUID
    uploader_id: UUID
    filename: str
    original_filename: str
    file_type: str
    mime_type: str
    file_size_bytes: int
    checksum_sha256: str
    storage_path: str
    version_number: int = 1
    category: DocumentCategory = DocumentCategory.REPORTS
    tags: list[str] = field(default_factory=list)
    status: DocumentProcessingState = DocumentProcessingState.AWAITING_PROCESSING
    ai_ready: bool = False
    project_id: UUID | None = None
    department_id: UUID | None = None
    title: str | None = None
    description: str | None = None
    error_message: str | None = None
    chunk_count: int = 0
    extracted_metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class DocumentVersionInfo:
    """Immutable version snapshot metadata record matching Chapter 11."""

    version_id: UUID
    document_id: UUID
    version_number: int
    file_path: str
    file_size_bytes: int
    checksum_sha256: str
    mime_type: str
    uploader_id: UUID
    change_notes: str | None = None
    metadata_json: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass
class DocumentValidationResult:
    """Outcome of server-side file attribute and magic byte validation."""

    is_valid: bool
    sanitized_filename: str
    detected_file_type: SupportedFileType | None = None
    detected_mime_type: str | None = None
    file_size_bytes: int = 0
    checksum_sha256: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class BaseDocumentValidator(ABC):
    """Abstract interface for server-side document validation (devdocs Chapter 6)."""

    @abstractmethod
    def validate_file_attributes(
        self,
        filename: str,
        file_size: int,
        mime_type: str | None = None,
    ) -> DocumentValidationResult:
        """Validates filename extension, size limit, and assigns sanitized attributes."""

    @abstractmethod
    def verify_magic_bytes(
        self,
        header_bytes: bytes,
        expected_type: SupportedFileType,
    ) -> bool:
        """Sniffs header magic bytes to prevent MIME-type spoofing."""

    @abstractmethod
    def sanitize_filename(self, filename: str) -> str:
        """Sanitizes filename against path traversal attacks and illegal characters."""

    @abstractmethod
    def compute_checksum(self, content: bytes) -> str:
        """Calculates SHA-256 cryptographic digest of file contents."""


class BaseFileStorageService(ABC):
    """Abstract interface for multi-tenant physical/cloud file storage (devdocs Chapter 7 & 8)."""

    @abstractmethod
    async def save_file(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        filename: str,
        content: bytes,
    ) -> str:
        """Stores binary document content in organization-isolated path and returns storage URI."""

    @abstractmethod
    async def get_file_path(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        filename: str,
    ) -> str:
        """Resolves physical filesystem or object storage path for a document version."""

    @abstractmethod
    async def read_file(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        filename: str,
    ) -> bytes:
        """Reads binary document bytes for streaming download or preview generation."""

    @abstractmethod
    async def delete_file(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        filename: str,
    ) -> bool:
        """Deletes binary document version from physical storage."""

    @abstractmethod
    async def get_storage_usage(self, organization_id: UUID) -> int:
        """Aggregates total bytes stored for the given organization tenant."""

    @abstractmethod
    async def check_quota(
        self,
        organization_id: UUID,
        additional_bytes: int,
        quota_limit: int,
    ) -> bool:
        """Verifies if tenant storage quota allows storing additional bytes."""

    @abstractmethod
    def generate_preview_path(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        preview_format: str = "pdf",
    ) -> str:
        """Generates tenant-isolated path for cached preview artifact."""


class BaseRAGDocumentIngestionSeam(ABC):
    """Abstract interface linking Phase 1.8 document storage to Phase 2 RAG ingestion pipeline."""

    @abstractmethod
    async def dispatch_ingestion_task(
        self,
        document_id: UUID,
        version_number: int,
        organization_id: UUID,
    ) -> str:
        """Dispatches asynchronous Celery ingestion task and returns the queued task ID."""

    @abstractmethod
    async def update_processing_status(
        self,
        document_id: UUID,
        new_status: DocumentProcessingState,
        error_message: str | None = None,
    ) -> bool:
        """Transitions document processing state during async extraction and embedding."""

    @abstractmethod
    async def register_version_chunks(
        self,
        document_id: UUID,
        version_number: int,
        chunk_ids: list[UUID],
    ) -> int:
        """Associates generated vector chunks with the specific document version snapshot."""

    @abstractmethod
    async def deactivate_superseded_version_chunks(
        self,
        document_id: UUID,
        active_version: int,
    ) -> int:
        """Deactivates semantic chunks belonging to prior versions when new revision reaches READY_FOR_AI."""



