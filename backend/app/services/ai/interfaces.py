"""Abstract Interfaces and Contracts for AI / LLM, Embedding Providers, Prompts & Context.

Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/ai
Specification: devdocs/p1/p1.2.txt (Chapters 10, 11, 16, 17, 19)
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID


class MessageRole(str, Enum):
    """Supported roles in conversational LLM interactions."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


@dataclass
class LLMMessage:
    """Represents a single message in an LLM conversation prompt."""

    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None


@dataclass
class TokenUsage:
    """Token consumption and accounting container."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


@dataclass
class LLMGenerationResult:
    """Result of an LLM generation call."""

    content: str
    model_name: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    finish_reason: str = "stop"
    usage: TokenUsage = field(default_factory=TokenUsage)
    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass
class AIExecutionContext:
    """Multi-tenant execution context attached to all AI operations."""

    organization_id: UUID
    user_id: UUID
    session_id: str | None = None
    model_name: str = "gpt-4o"
    temperature: float = 0.2
    max_tokens: int | None = 2048
    enable_cache: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptTemplate:
    """Structured, parameterized prompt template."""

    name: str
    version: str
    template: str
    system_instruction: str = ""
    input_variables: list[str] = field(default_factory=list)
    default_parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDefinition:
    """Schema defining a tool or function callable by the AI model."""

    name: str
    description: str
    parameters_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCallResult:
    """Result returned by a tool execution dispatched by an AI agent."""

    tool_name: str
    call_id: str
    output: Any
    is_error: bool = False


class BaseEmbeddingService(ABC):
    """Abstract interface for text embedding models."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns the vector dimensionality of the embedding model (e.g. 1536 or 384)."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the underlying model identifier string."""
        pass

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generates vector embeddings for a list of document chunk strings.

        Args:
            texts: List of text chunks to embed.

        Returns:
            List of high-dimensional float vector embeddings.
        """
        pass

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        """Generates a vector embedding for a single query string.

        Args:
            query: The user search query string.

        Returns:
            Single high-dimensional float vector embedding.
        """
        pass


class BaseLLMService(ABC):
    """Abstract interface for LLM orchestration (OpenAI, Anthropic, Local Ollama/vLLM)."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the model name identifier."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMGenerationResult:
        """Executes a single non-streaming generation call.

        Args:
            messages: List of structured conversation messages.
            temperature: Sampling temperature (0.0 for deterministic answers).
            max_tokens: Maximum tokens in completion.

        Returns:
            Structured LLMGenerationResult.
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Executes a streaming generation call yielding tokens in real time.

        Args:
            messages: List of structured conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in completion.

        Yields:
            Token strings as they arrive from the LLM engine.
        """
        pass


class BasePromptService(ABC):
    """Abstract interface for loading and rendering versioned prompt templates."""

    @abstractmethod
    def render_prompt(
        self,
        template_name: str,
        variables: dict[str, Any],
    ) -> list[LLMMessage]:
        """Renders messages from a named template and parameter map."""
        pass


class BaseSemanticCacheService(ABC):
    """Abstract interface for semantic query and response caching."""

    @abstractmethod
    async def get_cached_response(
        self,
        query: str,
        organization_id: UUID,
        similarity_threshold: float = 0.95,
    ) -> str | None:
        """Looks up a semantically equivalent query in cache."""
        pass

    @abstractmethod
    async def set_cached_response(
        self,
        query: str,
        response: str,
        organization_id: UUID,
        ttl_seconds: int = 86400,
    ) -> None:
        """Stores a query-response pair in semantic cache."""
        pass


class BaseTokenTrackerService(ABC):
    """Abstract interface for tracking token consumption and enterprise quotas."""

    @abstractmethod
    async def record_usage(
        self,
        context: AIExecutionContext,
        usage: TokenUsage,
    ) -> None:
        """Records token usage for billing, audit, and quota tracking."""
        pass

    @abstractmethod
    async def check_quota(self, organization_id: UUID) -> bool:
        """Verifies if tenant has remaining quota for AI inference."""
        pass


class BaseAssistantService(ABC):
    """Abstract interface for multi-tool AI assistant orchestration."""

    @abstractmethod
    async def process_user_intent(
        self,
        user_input: str,
        context: AIExecutionContext,
        available_tools: list[ToolDefinition] | None = None,
    ) -> LLMGenerationResult:
        """Processes intent, coordinates tool calling, and generates final answer."""
        pass
