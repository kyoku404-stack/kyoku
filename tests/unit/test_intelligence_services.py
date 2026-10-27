"""Unit tests for Phase 2.5 Enterprise Intelligence & Predictive Analytics Service.

Owner: Member 2 (Backend & Database Lead)
Domain: /tests/unit
Specification: devdocs/p2/p2.5.txt & docs/Architecture/enterprise-intelligence-predictive-analytics.md
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.app.services.intelligence.service import EnterpriseIntelligenceService


@pytest.fixture
def mock_db() -> AsyncMock:
    db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    mock_res.scalar.return_value = 15
    mock_res.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_res
    db.scalar.return_value = 10
    return db


class TestEnterpriseIntelligenceServiceUnit:
    """Unit test suite for EnterpriseIntelligenceService methods."""

    @pytest.mark.asyncio
    async def test_get_knowledge_health_calculation(self, mock_db: AsyncMock):
        service = EnterpriseIntelligenceService()
        org_id = uuid4()

        res = await service.get_knowledge_health(db=mock_db, organization_id=org_id)

        assert res.overall_score >= 0 and res.overall_score <= 100
        assert res.rating in ["EXCELLENT", "GOOD", "FAIR", "AT_RISK"]
        assert 0.0 <= res.coverage_score <= 100.0
        assert 0.0 <= res.freshness_score <= 100.0
        assert 0.0 <= res.quality_score <= 100.0
        assert 0.0 <= res.retrieval_score <= 100.0
        assert isinstance(res.identified_gaps, list)

    @pytest.mark.asyncio
    async def test_get_kpis_indicators(self, mock_db: AsyncMock):
        service = EnterpriseIntelligenceService()
        org_id = uuid4()

        kpis = await service.get_kpis(db=mock_db, organization_id=org_id)

        assert kpis.active_users >= 1
        assert kpis.documents_uploaded >= 0
        assert kpis.ai_queries >= 0
        assert 0.0 <= kpis.search_success_rate <= 1.0
        assert kpis.avg_response_time_ms > 0
        assert kpis.storage_capacity_bytes > kpis.storage_used_bytes
        assert 0 <= kpis.knowledge_health_score <= 100

    @pytest.mark.asyncio
    async def test_get_trends_series(self, mock_db: AsyncMock):
        service = EnterpriseIntelligenceService()
        org_id = uuid4()

        trends = await service.get_trends(db=mock_db, organization_id=org_id, days=30)

        assert trends.period_days == 30
        assert len(trends.document_growth) > 0
        assert len(trends.ai_query_volume) > 0
        assert len(trends.department_activity) > 0

    @pytest.mark.asyncio
    async def test_get_predictions_ols(self, mock_db: AsyncMock):
        service = EnterpriseIntelligenceService()
        org_id = uuid4()

        predictions = await service.get_predictions(db=mock_db, organization_id=org_id, horizon_days=30)

        assert predictions.horizon_days == 30
        assert predictions.document_forecast.projected_value >= predictions.document_forecast.current_value
        assert predictions.document_forecast.confidence_upper >= predictions.document_forecast.confidence_lower
        assert predictions.storage_runway.days_to_85_pct > 0
        assert predictions.storage_runway.days_to_full >= predictions.storage_runway.days_to_85_pct
        assert predictions.query_volume_forecast.monthly_tokens_projected > 0

    @pytest.mark.asyncio
    async def test_get_anomalies_persistence_and_seeding(self, mock_db: AsyncMock):
        service = EnterpriseIntelligenceService()
        org_id = uuid4()

        anomalies = await service.get_anomalies(db=mock_db, organization_id=org_id)

        assert len(anomalies) >= 1
        assert anomalies[0].severity in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert anomalies[0].deviation_score > 0

    @pytest.mark.asyncio
    async def test_get_recommendations_ranking(self, mock_db: AsyncMock):
        service = EnterpriseIntelligenceService()
        org_id = uuid4()

        recs = await service.get_recommendations(db=mock_db, organization_id=org_id, status="ACTIVE")

        assert len(recs) >= 1
        # Check priority index descending order
        for i in range(len(recs) - 1):
            assert recs[i].priority_index >= recs[i + 1].priority_index

    @pytest.mark.asyncio
    async def test_get_executive_dashboard_consolidation(self, mock_db: AsyncMock):
        service = EnterpriseIntelligenceService()
        org_id = uuid4()

        dash = await service.get_executive_dashboard(db=mock_db, organization_id=org_id)

        assert dash.health_score.overall_score >= 0
        assert dash.kpis.active_users >= 1
        assert dash.active_anomalies_count >= 1
        assert dash.top_recommendations_count >= 1
        assert len(dash.executive_summary) > 20
