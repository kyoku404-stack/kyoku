"""Abstract Interfaces and Contracts for AI / LLM & Embedding Providers.

Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/ai
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MessageRole(str, Enum):
    """Supported roles in conversational LLM interactions."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class LLMMessage:
    """Represents a single message in an LLM conversation prompt."""

    role: MessageRole
    content: str
    name: str | None = None


@dataclass
class LLMGenerationResult:
    """Result of an LLM generation call."""

    content: str
    model_name: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    finish_reason: str = "stop"
    raw_response: dict[str, Any] = field(default_factory=dict)


class BaseEmbeddingService(ABC):
    """Abstract interface for text embedding models."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns the vector dimensionality of the embedding model (e.g. 1536 or 384)."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the underlying model identifier string."""

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generates vector embeddings for a list of document chunk strings.

        Args:
            texts: List of text chunks to embed.

        Returns:
            List of high-dimensional float vector embeddings.
        """

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        """Generates a vector embedding for a single query string.

        Args:
            query: The user search query string.

        Returns:
            Single high-dimensional float vector embedding.
        """


class BaseLLMService(ABC):
    """Abstract interface for LLM orchestration (OpenAI, Anthropic, Local Ollama/vLLM)."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the model name identifier."""

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
