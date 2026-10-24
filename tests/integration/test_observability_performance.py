"""DevOps Integration Test Suite: Observability Performance, Concurrency & Metric Registry Stress Testing.

Specification Source: devdocs/p1/p1.9.txt (Chapter 16, 17)
Architecture: docs/Architecture/observability-architecture.md
Role: Member 4 (DevOps & Integration Lead)
"""

from __future__ import annotations

import concurrent.futures
import time
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from prometheus_client import CollectorRegistry
from sqlalchemy.orm import Session

from backend.app.core.constants import UserRole
from backend.app.core.logging import JSONLogFormatter
from backend.app.core.metrics import MetricsRegistry
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestObservabilityPerformance(unittest.TestCase):
    """Performance, load benchmark, and concurrency stress testing for the observability stack."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        # Pre-warm client
        cls.client.get("/health")
        cls.client.get("/metrics")

        with Session(sync_test_engine) as session:
            cls.org = Organization(
                name=f"DevOps Perf Org {uuid4().hex[:6]}",
                domain=f"devops_perf_{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.flush()

            cls.admin_user = User(
                email=f"devops_perf_{uuid4().hex[:6]}@enterprise.io",
                hashed_password=get_password_hash("DevOpsPerf2026!"),
                full_name="DevOps Perf Admin",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org.id,
                is_active=True,
            )
            session.add(cls.admin_user)
            session.commit()

            cls.org_id = cls.org.id
            cls.admin_id = cls.admin_user.id

        cls.token_admin = create_access_token(
            data={
                "sub": str(cls.admin_id),
                "email": cls.admin_user.email,
                "role": "OrgAdmin",
                "org_id": str(cls.org_id),
            }
        )
        cls.headers_admin = {"Authorization": f"Bearer {cls.token_admin}"}

    # --------------------------------------------------------------------------
    # 1. High-Concurrency Probe Stress Testing
    # --------------------------------------------------------------------------
    def test_concurrent_health_probe_execution(self) -> None:
        """Executes 50 concurrent health check queries across database, api, and auth probes."""
        endpoints = [
            "/health/database",
            "/health/api",
            "/health/auth",
        ]

        def query_probe(endpoint: str) -> tuple[int, float]:
            t0 = time.perf_counter()
            res = self.client.get(endpoint)
            duration_ms = (time.perf_counter() - t0) * 1000
            return res.status_code, duration_ms

        # Run 50 requests across 10 worker threads
        tasks = [endpoints[i % len(endpoints)] for i in range(50)]
        start_all = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(query_probe, tasks))

        _total_elapsed_ms = (time.perf_counter() - start_all) * 1000

        # Assert all 50 completed with HTTP 200
        for status_code, duration_ms in results:
            self.assertEqual(status_code, 200)
            self.assertLess(duration_ms, 500.0, f"Individual probe latency spiked: {duration_ms:.2f}ms")

        avg_latency = sum(r[1] for r in results) / len(results)
        self.assertLess(avg_latency, 100.0, f"Average concurrent probe latency too high: {avg_latency:.2f}ms")

    # --------------------------------------------------------------------------
    # 2. Prometheus Scrape Throughput Benchmark
    # --------------------------------------------------------------------------
    def test_prometheus_scraping_latency_under_load(self) -> None:
        """Benchmark repeated scrapes of /metrics verifying sub-30ms execution time."""
        latencies = []
        for _ in range(20):
            t0 = time.perf_counter()
            res = self.client.get("/metrics")
            dur = (time.perf_counter() - t0) * 1000
            self.assertEqual(res.status_code, 200)
            latencies.append(dur)

        mean_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        self.assertLess(mean_latency, 30.0, f"Prometheus scrape mean latency exceeded 30ms: {mean_latency:.2f}ms")
        self.assertLess(max_latency, 100.0, f"Prometheus scrape max latency spiked: {max_latency:.2f}ms")

    # --------------------------------------------------------------------------
    # 3. Thread-Safe Metrics Registry Concurrency Benchmark
    # --------------------------------------------------------------------------
    def test_metrics_registry_multithreaded_stress(self) -> None:
        """Validates thread-safe concurrent observations in isolated MetricsRegistry instance."""
        custom_collector = CollectorRegistry(auto_describe=True)
        reg = MetricsRegistry(registry=custom_collector)
        num_threads = 8
        ops_per_thread = 500

        def record_worker() -> None:
            for _i in range(ops_per_thread):
                reg.record_request("GET", "/api/v1/test", 200, 0.025)
                reg.ai_operations_total.labels(operation="llm_completion", status="success").inc()
                reg.set_db_pool_metrics(active=5, size=20)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(record_worker) for _ in range(num_threads)]
            for f in futures:
                f.result()

        # Prometheus export text should generate without deadlocks
        body_bytes, content_type = reg.generate_prometheus_text()
        text_export = body_bytes.decode("utf-8")
        self.assertIn("http_requests_total", text_export)
        self.assertIn("ai_operations_total", text_export)
        self.assertIn("db_pool_active_connections", text_export)

        # KPIs should compute cleanly
        kpis = reg.get_kpis()
        self.assertIn("requests_per_second", kpis)
        self.assertIn("p95_latency_ms", kpis)
        self.assertIn("error_rate_percent", kpis)

    # --------------------------------------------------------------------------
    # 4. Telemetry Summary Endpoint Benchmark
    # --------------------------------------------------------------------------
    def test_metrics_summary_endpoint_benchmark(self) -> None:
        """Benchmarks GET /api/v1/metrics/summary responding within 40ms."""
        latencies = []
        for _ in range(15):
            t0 = time.perf_counter()
            res = self.client.get("/api/v1/metrics/summary", headers=self.headers_admin)
            dur = (time.perf_counter() - t0) * 1000
            self.assertEqual(res.status_code, 200)
            latencies.append(dur)

        mean_dur = sum(latencies) / len(latencies)
        self.assertLess(mean_dur, 40.0, f"Metrics summary mean latency exceeded 40ms: {mean_dur:.2f}ms")

    # --------------------------------------------------------------------------
    # 5. High-Volume Structured Log Serialization Throughput
    # --------------------------------------------------------------------------
    def test_high_volume_log_serialization_throughput(self) -> None:
        """Serializes 1,000 canonical structured JSON log events in under 150ms."""
        import logging

        formatter = JSONLogFormatter()
        logger = logging.getLogger("keep.bench")
        logger.setLevel(logging.INFO)

        records = [
            logging.LogRecord(
                name="keep.bench",
                level=logging.INFO,
                pathname="test.py",
                lineno=100,
                msg=f"Simulated benchmark transaction #{i}",
                args=(),
                exc_info=None,
            )
            for i in range(1000)
        ]

        t0 = time.perf_counter()
        outputs = [formatter.format(rec) for rec in records]
        elapsed_ms = (time.perf_counter() - t0) * 1000

        self.assertEqual(len(outputs), 1000)
        self.assertTrue(outputs[0].startswith("{") and outputs[0].endswith("}"))
        self.assertLess(elapsed_ms, 150.0, f"Log serialization exceeded 150ms: {elapsed_ms:.2f}ms")
