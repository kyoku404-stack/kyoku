"""KEEP Enterprise Platform — Enterprise Intelligence & Predictive Analytics Pydantic v2 Schemas.

Specification: devdocs/p2/p2.5.txt Section 16 & docs/API/api-contract.md Section 12
Author: Member 2 (Backend & Database Lead)
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DepartmentHealthScoreItem(BaseModel):
    """Departmental health score item."""

    model_config = ConfigDict(from_attributes=True)

    department: str
    score: int
    rating: str
    document_count: int = 0


class HealthScoreBreakdown(BaseModel):
    """Component metrics for Knowledge Health Score."""

    model_config = ConfigDict(from_attributes=True)

    overall_score: int
    rating: str
    coverage_score: float
    freshness_score: float
    quality_score: float
    retrieval_score: float
    duplicate_penalty: float
    department_breakdown: list[DepartmentHealthScoreItem] = Field(default_factory=list)
    identified_gaps: list[str] = Field(default_factory=list)


class KPIsResponse(BaseModel):
    """Executive KPI indicator values."""

    model_config = ConfigDict(from_attributes=True)

    active_users: int
    documents_uploaded: int
    ai_queries: int
    search_success_rate: float
    avg_response_time_ms: float
    storage_used_bytes: int
    storage_capacity_bytes: int
    knowledge_health_score: int


class ExecutiveDashboardResponse(BaseModel):
    """Consolidated executive intelligence overview response."""

    model_config = ConfigDict(from_attributes=True)

    health_score: HealthScoreBreakdown
    kpis: KPIsResponse
    active_anomalies_count: int
    top_recommendations_count: int
    executive_summary: str


class TrendPointItem(BaseModel):
    """Single point in a metric time series."""

    model_config = ConfigDict(from_attributes=True)

    date: str
    value: float


class DepartmentActivityItem(BaseModel):
    """Departmental operational activity metrics."""

    model_config = ConfigDict(from_attributes=True)

    department: str
    document_count: int
    query_count: int


class TrendAnalysisResponse(BaseModel):
    """Historical multi-series trend analysis response."""

    model_config = ConfigDict(from_attributes=True)

    period_days: int
    document_growth: list[TrendPointItem] = Field(default_factory=list)
    ai_query_volume: list[TrendPointItem] = Field(default_factory=list)
    department_activity: list[DepartmentActivityItem] = Field(default_factory=list)


class DocumentForecastItem(BaseModel):
    """Document growth projection."""

    model_config = ConfigDict(from_attributes=True)

    current_value: float
    projected_value: float
    growth_rate_pct: float
    confidence_lower: float
    confidence_upper: float


class StorageRunwayItem(BaseModel):
    """Storage exhaustion and runway projection."""

    model_config = ConfigDict(from_attributes=True)

    current_usage_bytes: int
    capacity_bytes: int
    days_to_85_pct: int
    days_to_full: int
    is_critical: bool


class QueryVolumeForecastItem(BaseModel):
    """AI query volume projection."""

    model_config = ConfigDict(from_attributes=True)

    current_daily_avg: float
    projected_daily_avg: float
    monthly_tokens_projected: int


class PredictionsResponse(BaseModel):
    """Consolidated predictive analytics forecast response."""

    model_config = ConfigDict(from_attributes=True)

    horizon_days: int
    document_forecast: DocumentForecastItem
    storage_runway: StorageRunwayItem
    query_volume_forecast: QueryVolumeForecastItem


class AnomalyResponseItem(BaseModel):
    """Operational anomaly item representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    metric_name: str
    anomaly_type: str
    severity: str
    description: str
    deviation_score: float
    detected_at: datetime
    resolved_at: datetime | None = None


class AnomaliesResponse(BaseModel):
    """List of detected anomalies response."""

    model_config = ConfigDict(from_attributes=True)

    total_detected: int
    anomalies: list[AnomalyResponseItem] = Field(default_factory=list)


class RecommendationResponseItem(BaseModel):
    """Strategic AI recommendation item representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    title: str
    description: str
    impact_score: float
    effort_score: float
    priority_index: float
    status: str
    action_payload: dict[str, Any] = Field(default_factory=dict)


class RecommendationsResponse(BaseModel):
    """Prioritized recommendations response."""

    model_config = ConfigDict(from_attributes=True)

    total_recommendations: int
    recommendations: list[RecommendationResponseItem] = Field(default_factory=list)


class KnowledgeHealthResponse(HealthScoreBreakdown):
    """Dedicated response for Knowledge Health Score endpoint."""

