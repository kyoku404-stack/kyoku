"""Unit Test Suite for Prometheus Metrics Registry & KPI Aggregations.

Specification Source: devdocs/p1/p1.9.txt (Chapter 8, 15, 17) & ADR-027
Phase: 1.9 — Logging, Monitoring & System Observability
Role: Member 2 (Backend & Database Lead)
"""

from __future__ import annotations

import unittest

from prometheus_client import CollectorRegistry

from backend.app.core.metrics import MetricsRegistry


class TestMetricsRegistryUnit(unittest.TestCase):
    """Tests Prometheus metric collectors, sliding-window KPI computations, and text export."""

    def setUp(self) -> None:
        # Create an isolated CollectorRegistry for deterministic testing
        self.registry = CollectorRegistry(auto_describe=True)
        self.metrics = MetricsRegistry(registry=self.registry)

    def test_record_request_increments_counters_and_histograms(self) -> None:
        """Verifies HTTP request recording updates Prometheus counters and latency distributions."""
        self.metrics.record_request(
            method="GET",
            handler="/api/v1/documents",
            status_code=200,
            duration_seconds=0.045,
        )
        self.metrics.record_request(
            method="POST",
            handler="/api/v1/documents/upload",
            status_code=202,
            duration_seconds=0.120,
        )
        self.metrics.record_request(
            method="GET",
            handler="/api/v1/documents",
            status_code=500,
            duration_seconds=0.350,
        )

        # Generate exposition text
        text_output, content_type = self.metrics.generate_prometheus_text()
        decoded = text_output.decode("utf-8")

        self.assertIn("text/plain", content_type)
        self.assertIn("# HELP http_requests_total", decoded)
        self.assertIn("# TYPE http_requests_total counter", decoded)
        self.assertIn('http_requests_total{handler="/api/v1/documents",method="GET",status="200"} 1.0', decoded)
        self.assertIn('http_requests_total{handler="/api/v1/documents/upload",method="POST",status="202"} 1.0', decoded)
        self.assertIn('http_requests_total{handler="/api/v1/documents",method="GET",status="500"} 1.0', decoded)
        self.assertIn("# HELP http_request_duration_seconds", decoded)

    def test_concurrency_gauge_tracking(self) -> None:
        """Verifies in-flight request gauge increments and decrements cleanly."""
        self.metrics.increment_in_progress()
        self.metrics.increment_in_progress()
        val = self.metrics.http_requests_in_progress._value.get()
        self.assertEqual(val, 2.0)

        self.metrics.decrement_in_progress()
        val = self.metrics.http_requests_in_progress._value.get()
        self.assertEqual(val, 1.0)

    def test_database_and_storage_gauges(self) -> None:
        """Verifies pool and volume usage gauges update accurately."""
        self.metrics.set_db_pool_metrics(active=4, size=20)
        self.metrics.set_storage_metrics(used_bytes=104857600, capacity_bytes=1073741824000)

        text_output, _ = self.metrics.generate_prometheus_text()
        decoded = text_output.decode("utf-8")

        self.assertIn("db_pool_active_connections 4.0", decoded)
        self.assertIn("db_pool_size 20.0", decoded)
        self.assertIn("storage_used_bytes", decoded)
        self.assertIn("storage_capacity_bytes", decoded)


    def test_ai_telemetry_counters(self) -> None:
        """Verifies AI token accounting and operation counters."""
        self.metrics.ai_tokens_consumed_total.labels(
            model="gpt-4o",
            operation="rag_query",
            organization_id="org-alpha",
        ).inc(1250)

        self.metrics.ai_operations_total.labels(
            operation="vector_search",
            status="success",
        ).inc(5)

        text_output, _ = self.metrics.generate_prometheus_text()
        decoded = text_output.decode("utf-8")

        self.assertIn('ai_tokens_consumed_total{model="gpt-4o",operation="rag_query",organization_id="org-alpha"} 1250.0', decoded)
        self.assertIn('ai_operations_total{operation="vector_search",status="success"} 5.0', decoded)

    def test_rolling_kpis_calculation(self) -> None:
        """Verifies calculation of rolling p95 latency, RPS, and error percentage."""
        # Record 100 requests (95 fast, 5 slow errors)
        for _ in range(95):
            self.metrics.record_request("GET", "/api/v1/projects", 200, 0.020)  # 20ms
        for _ in range(5):
            self.metrics.record_request("POST", "/api/v1/auth/login", 401, 0.150)  # 150ms

        kpis = self.metrics.get_kpis()

        self.assertTrue(kpis["requests_per_second"] >= 0.0)
        self.assertTrue(kpis["p95_latency_ms"] >= 20.0)
        self.assertEqual(kpis["error_rate_percent"], 5.0)  # 5 errors out of 100 = 5%
        self.assertTrue(kpis["uptime_seconds"] >= 0.0)


if __name__ == "__main__":
    unittest.main()
