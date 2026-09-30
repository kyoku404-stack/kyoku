"""KEEP AI & LLM Service Package.

Exposes abstract contracts for LLMs, embedding models, prompt management,
token usage tracking, semantic caching, and AI assistants.
"""

from backend.app.services.ai.interfaces import (
    AIExecutionContext,
    BaseAssistantService,
    BaseEmbeddingService,
    BaseLLMService,
    BasePromptService,
    BaseSemanticCacheService,
    BaseTokenTrackerService,
    LLMGenerationResult,
    LLMMessage,
    MessageRole,
    PromptTemplate,
    TokenUsage,
    ToolCallResult,
    ToolDefinition,
)

__all__ = [
    "AIExecutionContext",
    "BaseAssistantService",
    "BaseEmbeddingService",
    "BaseLLMService",
    "BasePromptService",
    "BaseSemanticCacheService",
    "BaseTokenTrackerService",
    "LLMGenerationResult",
    "LLMMessage",
    "MessageRole",
    "PromptTemplate",
    "TokenUsage",
    "ToolCallResult",
    "ToolDefinition",
]
