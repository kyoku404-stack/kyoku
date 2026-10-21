"""KEEP Enterprise Platform — Operational Telemetry & System Metrics Endpoint (`/api/v1/metrics`).

Specification Source: devdocs/p1/p1.9.txt (Chapter 8, 9) & docs/API/api-contract.md Section 6.8
Phase: 1.9 — Logging, Monitoring & System Observability
Role: Member 2 (Backend & Database Lead)
"""

from __future__ import annotations

from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.api.dependencies.authorization import require_permission
from backend.app.api.dependencies.database import get_db
from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.health import MetricsSummaryData
from backend.app.services.health_service import HealthService
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/metrics", tags=["Observability & Metrics"])
health_service = HealthService()


@router.get(
    "/summary",
    response_model=ApiResponse[MetricsSummaryData],
    status_code=status.HTTP_200_OK,
    summary="Get aggregated operational telemetry and KPI summary",
    description="Returns high-level system KPIs, rolling error rates, p95 latency, storage utilization, and subsystem alert statuses for frontend dashboards.",
)
async def get_metrics_summary(
    current_user: AuthenticatedUser = Depends(require_permission("audit.read")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[MetricsSummaryData]:
    """Returns aggregated platform metrics summary for authorized administrators."""
    data = await health_service.get_metrics_summary(db)
    return ApiResponse(
        success=True,
        message="System telemetry summary retrieved successfully.",
        data=data,
    )
