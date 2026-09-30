"""KEEP RAG Service Package.

Exposes abstract contracts, hybrid search pipelines, cross-encoder rerankers,
context builders, citation formatters, and RAG synthesis engines.
"""

from backend.app.services.rag.interfaces import (
    BaseCitationFormatter,
    BaseContextBuilder,
    BaseHybridSearchService,
    BaseKnowledgeGraphQueryService,
    BaseRAGEngine,
    BaseRAGService,
    BaseReranker,
    BaseRetriever,
    CitationMetadata,
    ContextBlock,
    RAGResponse,
    RetrievalResult,
    SearchQuery,
    SearchResultSet,
    StreamEvent,
    StreamEventType,
)

__all__ = [
    "BaseCitationFormatter",
    "BaseContextBuilder",
    "BaseHybridSearchService",
    "BaseKnowledgeGraphQueryService",
    "BaseRAGEngine",
    "BaseRAGService",
    "BaseReranker",
    "BaseRetriever",
    "CitationMetadata",
    "ContextBlock",
    "RAGResponse",
    "RetrievalResult",
    "SearchQuery",
    "SearchResultSet",
    "StreamEvent",
    "StreamEventType",
]
