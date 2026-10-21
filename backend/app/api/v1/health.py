"""KEEP Enterprise Platform — Health Diagnostics & Probes Endpoints (`/health` & `/api/v1/health`).

Specification Source: devdocs/p1/p1.9.txt (Chapter 7) & docs/API/api-contract.md Section 6
Phase: 1.9 — Logging, Monitoring & System Observability
Role: Member 2 (Backend & Database Lead)
"""

from __future__ import annotations

from backend.app.api.dependencies.database import get_db
from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.health import (
    ApiHealthResponse,
    AuthHealthResponse,
    DatabaseHealthResponse,
    DetailedHealthResponse,
    HealthCheckResponse,
    StorageHealthResponse,
)
from backend.app.services.health_service import HealthService
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Health"])
health_service = HealthService()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Composite platform operational readiness probe",
    description="Aggregates database, storage, process runtime, and auth subsystems into a unified platform health assessment.",
    responses={
        200: {"description": "Platform is fully operational or degraded with non-critical alerts."},
        503: {"description": "One or more critical dependencies (database/storage) are offline."},
    },
)
async def get_health(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> HealthCheckResponse:
    """Returns composite platform health probe."""
    result, code = await health_service.check_composite(db)
    response.status_code = code
    return result


@router.get(
    "/health/database",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Isolated database connectivity & pgvector probe",
    description="Validates PostgreSQL connection pool, ping round-trip latency, and pgvector extension readiness.",
    responses={
        200: {"description": "Database is connected and operational."},
        503: {"description": "Database connection failed or timed out."},
    },
)
async def get_health_database(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> DatabaseHealthResponse:
    """Returns database dependency health status."""
    result, code = await health_service.check_database(db)
    response.status_code = code
    return result


@router.get(
    "/health/storage",
    response_model=StorageHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Isolated storage filesystem probe",
    description="Validates storage volume write/read permissions, latency, and disk capacity headroom.",
    responses={
        200: {"description": "Storage filesystem is writable and within capacity limits."},
        503: {"description": "Storage is unwritable or exceeds critical 95% capacity threshold."},
    },
)
async def get_health_storage(
    response: Response,
) -> StorageHealthResponse:
    """Returns storage filesystem dependency health status."""
    result, code = await health_service.check_storage()
    response.status_code = code
    return result


@router.get(
    "/health/api",
    response_model=ApiHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Isolated API gateway process runtime probe",
    description="Inspects process uptime, memory RSS, CPU utilization, and concurrent active requests.",
)
async def get_health_api() -> ApiHealthResponse:
    """Returns API gateway runtime health status."""
    result, _ = health_service.check_api()
    return result


@router.get(
    "/health/auth",
    response_model=AuthHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Authentication readiness probe",
    description="Validates cryptographic key configuration, signing algorithm, and token lifecycle parameters.",
)
async def get_health_auth() -> AuthHealthResponse:
    """Returns authentication configuration status."""
    result, _ = health_service.check_auth()
    return result


# Backwards compatibility endpoint for Phase 1.1/1.2 test suites
@router.get(
    "/health/details",
    response_model=ApiResponse[DetailedHealthResponse],
    status_code=status.HTTP_200_OK,
    summary="Detailed system diagnostics (legacy)",
    description="Returns uptime and sub-component status indicators in legacy ApiResponse format.",
)
async def get_health_details() -> ApiResponse[DetailedHealthResponse]:
    """Returns legacy detailed diagnostic health check."""
    details = await health_service.get_detailed_health()
    return ApiResponse(
        success=True,
        message="System diagnostic status healthy.",
        data=details,
    )
