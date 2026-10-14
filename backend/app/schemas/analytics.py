"""KEEP Enterprise Platform — Analytics Schemas.

Authoritative schemas for organizational analytics and operational metrics.
Conforms to docs/API/api-contract.md Section 5.6.
"""

from backend.app.schemas.dashboard import ProjectDistributionItem, TimeSeriesPoint
from pydantic import BaseModel, Field


class AnalyticsSummaryResponse(BaseModel):
    """Aggregated usage and operational metrics summary."""

    period: str = Field(default="week", description="Aggregation period: week, month, quarter, year")
    documents_uploaded: list[TimeSeriesPoint] = Field(default_factory=list)
    active_users: list[TimeSeriesPoint] = Field(default_factory=list)
    new_members: list[TimeSeriesPoint] = Field(default_factory=list)
    project_distribution: list[ProjectDistributionItem] = Field(default_factory=list)
    ai_usage_trend: list[TimeSeriesPoint] = Field(default_factory=list)
    search_trend: list[TimeSeriesPoint] = Field(default_factory=list)

    # Backwards-compatible legacy operational counters
    total_documents: int | None = Field(default=None, description="Total ingested documents")
    total_queries: int | None = Field(default=None, description="Total search and RAG queries executed")
    total_users: int | None = Field(default=None, description="Total active users")
    active_sessions: int | None = Field(default=None, description="Currently active user sessions")
    storage_used_bytes: int | None = Field(default=None, description="Total document storage consumed in bytes")


class UsageMetricsResponse(BaseModel):
    """Detailed daily usage statistics."""

    queries_today: int = Field(default=0, description="Queries executed in the last 24h")
    tokens_consumed_today: int = Field(default=0, description="AI tokens processed today")
    avg_latency_ms: float = Field(default=0.0, description="Average query response latency in milliseconds")
