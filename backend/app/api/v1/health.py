"""KEEP Enterprise Platform — Health Diagnostics Endpoints."""

from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.health import DetailedHealthResponse, HealthCheckResponse
from backend.app.services.health_service import HealthService
from fastapi import APIRouter, status

router = APIRouter(tags=["Health"])
health_service = HealthService()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Central system health-check",
    description="Returns platform health status, semantic version, and runtime environment.",
)
async def get_health() -> HealthCheckResponse:
    """Returns basic system health status."""
    return await health_service.get_health_status()


@router.get(
    "/health/details",
    response_model=ApiResponse[DetailedHealthResponse],
    status_code=status.HTTP_200_OK,
    summary="Detailed system diagnostics",
    description="Returns uptime and sub-component status indicators for database and cache.",
)
async def get_health_details() -> ApiResponse[DetailedHealthResponse]:
    """Returns detailed diagnostic health check."""
    details = await health_service.get_detailed_health()
    return ApiResponse(
        success=True,
        message="System diagnostic status healthy.",
        data=details,
    )
