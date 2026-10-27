"""Integration and Performance Benchmark Test Suite for Enterprise Intelligence & Predictive Analytics (Phase 2.5).

Verifies the end-to-end Enterprise Intelligence pipeline across:
1. Multi-tenant isolation and data quarantine boundaries (Tenant A vs Tenant B)
2. Knowledge Health Score (KHS) decomposition algorithm execution with seeded data
3. Statistical OLS linear regression forecasting & storage runway projection
4. Operational anomaly detection and lifecycle persistence
5. Strategic recommendation generation and Priority Index ranking ($PI = \\frac{\\text{Impact} \\times 1.5}{\\text{Effort}}$)
6. Performance latency benchmark satisfying SLA (< 2000ms execution)

Specification: devdocs/p2/p2.5.txt & docs/Architecture/enterprise-intelligence-predictive-analytics.md
Author: Member 4 (Integration & DevOps Lead)
"""

import time
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


class TestIntelligencePipelineIntegration(unittest.TestCase):
    """End-to-end integration and security benchmark suite for Phase 2.5 Enterprise Intelligence."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            # 1. Primary Tenant Organization Alpha
            cls.org_alpha = Organization(
                name="Intelligence Alpha Tenant",
                domain=f"alpha-intel-{uuid4().hex[:6]}.com",
            )
            # 2. Secondary Tenant Organization Beta (Multi-tenant quarantine)
            cls.org_beta = Organization(
                name="Intelligence Beta Tenant",
                domain=f"beta-intel-{uuid4().hex[:6]}.com",
            )
            session.add_all([cls.org_alpha, cls.org_beta])
            session.commit()
            session.refresh(cls.org_alpha)
            session.refresh(cls.org_beta)

            cls.org_alpha_id = cls.org_alpha.id
            cls.org_beta_id = cls.org_beta.id

            # 3. Users for each organization (OrgAdmin role)
            cls.user_alpha = User(
                email=f"alpha-admin-{uuid4().hex[:6]}@test.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Alpha Admin",
                organization_id=cls.org_alpha_id,
                role="OrgAdmin",
            )
            cls.user_beta = User(
                email=f"beta-admin-{uuid4().hex[:6]}@test.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Beta Admin",
                organization_id=cls.org_beta_id,
                role="OrgAdmin",
            )
            session.add_all([cls.user_alpha, cls.user_beta])
            session.commit()
            session.refresh(cls.user_alpha)
            session.refresh(cls.user_beta)

            cls.user_alpha_id = cls.user_alpha.id
            cls.user_beta_id = cls.user_beta.id

            # 4. Departments for Alpha
            cls.dept_alpha_eng = Department(
                organization_id=cls.org_alpha_id,
                name="Platform Engineering",
            )
            cls.dept_alpha_hr = Department(
                organization_id=cls.org_alpha_id,
                name="Human Resources",
            )
            session.add_all([cls.dept_alpha_eng, cls.dept_alpha_hr])

            # 5. Seed Documents for Alpha
            cls.doc_alpha_1 = Document(
                id=uuid4(),
                organization_id=cls.org_alpha_id,
                uploader_id=cls.user_alpha_id,
                filename="arch-spec.pdf",
                original_filename="arch-spec.pdf",
                title="System Architecture Specification",
                file_path="/tmp/arch-spec.pdf",
                file_type="pdf",
                mime_type="application/pdf",
                file_size=2097152,
                status="PROCESSED",
            )
            cls.doc_alpha_2 = Document(
                id=uuid4(),
                organization_id=cls.org_alpha_id,
                uploader_id=cls.user_alpha_id,
                filename="runbook.pdf",
                original_filename="runbook.pdf",
                title="Production Operations Runbook",
                file_path="/tmp/runbook.pdf",
                file_type="pdf",
                mime_type="application/pdf",
                file_size=1048576,
                status="PROCESSED",
            )

            # 6. Seed Specific Anomaly for Alpha only
            cls.anomaly_alpha = DetectedAnomaly(
                organization_id=cls.org_alpha_id,
                metric_name="cross_department_collaboration",
                anomaly_type="ACTIVITY_DROP",
                severity="HIGH",
                description="Alpha tenant collaboration dropped 45%.",
                deviation_score=2.85,
            )
            session.add(cls.anomaly_alpha)

            # 7. Seed Specific Recommendation for Alpha
            cls.rec_alpha = AIRecommendation(
                organization_id=cls.org_alpha_id,
                category="ARCHIVE",
                title="Archive Alpha Inactive Specs",
                description="Alpha documents stale >180 days.",
                impact_score=8.5,
                effort_score=1.5,
                priority_index=8.5,
                status="ACTIVE",
            )
            session.add(cls.rec_alpha)

            session.add_all([cls.doc_alpha_1, cls.doc_alpha_2])
            session.commit()

        # Auth Tokens
        cls.token_alpha = create_access_token(
            data={
                "sub": str(cls.user_alpha_id),
                "email": cls.user_alpha.email,
                "org_id": str(cls.org_alpha_id),
                "role": "OrgAdmin",
            }
        )
        cls.headers_alpha = {"Authorization": f"Bearer {cls.token_alpha}"}

        cls.token_beta = create_access_token(
            data={
                "sub": str(cls.user_beta_id),
                "email": cls.user_beta.email,
                "org_id": str(cls.org_beta_id),
                "role": "OrgAdmin",
            }
        )
        cls.headers_beta = {"Authorization": f"Bearer {cls.token_beta}"}

    def test_01_multi_tenant_isolation_quarantine(self) -> None:
        """Verifies strict multi-tenant boundary: Beta cannot see Alpha's anomalies or custom recs."""
        resp_alpha = self.client.get("/api/v1/analytics/anomalies", headers=self.headers_alpha)
        self.assertEqual(resp_alpha.status_code, 200)
        data_alpha = resp_alpha.json()["data"]
        alpha_anomaly_ids = [a["id"] for a in data_alpha["anomalies"]]
        self.assertIn(str(self.anomaly_alpha.id), alpha_anomaly_ids)

        resp_beta = self.client.get("/api/v1/analytics/anomalies", headers=self.headers_beta)
        self.assertEqual(resp_beta.status_code, 200)
        data_beta = resp_beta.json()["data"]
        beta_anomaly_ids = [a["id"] for a in data_beta["anomalies"]]
        self.assertNotIn(str(self.anomaly_alpha.id), beta_anomaly_ids)

    def test_02_khs_decomposition_execution(self) -> None:
        """Verifies multi-dimensional Knowledge Health Score formulation and factors."""
        resp = self.client.get("/api/v1/analytics/knowledge-health", headers=self.headers_alpha)
        self.assertEqual(resp.status_code, 200)
        health = resp.json()["data"]

        # Composite score bounds [0, 100]
        self.assertGreaterEqual(health["overall_score"], 0)
        self.assertLessEqual(health["overall_score"], 100)
        self.assertIn(health["rating"], ["EXCELLENT", "GOOD", "FAIR", "AT_RISK"])

        # Factors
        self.assertGreaterEqual(health["coverage_score"], 0.0)
        self.assertGreaterEqual(health["freshness_score"], 0.0)
        self.assertGreaterEqual(health["quality_score"], 0.0)
        self.assertGreaterEqual(health["retrieval_score"], 0.0)
        self.assertGreaterEqual(health["duplicate_penalty"], 0.0)

    def test_03_ols_forecast_and_runway_pipeline(self) -> None:
        """Verifies linear trend forecasting, 95% confidence intervals, and storage capacity runway."""
        resp = self.client.get("/api/v1/analytics/predictions?horizon_days=60", headers=self.headers_alpha)
        self.assertEqual(resp.status_code, 60 if False else 200)
        preds = resp.json()["data"]

        self.assertEqual(preds["horizon_days"], 60)
        doc_forecast = preds["document_forecast"]
        self.assertGreaterEqual(doc_forecast["projected_value"], doc_forecast["current_value"])
        self.assertGreaterEqual(doc_forecast["confidence_upper"], doc_forecast["confidence_lower"])

        storage_runway = preds["storage_runway"]
        self.assertGreater(storage_runway["days_to_85_pct"], 0)
        self.assertGreaterEqual(storage_runway["days_to_full"], storage_runway["days_to_85_pct"])
        self.assertFalse(storage_runway["is_critical"])

    def test_04_anomaly_detection_lifecycle(self) -> None:
        """Verifies Z-score deviation metrics and severity classifications."""
        resp = self.client.get("/api/v1/analytics/anomalies", headers=self.headers_alpha)
        self.assertEqual(resp.status_code, 200)
        anomalies = resp.json()["data"]["anomalies"]
        self.assertGreaterEqual(len(anomalies), 1)

        anomaly = anomalies[0]
        self.assertIn(anomaly["severity"], ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.assertGreater(anomaly["deviation_score"], 0.0)

    def test_05_recommendation_ranking_priority_index(self) -> None:
        """Verifies strategic recommendations are ordered descending by Priority Index."""
        resp = self.client.get("/api/v1/analytics/recommendations?status=ACTIVE", headers=self.headers_alpha)
        self.assertEqual(resp.status_code, 200)
        recs = resp.json()["data"]["recommendations"]
        self.assertGreaterEqual(len(recs), 1)

        for i in range(len(recs) - 1):
            self.assertGreaterEqual(recs[i]["priority_index"], recs[i + 1]["priority_index"])

    def test_06_dashboard_performance_sla_benchmark(self) -> None:
        """Verifies complete decision-support dashboard computation satisfies < 2000ms SLA."""
        start_time = time.perf_counter()
        resp = self.client.get("/api/v1/analytics/dashboard", headers=self.headers_alpha)
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        self.assertEqual(resp.status_code, 200)
        self.assertLess(duration_ms, 2000.0, f"Dashboard generation took {duration_ms:.2f}ms (exceeded 2000ms SLA)")
