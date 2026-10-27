"""Unit Test Suite for Phase 2.5 Enterprise Intelligence & Predictive Analytics Contracts.

Verifies:
1. Knowledge Health Score calculation, factor weighting, bounds clamping, and rating tiers.
2. Department breakdown and knowledge gap identification.
3. Statistical OLS linear trend forecasting and 95% confidence intervals.
4. Storage runway and capacity exhaustion warning logic.
5. Z-score anomaly detection and severity classification.
6. Priority Index scoring and recommendation ranking.

Specification: devdocs/p2/p2.5.txt & docs/Architecture/enterprise-intelligence-predictive-analytics.md
Author: Member 1 (Project Lead & AI Architect)
"""

import unittest

from backend.app.services.intelligence.contracts import (
    AnomalySeverity,
    AnomalyType,
    DefaultAnomalyDetector,
    DefaultKnowledgeHealthCalculator,
    DefaultRecommendationPrioritizer,
    DefaultTrendForecaster,
    HealthScoreRating,
    RecommendationCategory,
    RecommendationStatus,
    StrategicRecommendationItem,
)


class TestEnterpriseIntelligenceContracts(unittest.TestCase):
    """Unit tests for Phase 2.5 algorithms and domain contracts."""

    def setUp(self) -> None:
        self.health_calc = DefaultKnowledgeHealthCalculator()
        self.forecaster = DefaultTrendForecaster()
        self.anomaly_detector = DefaultAnomalyDetector()
        self.prioritizer = DefaultRecommendationPrioritizer()

    # --------------------------------------------------------------------------
    # 1. Knowledge Health Score (KHS) Tests
    # --------------------------------------------------------------------------

    def test_01_health_score_excellent_rating(self) -> None:
        """Verifies high coverage, freshness, quality and retrieval yields EXCELLENT rating."""
        res = self.health_calc.calculate_health(
            coverage_pct=95.0,
            freshness_pct=90.0,
            quality_pct=92.0,
            retrieval_pct=90.0,
            duplicate_pct=2.0,
        )
        self.assertGreaterEqual(res.overall_score, 85)
        self.assertEqual(res.rating, HealthScoreRating.EXCELLENT)
        self.assertEqual(res.coverage_score, 95.0)

    def test_02_health_score_fair_and_at_risk_tiers(self) -> None:
        """Verifies lower factors and duplicate penalties lower the score into FAIR or AT_RISK."""
        # Moderate performance
        res_fair = self.health_calc.calculate_health(
            coverage_pct=60.0,
            freshness_pct=50.0,
            quality_pct=60.0,
            retrieval_pct=55.0,
            duplicate_pct=10.0,
        )
        self.assertGreaterEqual(res_fair.overall_score, 50)
        self.assertLess(res_fair.overall_score, 70)
        self.assertEqual(res_fair.rating, HealthScoreRating.FAIR)

        # Depleted knowledge performance
        res_at_risk = self.health_calc.calculate_health(
            coverage_pct=30.0,
            freshness_pct=20.0,
            quality_pct=40.0,
            retrieval_pct=30.0,
            duplicate_pct=40.0,
        )
        self.assertLess(res_at_risk.overall_score, 50)
        self.assertEqual(res_at_risk.rating, HealthScoreRating.AT_RISK)

    def test_03_health_score_department_breakdown_and_gaps(self) -> None:
        """Verifies per-department score breakdown and automated gap detection."""
        dept_data = [
            ("Platform Engineering", 45, 5),  # 45 docs, 5 stale -> good
            ("Human Resources", 0, 0),        # 0 docs -> uncovered gap
            ("Legal", 20, 16),                # 20 docs, 16 stale -> >50% stale gap
        ]
        res = self.health_calc.calculate_health(
            coverage_pct=66.7,
            freshness_pct=70.0,
            quality_pct=75.0,
            retrieval_pct=80.0,
            department_data=dept_data,
        )
        self.assertEqual(len(res.department_breakdown), 3)
        self.assertTrue(any("Human Resources has no indexed operational documentation" in gap for gap in res.identified_gaps))
        self.assertTrue(any("Legal has over 50% stale documentation" in gap for gap in res.identified_gaps))

    # --------------------------------------------------------------------------
    # 2. Predictive Analytics & Forecasting Tests
    # --------------------------------------------------------------------------

    def test_04_ols_linear_trend_forecasting(self) -> None:
        """Verifies linear trend projection with upward trajectory and confidence intervals."""
        # Historical monthly document counts: 100, 110, 120, 130, 140
        historical = [100.0, 110.0, 120.0, 130.0, 140.0]
        forecast = self.forecaster.forecast_linear(historical, horizon_steps=3)

        self.assertEqual(forecast.current_value, 140.0)
        self.assertGreater(forecast.projected_value, 140.0)
        self.assertAlmostEqual(forecast.projected_value, 170.0, delta=1.0)
        self.assertGreater(forecast.growth_rate_pct, 0.0)
        self.assertLessEqual(forecast.confidence_lower, forecast.projected_value)
        self.assertGreaterEqual(forecast.confidence_upper, forecast.projected_value)

    def test_05_storage_runway_calculation(self) -> None:
        """Verifies storage days-to-85% and days-to-full capacity runway projection."""
        capacity = 10_000_000_000       # 10 GB
        current_usage = 8_000_000_000   # 8 GB (80% used)
        daily_growth = [50_000_000] * 7  # 50 MB / day

        runway = self.forecaster.calculate_storage_runway(
            daily_growth_bytes=daily_growth,
            current_usage_bytes=current_usage,
            capacity_bytes=capacity,
        )

        # 85% target is 8.5 GB -> 500 MB remaining -> 10 days at 50 MB/day
        self.assertEqual(runway.days_to_85_pct, 10)
        # 100% target is 10 GB -> 2 GB remaining -> 40 days at 50 MB/day
        self.assertEqual(runway.days_to_full, 40)
        self.assertTrue(runway.is_critical)  # True because days_to_85 <= 14

    # --------------------------------------------------------------------------
    # 3. Anomaly Detection Tests
    # --------------------------------------------------------------------------

    def test_06_z_score_anomaly_detection(self) -> None:
        """Verifies statistical outlier detection flags deviations exceeding Z >= 2.0."""
        # Rolling baseline: mean ~ 100, std ~ 5
        baseline = [102.0, 98.0, 101.0, 99.0, 100.0, 103.0, 97.0]

        # Normal value within 1 standard deviation
        no_anomaly = self.anomaly_detector.detect_anomalies(
            metric_name="collaboration_events",
            historical_series=baseline,
            current_value=102.0,
        )
        self.assertIsNone(no_anomaly)

        # Sudden severe drop (Z-score > 3.0)
        critical_anomaly = self.anomaly_detector.detect_anomalies(
            metric_name="collaboration_events",
            historical_series=baseline,
            current_value=30.0,
            anomaly_type=AnomalyType.ACTIVITY_DROP,
        )
        self.assertIsNotNone(critical_anomaly)
        self.assertEqual(critical_anomaly.severity, AnomalySeverity.CRITICAL)
        self.assertGreaterEqual(critical_anomaly.deviation_score, 3.0)

    # --------------------------------------------------------------------------
    # 4. Strategic Recommendation Prioritization Tests
    # --------------------------------------------------------------------------

    def test_07_recommendation_priority_scoring_and_ranking(self) -> None:
        """Verifies Priority Index = (Impact * 1.5) / Effort and descending rank order."""
        rec_high_win = StrategicRecommendationItem(
            id="rec-1",
            category=RecommendationCategory.ARCHIVE,
            title="Archive Inactive Documents",
            description="High impact, low effort quick win.",
            impact_score=8.0,
            effort_score=1.5,
            priority_index=0.0,
        )
        rec_low_win = StrategicRecommendationItem(
            id="rec-2",
            category=RecommendationCategory.COVERAGE,
            title="Rewrite Entire SOP Catalog",
            description="High impact, very high effort initiative.",
            impact_score=9.0,
            effort_score=5.0,
            priority_index=0.0,
        )
        rec_dismissed = StrategicRecommendationItem(
            id="rec-3",
            category=RecommendationCategory.DEDUPLICATE,
            title="Merge Duplicate Specs",
            description="Already dismissed recommendation.",
            impact_score=10.0,
            effort_score=1.0,
            priority_index=0.0,
            status=RecommendationStatus.DISMISSED,
        )

        ranked = self.prioritizer.rank_recommendations([rec_low_win, rec_high_win, rec_dismissed])

        # Dismissed should be excluded from active ranked list
        self.assertEqual(len(ranked), 2)
        # rec-1 PI: (8.0 * 1.5) / 1.5 = 8.0
        # rec-2 PI: (9.0 * 1.5) / 5.0 = 2.7
        self.assertEqual(ranked[0].id, "rec-1")
        self.assertEqual(ranked[1].id, "rec-2")
        self.assertEqual(ranked[0].priority_index, 8.0)
        self.assertEqual(ranked[1].priority_index, 2.7)


if __name__ == "__main__":
    unittest.main()
