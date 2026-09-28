"""KEEP RAG Service Package.

Exposes abstract contracts, hybrid search pipelines, cross-encoder rerankers,
and citation synthesis engines.
"""

from backend.app.services.rag.interfaces import (
    BaseRAGEngine,
    BaseReranker,
    BaseRetriever,
    CitationMetadata,
    RAGResponse,
    RetrievalResult,
)

__all__ = [
    "BaseRAGEngine",
    "BaseReranker",
    "BaseRetriever",
    "CitationMetadata",
    "RAGResponse",
    "RetrievalResult",
]
