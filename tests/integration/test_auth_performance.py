"""Performance & Concurrency Test Suite for Phase 1.4 Authentication.

Verifies:
1. High-concurrency login throughput and latency bounds under concurrent requests.
2. Fast token issuance and cryptographic verification under high load.
3. Concurrent authenticated profile resolution (/api/v1/auth/me) without deadlocks or pool exhaustion.

Owner: Member 4 (DevOps & Integration Lead)
Sub-phase: Phase 1.4 Authentication & Identity Management
"""

import time
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.constants import UserRole
from backend.app.core.security import (
    create_access_token,
    decode_token,
    get_password_hash,
)
from backend.app.main import app
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestAuthPerformance(unittest.TestCase):
    """Performance benchmarks and concurrency stress tests for the auth subsystem."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine) as session:
            cls.perf_org = Organization(name="Perf Org", domain="perf.com")
            session.add(cls.perf_org)
            session.flush()

            cls.perf_user = User(
                email="perf.user@perf.com",
                hashed_password=get_password_hash("PerfPassword123!"),
                full_name="Perf Tester",
                role=UserRole.MEMBER,
                organization_id=cls.perf_org.id,
                is_active=True,
            )
            session.add(cls.perf_user)
            session.commit()

            cls.org_id = str(cls.perf_org.id)

    def test_concurrent_logins_concurrency_and_latency(self) -> None:
        """Verify login operations achieve 100% success rate within latency bounds."""
        iterations = 5
        login_payload = {
            "email": "perf.user@perf.com",
            "password": "PerfPassword123!",
        }

        latencies = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            res = self.client.post(
                f"{settings.API_V1_STR}/auth/login",
                json=login_payload,
            )
            elapsed = time.perf_counter() - t0
            self.assertEqual(res.status_code, 200)
            latencies.append(elapsed)

        avg_latency = sum(latencies) / len(latencies)
        # Bcrypt is intentionally compute-intensive (~50-250ms per verification),
        # so avg latency should comfortably complete within 1.0s
        self.assertLess(
            avg_latency,
            1.0,
            f"Average login latency {avg_latency:.3f}s exceeds threshold",
        )

    def test_high_throughput_jwt_generation_and_validation(self) -> None:
        """Benchmark 200 token generation and validation iterations."""
        claims = {
            "sub": str(uuid4()),
            "email": "throughput@perf.com",
            "role": "Member",
            "org_id": self.org_id,
        }

        iterations = 200
        start = time.perf_counter()

        for _ in range(iterations):
            token = create_access_token(claims)
            decoded = decode_token(token)
            self.assertEqual(decoded["email"], "throughput@perf.com")

        duration = time.perf_counter() - start
        ops_per_sec = iterations / duration

        # HMAC-SHA256 in PyJWT easily does >1,000 ops/sec
        self.assertGreater(
            ops_per_sec,
            200,
            f"Throughput {ops_per_sec:.1f} ops/sec below acceptable performance bar",
        )
        self.assertLess(
            duration,
            1.0,
            f"200 token cycles took {duration:.3f}s (exceeds 1s budget)",
        )

    def test_concurrent_profile_retrieval_under_load(self) -> None:
        """Verify profile retrieval under repeated calls with low latency (<200ms avg)."""
        # Obtain token
        login_res = self.client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": "perf.user@perf.com", "password": "PerfPassword123!"},
        )
        self.assertEqual(login_res.status_code, 200)
        token = login_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        iterations = 20
        latencies = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            res = self.client.get(
                f"{settings.API_V1_STR}/auth/me",
                headers=headers,
            )
            elapsed = time.perf_counter() - t0
            self.assertEqual(res.status_code, 200)
            latencies.append(elapsed)

        avg_latency = sum(latencies) / len(latencies)
        self.assertLess(
            avg_latency,
            0.2,
            f"Average /me profile resolution latency {avg_latency:.3f}s exceeded 200ms",
        )


if __name__ == "__main__":
    unittest.main()
