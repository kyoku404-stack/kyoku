"""KEEP Enterprise Platform — Enterprise Intelligence, Predictive Analytics & Knowledge Health Domain Contracts.

Specification: devdocs/p2/p2.5.txt & docs/Architecture/enterprise-intelligence-predictive-analytics.md
Author: Member 1 (Project Lead & AI Architect)
"""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

# ==============================================================================
# Enumerations
# ==============================================================================

class HealthScoreRating(str, Enum):
    """Categorical performance tiers for Knowledge Health Score."""
    EXCELLENT = "EXCELLENT"  # >= 85
    GOOD = "GOOD"            # 70 - 84
    FAIR = "FAIR"            # 50 - 69
    AT_RISK = "AT_RISK"      # < 50


class AnomalySeverity(str, Enum):
    """Severity ratings for detected operational anomalies."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnomalyType(str, Enum):
    """Categorical taxonomy for operational anomalies."""
    ACTIVITY_DROP = "ACTIVITY_DROP"
    UNUSUAL_LOGIN = "UNUSUAL_LOGIN"
    DELETION_BURST = "DELETION_BURST"
    STORAGE_SPIKE = "STORAGE_SPIKE"
    API_FAILURE_SPIKE = "API_FAILURE_SPIKE"
    RETRIEVAL_DEGRADATION = "RETRIEVAL_DEGRADATION"


class RecommendationCategory(str, Enum):
    """Strategic recommendation taxonomy."""
    ARCHIVE = "ARCHIVE"
    DEDUPLICATE = "DEDUPLICATE"
    COVERAGE = "COVERAGE"
    OWNERSHIP = "OWNERSHIP"
    COLLABORATION = "COLLABORATION"
    SECURITY = "SECURITY"


class RecommendationStatus(str, Enum):
    """Lifecycle states for strategic recommendations."""
    ACTIVE = "ACTIVE"
    APPLIED = "APPLIED"
    DISMISSED = "DISMISSED"


class ForecastMetricType(str, Enum):
    """Metrics supported by time-series predictive forecasting."""
    DOCUMENTS = "DOCUMENTS"
    STORAGE = "STORAGE"
    AI_QUERIES = "AI_QUERIES"
    ACTIVE_USERS = "ACTIVE_USERS"


# ==============================================================================
# Data Structures
# ==============================================================================

@dataclass
class KnowledgeHealthBreakdown:
    """Component factor breakdown for Knowledge Health Score."""
    coverage_score: float = 0.0     # 0.0 - 100.0 (30% weight)
    freshness_score: float = 0.0    # 0.0 - 100.0 (25% weight)
    quality_score: float = 0.0      # 0.0 - 100.0 (25% weight)
    retrieval_score: float = 0.0    # 0.0 - 100.0 (20% weight)
    duplicate_penalty: float = 0.0  # deduction penalty


@dataclass
class DepartmentHealthScore:
    """Individual department knowledge health evaluation."""
    department: str
    score: int
    rating: HealthScoreRating
    document_count: int = 0


@dataclass
class KnowledgeHealthResult:
    """Consolidated Knowledge Health Score payload."""
    overall_score: int
    rating: HealthScoreRating
    coverage_score: float
    freshness_score: float
    quality_score: float
    retrieval_score: float
    duplicate_penalty: float
    department_breakdown: list[DepartmentHealthScore] = field(default_factory=list)
    identified_gaps: list[str] = field(default_factory=list)


@dataclass
class TrendDataPoint:
    """Individual time-series observation."""
    date: str
    value: float


@dataclass
class ForecastProjection:
    """Statistical OLS forecast with 95% confidence intervals."""
    current_value: float
    projected_value: float
    growth_rate_pct: float
    confidence_lower: float
    confidence_upper: float


@dataclass
class StorageRunwayProjection:
    """Storage capacity exhaustion forecast."""
    current_usage_bytes: int
    capacity_bytes: int
    days_to_85_pct: int
    days_to_full: int
    is_critical: bool


@dataclass
class QueryVolumeProjection:
    """AI query and token volume consumption forecast."""
    current_daily_avg: float
    projected_daily_avg: float
    monthly_tokens_projected: int


@dataclass
class PredictionResult:
    """Consolidated predictive analytics forecast."""
    horizon_days: int
    document_forecast: ForecastProjection
    storage_runway: StorageRunwayProjection
    query_volume_forecast: QueryVolumeProjection


@dataclass
class AnomalyItem:
    """Operational anomaly detection entity."""
    id: str
    metric_name: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    description: str
    deviation_score: float
    detected_at: datetime
    resolved_at: datetime | None = None


@dataclass
class StrategicRecommendationItem:
    """Actionable AI strategic recommendation with Priority Index."""
    id: str
    category: RecommendationCategory
    title: str
    description: str
    impact_score: float
    effort_score: float
    priority_index: float
    status: RecommendationStatus = RecommendationStatus.ACTIVE
    action_payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class KPISummary:
    """Core platform operational KPIs."""
    active_users: int
    documents_uploaded: int
    ai_queries: int
    search_success_rate: float
    avg_response_time_ms: float
    storage_used_bytes: int
    storage_capacity_bytes: int
    knowledge_health_score: int


@dataclass
class ExecutiveDashboardResult:
    """Master executive decision-support overview."""
    health_score: KnowledgeHealthResult
    kpis: KPISummary
    active_anomalies_count: int
    top_recommendations_count: int
    executive_summary: str


# ==============================================================================
# Abstract Engine Interfaces
# ==============================================================================

class BaseKnowledgeHealthCalculator(ABC):
    """Contract for computing multi-dimensional Knowledge Health Score."""

    @abstractmethod
    def calculate_health(
        self,
        coverage_pct: float,
        freshness_pct: float,
        quality_pct: float,
        retrieval_pct: float,
        duplicate_pct: float = 0.0,
        department_data: list[tuple[str, int, int]] | None = None,
    ) -> KnowledgeHealthResult:
        """Computes KHS using ADR-044 decomposed linear formula."""


class BaseTrendForecaster(ABC):
    """Contract for statistical OLS linear forecasting and runway estimation."""

    @abstractmethod
    def forecast_linear(
        self,
        historical_values: list[float],
        horizon_steps: int = 30,
    ) -> ForecastProjection:
        """Forecasts future value with standard error confidence bounds."""

    @abstractmethod
    def calculate_storage_runway(
        self,
        daily_growth_bytes: list[int],
        current_usage_bytes: int,
        capacity_bytes: int,
    ) -> StorageRunwayProjection:
        """Estimates days until 85% warning and 100% capacity threshold breaches."""


class BaseAnomalyDetector(ABC):
    """Contract for statistical Z-score anomaly detection."""

    @abstractmethod
    def detect_anomalies(
        self,
        metric_name: str,
        historical_series: list[float],
        current_value: float,
        anomaly_type: AnomalyType = AnomalyType.ACTIVITY_DROP,
    ) -> AnomalyItem | None:
        """Evaluates Z-score deviation against rolling baseline."""


class BaseRecommendationPrioritizer(ABC):
    """Contract for prioritizing AI strategic recommendations."""

    @abstractmethod
    def score_recommendation(
        self,
        impact: float,
        effort: float,
    ) -> float:
        """Computes Priority Index = (Impact * 1.5) / Effort."""

    @abstractmethod
    def rank_recommendations(
        self,
        recommendations: list[StrategicRecommendationItem],
    ) -> list[StrategicRecommendationItem]:
        """Ranks active recommendations in descending order of Priority Index."""


# ==============================================================================
# Concrete Reference Implementations
# ==============================================================================

class DefaultKnowledgeHealthCalculator(BaseKnowledgeHealthCalculator):
    """Concrete reference implementation of ADR-044 Knowledge Health Score."""

    def calculate_health(
        self,
        coverage_pct: float,
        freshness_pct: float,
        quality_pct: float,
        retrieval_pct: float,
        duplicate_pct: float = 0.0,
        department_data: list[tuple[str, int, int]] | None = None,
    ) -> KnowledgeHealthResult:
        # Clamp inputs to [0.0, 100.0]
        cov = max(0.0, min(100.0, coverage_pct))
        fresh = max(0.0, min(100.0, freshness_pct))
        qual = max(0.0, min(100.0, quality_pct))
        ret = max(0.0, min(100.0, retrieval_pct))
        dup = max(0.0, min(100.0, duplicate_pct))

        # Weighting: Coverage (30%), Freshness (25%), Quality (25%), Retrieval (20%) - Duplicate Penalty (up to 15%)
        raw_score = (0.30 * cov) + (0.25 * fresh) + (0.25 * qual) + (0.20 * ret) - (0.15 * dup)
        score = round(max(0.0, min(100.0, raw_score)))

        # Rating tier
        if score >= 85:
            rating = HealthScoreRating.EXCELLENT
        elif score >= 70:
            rating = HealthScoreRating.GOOD
        elif score >= 50:
            rating = HealthScoreRating.FAIR
        else:
            rating = HealthScoreRating.AT_RISK

        # Department breakdown
        dept_breakdown: list[DepartmentHealthScore] = []
        identified_gaps: list[str] = []

        if department_data:
            for dept_name, doc_count, stale_count in department_data:
                dept_fresh = ((doc_count - stale_count) / doc_count * 100.0) if doc_count > 0 else 0.0
                dept_score = round(0.6 * (100.0 if doc_count > 0 else 0.0) + 0.4 * dept_fresh)
                dept_rating = (
                    HealthScoreRating.EXCELLENT if dept_score >= 85
                    else HealthScoreRating.GOOD if dept_score >= 70
                    else HealthScoreRating.FAIR if dept_score >= 50
                    else HealthScoreRating.AT_RISK
                )
                dept_breakdown.append(DepartmentHealthScore(
                    department=dept_name,
                    score=dept_score,
                    rating=dept_rating,
                    document_count=doc_count,
                ))
                if doc_count == 0:
                    identified_gaps.append(f"{dept_name} has no indexed operational documentation.")
                elif stale_count > (doc_count // 2):
                    identified_gaps.append(f"{dept_name} has over 50% stale documentation (>90 days old).")

        if not identified_gaps:
            if dup > 20:
                identified_gaps.append(f"High duplicate redundancy detected ({dup:.1f}% duplicate chunk penalty).")
            if fresh < 60:
                identified_gaps.append("Organization documentation freshness is below 60% baseline.")

        return KnowledgeHealthResult(
            overall_score=score,
            rating=rating,
            coverage_score=cov,
            freshness_score=fresh,
            quality_score=qual,
            retrieval_score=ret,
            duplicate_penalty=round(dup * 0.15, 1),
            department_breakdown=dept_breakdown,
            identified_gaps=identified_gaps,
        )


class DefaultTrendForecaster(BaseTrendForecaster):
    """Concrete reference implementation of OLS linear forecasting and runway estimation."""

    def forecast_linear(
        self,
        historical_values: list[float],
        horizon_steps: int = 30,
    ) -> ForecastProjection:
        if not historical_values:
            return ForecastProjection(0.0, 0.0, 0.0, 0.0, 0.0)

        n = len(historical_values)
        if n == 1:
            val = historical_values[0]
            return ForecastProjection(val, val, 0.0, val, val)

        # X is time indices 0 .. n-1
        x_mean = (n - 1) / 2.0
        y_mean = sum(historical_values) / n

        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(historical_values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        slope = (numerator / denominator) if denominator != 0 else 0.0
        intercept = y_mean - (slope * x_mean)

        current_val = historical_values[-1]
        # Forecast step n - 1 + horizon_steps
        target_step = (n - 1) + horizon_steps
        projected_val = max(0.0, intercept + (slope * target_step))

        # Standard error of regression
        residuals = [
            historical_values[i] - (intercept + slope * i)
            for i in range(n)
        ]
        sse = sum(r ** 2 for r in residuals)
        se = math.sqrt(sse / max(1, n - 2)) if n > 2 else (0.1 * current_val)

        growth_rate = ((projected_val - current_val) / current_val * 100.0) if current_val > 0 else 0.0
        margin = 1.96 * se

        return ForecastProjection(
            current_value=round(current_val, 2),
            projected_value=round(projected_val, 2),
            growth_rate_pct=round(growth_rate, 1),
            confidence_lower=round(max(0.0, projected_val - margin), 2),
            confidence_upper=round(projected_val + margin, 2),
        )

    def calculate_storage_runway(
        self,
        daily_growth_bytes: list[int],
        current_usage_bytes: int,
        capacity_bytes: int,
    ) -> StorageRunwayProjection:
        if not daily_growth_bytes or capacity_bytes <= 0:
            return StorageRunwayProjection(
                current_usage_bytes=current_usage_bytes,
                capacity_bytes=capacity_bytes,
                days_to_85_pct=999,
                days_to_full=999,
                is_critical=False,
            )

        avg_daily_growth = max(1, int(sum(daily_growth_bytes) / len(daily_growth_bytes)))
        target_85_bytes = int(capacity_bytes * 0.85)
        remaining_to_85 = max(0, target_85_bytes - current_usage_bytes)
        remaining_to_full = max(0, capacity_bytes - current_usage_bytes)

        days_to_85 = remaining_to_85 // avg_daily_growth
        days_to_full = remaining_to_full // avg_daily_growth

        is_critical = (current_usage_bytes / capacity_bytes) >= 0.85 or days_to_85 <= 14

        return StorageRunwayProjection(
            current_usage_bytes=current_usage_bytes,
            capacity_bytes=capacity_bytes,
            days_to_85_pct=days_to_85,
            days_to_full=days_to_full,
            is_critical=is_critical,
        )


class DefaultAnomalyDetector(BaseAnomalyDetector):
    """Concrete reference implementation of Z-score anomaly detector."""

    def detect_anomalies(
        self,
        metric_name: str,
        historical_series: list[float],
        current_value: float,
        anomaly_type: AnomalyType = AnomalyType.ACTIVITY_DROP,
    ) -> AnomalyItem | None:
        if len(historical_series) < 3:
            return None

        n = len(historical_series)
        mean_val = sum(historical_series) / n
        variance = sum((x - mean_val) ** 2 for x in historical_series) / n
        std_dev = math.sqrt(variance)

        if std_dev == 0.0:
            return None

        z_score = abs(current_value - mean_val) / std_dev

        if z_score < 2.0:
            return None

        # Severity classification
        if z_score >= 3.0:
            severity = AnomalySeverity.CRITICAL
        elif z_score >= 2.5:
            severity = AnomalySeverity.HIGH
        else:
            severity = AnomalySeverity.MEDIUM

        delta_pct = ((current_value - mean_val) / mean_val * 100.0) if mean_val != 0 else 0.0
        direction = "decreased" if current_value < mean_val else "increased"

        description = (
            f"Metric '{metric_name}' {direction} by {abs(delta_pct):.1f}% "
            f"(Z-score: {z_score:.2f}) compared to historical baseline."
        )

        return AnomalyItem(
            id=str(uuid4()),
            metric_name=metric_name,
            anomaly_type=anomaly_type,
            severity=severity,
            description=description,
            deviation_score=round(z_score, 2),
            detected_at=datetime.now(UTC),
        )


class DefaultRecommendationPrioritizer(BaseRecommendationPrioritizer):
    """Concrete reference implementation of Priority Index recommendation ranking."""

    def score_recommendation(
        self,
        impact: float,
        effort: float,
    ) -> float:
        eff = max(0.5, effort)
        return round((impact * 1.5) / eff, 2)

    def rank_recommendations(
        self,
        recommendations: list[StrategicRecommendationItem],
    ) -> list[StrategicRecommendationItem]:
        active_recs = [r for r in recommendations if r.status == RecommendationStatus.ACTIVE]
        for rec in active_recs:
            rec.priority_index = self.score_recommendation(rec.impact_score, rec.effort_score)
        active_recs.sort(key=lambda r: r.priority_index, reverse=True)
        return active_recs
