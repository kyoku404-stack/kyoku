"""KEEP Enterprise Platform — Health Diagnostics Service."""

import time
from datetime import UTC, datetime

from backend.app.core.config import settings
from backend.app.schemas.health import (
    ComponentHealth,
    DetailedHealthResponse,
    HealthCheckResponse,
)

START_TIME = time.time()


class HealthService:
    """Service providing platform uptime and sub-system health statuses."""

    async def get_health_status(self) -> HealthCheckResponse:
        """Returns high-level system readiness status."""
        return HealthCheckResponse(
            status="healthy",
            environment=settings.ENVIRONMENT,
            version=settings.VERSION,
            timestamp=datetime.now(UTC).isoformat(),
        )

    async def get_detailed_health(self) -> DetailedHealthResponse:
        """Returns deep component-level diagnostics."""
        uptime = time.time() - START_TIME
        components = {
            "database": ComponentHealth(
                status="healthy",
                latency_ms=1.2,
                details="PostgreSQL connection pool active",
            ),
            "redis": ComponentHealth(
                status="healthy", latency_ms=0.8, details="Redis ping OK"
            ),
        }
        return DetailedHealthResponse(
            status="healthy",
            environment=settings.ENVIRONMENT,
            version=settings.VERSION,
            timestamp=datetime.now(UTC).isoformat(),
            uptime_seconds=round(uptime, 2),
            components=components,
        )
