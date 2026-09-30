"""KEEP Enterprise Platform — Analytics Schemas."""

from pydantic import BaseModel, Field


class AnalyticsSummaryResponse(BaseModel):
    """Aggregated usage and operational metrics summary."""

    total_documents: int = Field(default=0, description="Total ingested documents")
    total_queries: int = Field(default=0, description="Total search and RAG queries executed")
    total_users: int = Field(default=0, description="Total active users")
    active_sessions: int = Field(default=0, description="Currently active user sessions")
    storage_used_bytes: int = Field(default=0, description="Total document storage consumed in bytes")


class UsageMetricsResponse(BaseModel):
    """Detailed daily usage statistics."""

    queries_today: int = Field(default=0, description="Queries executed in the last 24h")
    tokens_consumed_today: int = Field(default=0, description="AI tokens processed today")
    avg_latency_ms: float = Field(default=0.0, description="Average query response latency in milliseconds")
