"""KEEP AI Observability, Monitoring & Telemetry Contracts.

Specification Source: devdocs/p1/p1.9.txt (Chapter 5, 6, 8, 17)
Phase: 1.9 — Logging, Monitoring & System Observability
Role: Member 1 (Project Lead & AI Architect)

Defines authoritative typed contracts for tracking LLM token consumption,
cost estimation, vector search retrieval latency, citation grounding quality,
distributed trace correlation, and AI-specific KPI aggregation.
"""

from __future__ import annotations

import math
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class AIOperationType(str, Enum):
    """Enumeration of observable AI operations across Phase 2 and Phase 3."""

    EMBEDDING_GENERATION = "embedding_generation"
    VECTOR_SEARCH = "vector_search"
    HYBRID_SEARCH = "hybrid_search"
    LLM_COMPLETION = "llm_completion"
    LLM_STREAM = "llm_stream"
    RAG_QUERY = "rag_query"
    GRAPH_EXTRACTION = "graph_extraction"
    GRAPH_QUERY = "graph_query"
    DOCUMENT_CHUNKING = "document_chunking"
    CITATION_GROUNDING = "citation_grounding"
    AGENT_TOOL_CALL = "agent_tool_call"


class AILogLevel(str, Enum):
    """Standardized log levels conforming to devdocs Chapter 6."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# Default pricing catalog (USD per 1,000 tokens)
DEFAULT_MODEL_PRICING: dict[str, dict[str, float]] = {
    # OpenAI GPT-4o
    "gpt-4o": {
        "prompt_cost_per_1k": 0.0050,
        "completion_cost_per_1k": 0.0150,
    },
    # OpenAI GPT-4o Mini
    "gpt-4o-mini": {
        "prompt_cost_per_1k": 0.00015,
        "completion_cost_per_1k": 0.00060,
    },
    # OpenAI Embedding 3 Small
    "text-embedding-3-small": {
        "prompt_cost_per_1k": 0.00002,
        "completion_cost_per_1k": 0.0,
    },
    # OpenAI Embedding 3 Large
    "text-embedding-3-large": {
        "prompt_cost_per_1k": 0.00013,
        "completion_cost_per_1k": 0.0,
    },
    # Local / Self-Hosted Open-Source (Zero cloud API cost)
    "all-MiniLM-L6-v2": {
        "prompt_cost_per_1k": 0.0,
        "completion_cost_per_1k": 0.0,
    },
    "mistral-7b-instruct": {
        "prompt_cost_per_1k": 0.0,
        "completion_cost_per_1k": 0.0,
    },
    "llama-3-8b": {
        "prompt_cost_per_1k": 0.0,
        "completion_cost_per_1k": 0.0,
    },
}


@dataclass
class AIExecutionMetrics:
    """Execution performance and token consumption metrics for an AI operation."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    time_to_first_token_ms: float | None = None
    estimated_cost_usd: float = 0.0
    model_name: str = ""
    provider: str = "openai"

    def __post_init__(self) -> None:
        if self.total_tokens == 0 and (self.prompt_tokens > 0 or self.completion_tokens > 0):
            self.total_tokens = self.prompt_tokens + self.completion_tokens

    def to_dict(self) -> dict[str, Any]:
        """Converts execution metrics to a dictionary representation."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": round(self.latency_ms, 3),
            "time_to_first_token_ms": round(self.time_to_first_token_ms, 3)
            if self.time_to_first_token_ms is not None
            else None,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "model_name": self.model_name,
            "provider": self.provider,
        }


@dataclass
class RAGRetrievalMetrics:
    """Specialized telemetry metrics for dense/sparse RAG vector queries."""

    query: str
    candidate_count: int = 0
    rerank_count: int = 0
    top_similarity_score: float = 0.0
    average_similarity_score: float = 0.0
    retrieval_latency_ms: float = 0.0
    context_token_count: int = 0
    filtered_chunk_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Converts retrieval metrics to a dictionary representation."""
        return {
            "query": self.query,
            "candidate_count": self.candidate_count,
            "rerank_count": self.rerank_count,
            "top_similarity_score": round(self.top_similarity_score, 4),
            "average_similarity_score": round(self.average_similarity_score, 4),
            "retrieval_latency_ms": round(self.retrieval_latency_ms, 3),
            "context_token_count": self.context_token_count,
            "filtered_chunk_count": len(self.filtered_chunk_ids),
        }


@dataclass
class AIObservabilityEvent:
    """Standardized event record capturing execution, trace, and telemetry context."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    trace_id: str | None = None
    request_id: str | None = None
    organization_id: UUID | None = None
    user_id: UUID | None = None
    project_id: UUID | None = None
    operation_type: AIOperationType = AIOperationType.RAG_QUERY
    level: AILogLevel = AILogLevel.INFO
    status: str = "success"  # "success", "failure", "degraded"
    execution_metrics: AIExecutionMetrics | None = None
    retrieval_metrics: RAGRetrievalMetrics | None = None
    error_details: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        """Serializes the event into canonical JSON structured log format."""
        payload: dict[str, Any] = {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "module": "ai_observability",
            "action": self.operation_type.value,
            "status": self.status,
            "event_id": self.event_id,
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "project_id": str(self.project_id) if self.project_id else None,
            "execution_time_ms": self.execution_metrics.latency_ms
            if self.execution_metrics
            else 0.0,
            "metadata": dict(self.metadata),
        }

        if self.execution_metrics:
            payload["execution_metrics"] = self.execution_metrics.to_dict()

        if self.retrieval_metrics:
            payload["retrieval_metrics"] = self.retrieval_metrics.to_dict()

        if self.error_details:
            payload["error_details"] = self.error_details

        return payload


@dataclass
class AIMonitoringKPIs:
    """Aggregated key performance indicators for an organization or system."""

    organization_id: UUID | None
    total_operations: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    average_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    error_count: int = 0
    error_rate_percent: float = 0.0
    operation_counts_by_type: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Converts KPI statistics to a dictionary."""
        return {
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "total_operations": self.total_operations,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "average_latency_ms": round(self.average_latency_ms, 2),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "error_count": self.error_count,
            "error_rate_percent": round(self.error_rate_percent, 2),
            "operation_counts_by_type": self.operation_counts_by_type,
        }


class BaseAICostCalculator(ABC):
    """Abstract interface for estimating financial costs of AI model inference."""

    @abstractmethod
    def calculate_cost(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Calculates estimated cost in USD based on model pricing."""


class DefaultAICostCalculator(BaseAICostCalculator):
    """Standard cost calculator using registered model pricing table."""

    def __init__(self, pricing_catalog: dict[str, dict[str, float]] | None = None) -> None:
        self.pricing = pricing_catalog or DEFAULT_MODEL_PRICING

    def calculate_cost(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Calculates cost in USD for the given token quantities."""
        rates = self.pricing.get(model_name)
        if not rates:
            # Fallback for unknown or fine-tuned models
            return 0.0

        p_rate = rates.get("prompt_cost_per_1k", 0.0) / 1000.0
        c_rate = rates.get("completion_cost_per_1k", 0.0) / 1000.0
        return (prompt_tokens * p_rate) + (completion_tokens * c_rate)


class BaseAIObservabilityCollector(ABC):
    """Abstract protocol for recording, aggregating, and retrieving AI telemetry."""

    @abstractmethod
    def record_event(self, event: AIObservabilityEvent) -> None:
        """Records a single observability event."""

    @abstractmethod
    def record_llm_metrics(
        self,
        operation_type: AIOperationType,
        metrics: AIExecutionMetrics,
        organization_id: UUID | None = None,
        user_id: UUID | None = None,
        project_id: UUID | None = None,
        request_id: str | None = None,
        trace_id: str | None = None,
        status: str = "success",
        error_details: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AIObservabilityEvent:
        """Helper to create and record an LLM execution event."""

    @abstractmethod
    def record_retrieval_metrics(
        self,
        retrieval_metrics: RAGRetrievalMetrics,
        organization_id: UUID | None = None,
        user_id: UUID | None = None,
        project_id: UUID | None = None,
        request_id: str | None = None,
        trace_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AIObservabilityEvent:
        """Helper to create and record a vector retrieval event."""

    @abstractmethod
    def get_organization_kpis(
        self,
        organization_id: UUID | None = None,
        since: datetime | None = None,
    ) -> AIMonitoringKPIs:
        """Aggregates KPI metrics for a specific organization or all tenants."""

    @abstractmethod
    def get_recent_events(
        self,
        organization_id: UUID | None = None,
        limit: int = 50,
    ) -> list[AIObservabilityEvent]:
        """Returns recent events matching filters."""

    @abstractmethod
    def flush(self) -> None:
        """Flushes buffered events to underlying sinks."""


class InMemoryAIObservabilityCollector(BaseAIObservabilityCollector):
    """Thread-safe, in-memory collector for local development, tests, and base telemetry."""

    def __init__(
        self,
        cost_calculator: BaseAICostCalculator | None = None,
        max_events: int = 2000,
    ) -> None:
        self.cost_calculator = cost_calculator or DefaultAICostCalculator()
        self.max_events = max_events
        self._events: list[AIObservabilityEvent] = []
        self._lock = threading.Lock()

    def record_event(self, event: AIObservabilityEvent) -> None:
        """Thread-safely stores an observability event with capacity management."""
        with self._lock:
            if len(self._events) >= self.max_events:
                # Evict oldest 20% to prevent unbound growth
                trim_count = max(1, self.max_events // 5)
                self._events = self._events[trim_count:]
            self._events.append(event)

    def record_llm_metrics(
        self,
        operation_type: AIOperationType,
        metrics: AIExecutionMetrics,
        organization_id: UUID | None = None,
        user_id: UUID | None = None,
        project_id: UUID | None = None,
        request_id: str | None = None,
        trace_id: str | None = None,
        status: str = "success",
        error_details: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AIObservabilityEvent:
        """Creates and stores an LLM metrics event, computing costs if omitted."""
        if metrics.estimated_cost_usd == 0.0 and metrics.model_name:
            metrics.estimated_cost_usd = self.cost_calculator.calculate_cost(
                model_name=metrics.model_name,
                prompt_tokens=metrics.prompt_tokens,
                completion_tokens=metrics.completion_tokens,
            )

        level = AILogLevel.ERROR if status == "failure" else AILogLevel.INFO

        event = AIObservabilityEvent(
            trace_id=trace_id,
            request_id=request_id,
            organization_id=organization_id,
            user_id=user_id,
            project_id=project_id,
            operation_type=operation_type,
            level=level,
            status=status,
            execution_metrics=metrics,
            error_details=error_details,
            metadata=metadata or {},
        )
        self.record_event(event)
        return event

    def record_retrieval_metrics(
        self,
        retrieval_metrics: RAGRetrievalMetrics,
        organization_id: UUID | None = None,
        user_id: UUID | None = None,
        project_id: UUID | None = None,
        request_id: str | None = None,
        trace_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AIObservabilityEvent:
        """Creates and records a vector retrieval event."""
        exec_metrics = AIExecutionMetrics(
            latency_ms=retrieval_metrics.retrieval_latency_ms,
            total_tokens=retrieval_metrics.context_token_count,
        )

        event = AIObservabilityEvent(
            trace_id=trace_id,
            request_id=request_id,
            organization_id=organization_id,
            user_id=user_id,
            project_id=project_id,
            operation_type=AIOperationType.VECTOR_SEARCH,
            level=AILogLevel.INFO,
            status="success",
            execution_metrics=exec_metrics,
            retrieval_metrics=retrieval_metrics,
            metadata=metadata or {},
        )
        self.record_event(event)
        return event

    def get_organization_kpis(
        self,
        organization_id: UUID | None = None,
        since: datetime | None = None,
    ) -> AIMonitoringKPIs:
        """Aggregates KPI metrics across stored events."""
        with self._lock:
            filtered = [
                e
                for e in self._events
                if (organization_id is None or e.organization_id == organization_id)
                and (since is None or e.timestamp >= since)
            ]

        total_ops = len(filtered)
        if total_ops == 0:
            return AIMonitoringKPIs(organization_id=organization_id)

        prompt_tokens = 0
        comp_tokens = 0
        total_tokens = 0
        total_cost = 0.0
        latencies: list[float] = []
        error_count = 0
        op_counts: dict[str, int] = {}

        for e in filtered:
            op_key = e.operation_type.value
            op_counts[op_key] = op_counts.get(op_key, 0) + 1

            if e.status != "success":
                error_count += 1

            if e.execution_metrics:
                m = e.execution_metrics
                prompt_tokens += m.prompt_tokens
                comp_tokens += m.completion_tokens
                total_tokens += m.total_tokens
                total_cost += m.estimated_cost_usd
                if m.latency_ms > 0:
                    latencies.append(m.latency_ms)

        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        p95_latency = 0.0
        if latencies:
            latencies.sort()
            idx = math.ceil(len(latencies) * 0.95) - 1
            p95_latency = latencies[max(0, min(idx, len(latencies) - 1))]

        error_rate = (error_count / total_ops) * 100.0

        return AIMonitoringKPIs(
            organization_id=organization_id,
            total_operations=total_ops,
            total_prompt_tokens=prompt_tokens,
            total_completion_tokens=comp_tokens,
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
            average_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            error_count=error_count,
            error_rate_percent=error_rate,
            operation_counts_by_type=op_counts,
        )

    def get_recent_events(
        self,
        organization_id: UUID | None = None,
        limit: int = 50,
    ) -> list[AIObservabilityEvent]:
        """Returns the most recent events."""
        with self._lock:
            filtered = [
                e
                for e in self._events
                if organization_id is None or e.organization_id == organization_id
            ]
            return list(reversed(filtered[-limit:]))

    def flush(self) -> None:
        """No-op for in-memory collector."""


# Global singleton instance for easy cross-module recording
default_ai_observability_collector = InMemoryAIObservabilityCollector()
