"""Integration Tests for Enterprise Intelligence & Predictive Analytics REST API Endpoints (Phase 2.5).

Verifies all 7 Intelligence endpoints defined in docs/api/api-contract.md Section 12:
1. GET /api/v1/analytics/dashboard
2. GET /api/v1/analytics/kpis
3. GET /api/v1/analytics/trends
4. GET /api/v1/analytics/predictions
5. GET /api/v1/analytics/anomalies
6. GET /api/v1/analytics/recommendations
7. GET /api/v1/analytics/knowledge-health

Specification: devdocs/p2/p2.5.txt & docs/api/api-contract.md Section 12
Owner: Member 2 (Backend & Database Lead)
"""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.analytics import AIRecommendation, DetectedAnomaly
from backend.app.models.department import Department
from backend.app.models.document import Document
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestAnalyticsIntelligenceEndpointsIntegration(unittest.TestCase):
    """Integration test suite for Phase 2.5 Intelligence & Analytics REST APIs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            # 1. Organization
            cls.org = Organization(
                name="Intelligence Test Org",
                domain=f"intelligence-{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            # 2. User with Admin role (has analytics.view permission)
            cls.user = User(
                email=f"intel-user-{uuid4().hex[:6]}@test.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Intelligence Test User",
                organization_id=cls.org_id,
                role="OrgAdmin",
            )
            session.add(cls.user)
            session.commit()
            session.refresh(cls.user)
            cls.user_id = cls.user.id

            # 3. Department
            cls.dept = Department(
                organization_id=cls.org_id,
                name="Engineering",
            )
            session.add(cls.dept)
            session.commit()
            session.refresh(cls.dept)

            # 4. Document
            cls.doc = Document(
                id=uuid4(),
                organization_id=cls.org_id,
                uploader_id=cls.user_id,
                filename="system-architecture.pdf",
                original_filename="system-architecture.pdf",
                title="System Architecture Guide",
                file_path="/tmp/system-architecture.pdf",
                file_type="pdf",
                mime_type="application/pdf",
                file_size=1048576,
                status="PROCESSED",
            )
            session.add(cls.doc)

            # 5. Anomaly
            cls.anomaly = DetectedAnomaly(
                organization_id=cls.org_id,
                metric_name="cross_department_collaboration",
                anomaly_type="ACTIVITY_DROP",
                severity="MEDIUM",
                description="Cross-team document sharing dropped 35% below baseline.",
                deviation_score=2.35,
            )
            session.add(cls.anomaly)

            # 6. Recommendation
            cls.rec = AIRecommendation(
                organization_id=cls.org_id,
                category="ARCHIVE",
                title="Archive 8 Stale RFCs",
                description="Documents have not been viewed or cited in >180 days.",
                impact_score=7.0,
                effort_score=1.5,
                priority_index=7.0,
                status="ACTIVE",
            )
            session.add(cls.rec)

            session.commit()

        # Auth Token
        token = create_access_token(
            data={
                "sub": str(cls.user_id),
                "email": cls.user.email,
                "org_id": str(cls.org_id),
                "role": "OrgAdmin",
            }
        )
        cls.headers = {"Authorization": f"Bearer {token}"}

    def test_01_get_executive_dashboard(self) -> None:
        """GET /api/v1/analytics/dashboard should return 200 with complete dashboard breakdown."""
        resp = self.client.get("/api/v1/analytics/dashboard", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        dashboard = data["data"]
        self.assertIn("health_score", dashboard)
        self.assertIn("kpis", dashboard)
        self.assertGreaterEqual(dashboard["active_anomalies_count"], 1)
        self.assertGreaterEqual(dashboard["top_recommendations_count"], 1)
        self.assertIn("executive_summary", dashboard)

    def test_02_get_kpis(self) -> None:
        """GET /api/v1/analytics/kpis should return 200 with platform metrics."""
        resp = self.client.get("/api/v1/analytics/kpis", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        kpis = data["data"]
        self.assertGreaterEqual(kpis["active_users"], 1)
        self.assertGreaterEqual(kpis["documents_uploaded"], 1)
        self.assertGreaterEqual(kpis["storage_used_bytes"], 1048576)
        self.assertGreaterEqual(kpis["knowledge_health_score"], 0)

    def test_03_get_trends(self) -> None:
        """GET /api/v1/analytics/trends should return 200 with multi-series trend points."""
        resp = self.client.get("/api/v1/analytics/trends?days=30", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        trends = data["data"]
        self.assertEqual(trends["period_days"], 30)
        self.assertGreater(len(trends["document_growth"]), 0)
        self.assertGreater(len(trends["ai_query_volume"]), 0)
        self.assertGreater(len(trends["department_activity"]), 0)

    def test_04_get_predictions(self) -> None:
        """GET /api/v1/analytics/predictions should return 200 with forecast projections."""
        resp = self.client.get("/api/v1/analytics/predictions?horizon_days=30", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        preds = data["data"]
        self.assertEqual(preds["horizon_days"], 30)
        self.assertIn("document_forecast", preds)
        self.assertIn("storage_runway", preds)
        self.assertIn("query_volume_forecast", preds)
        self.assertGreater(preds["storage_runway"]["days_to_85_pct"], 0)

    def test_05_get_anomalies(self) -> None:
        """GET /api/v1/analytics/anomalies should return 200 with detected anomalies."""
        resp = self.client.get("/api/v1/analytics/anomalies", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        anomalies_data = data["data"]
        self.assertGreaterEqual(anomalies_data["total_detected"], 1)
        self.assertGreater(len(anomalies_data["anomalies"]), 0)
        anomaly = anomalies_data["anomalies"][0]
        self.assertIn("metric_name", anomaly)
        self.assertIn("severity", anomaly)
        self.assertIn("deviation_score", anomaly)

    def test_06_get_recommendations(self) -> None:
        """GET /api/v1/analytics/recommendations should return 200 with prioritized recommendations."""
        resp = self.client.get("/api/v1/analytics/recommendations?status=ACTIVE", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        recs_data = data["data"]
        self.assertGreaterEqual(recs_data["total_recommendations"], 1)
        self.assertGreater(len(recs_data["recommendations"]), 0)
        rec = recs_data["recommendations"][0]
        self.assertIn("priority_index", rec)
        self.assertIn("impact_score", rec)
        self.assertIn("effort_score", rec)

    def test_07_get_knowledge_health(self) -> None:
        """GET /api/v1/analytics/knowledge-health should return 200 with KHS decomposition."""
        resp = self.client.get("/api/v1/analytics/knowledge-health", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        health = data["data"]
        self.assertIn("overall_score", health)
        self.assertIn("rating", health)
        self.assertIn("coverage_score", health)
        self.assertIn("freshness_score", health)
        self.assertIn("quality_score", health)
        self.assertIn("retrieval_score", health)
        self.assertIn("duplicate_penalty", health)
        self.assertIsInstance(health["department_breakdown"], list)
        self.assertIsInstance(health["identified_gaps"], list)
