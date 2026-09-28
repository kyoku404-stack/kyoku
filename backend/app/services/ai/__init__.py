"""KEEP AI Service Package.

Exposes abstract contracts and implementations for LLMs, Embedding models,
and AI agent orchestrators.
"""

from backend.app.services.ai.interfaces import (
    BaseEmbeddingService,
    BaseLLMService,
    LLMGenerationResult,
    LLMMessage,
    MessageRole,
)

__all__ = [
    "BaseEmbeddingService",
    "BaseLLMService",
    "LLMGenerationResult",
    "LLMMessage",
    "MessageRole",
]
