"""KEEP AI & LLM Service Package.

Exposes abstract contracts for LLMs, embedding models, prompt management,
token usage tracking, semantic caching, and AI assistants.
"""

from backend.app.services.ai.interfaces import (
    AIExecutionContext,
    AIPermission,
    AISecurityContext,
    BaseAIAccessController,
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
    ROLE_PERMISSIONS,
    TokenUsage,
    ToolCallResult,
    ToolDefinition,
    UserRole,
)

__all__ = [
    "AIExecutionContext",
    "AIPermission",
    "AISecurityContext",
    "BaseAIAccessController",
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
    "ROLE_PERMISSIONS",
    "TokenUsage",
    "ToolCallResult",
    "ToolDefinition",
    "UserRole",
]
