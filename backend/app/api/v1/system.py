"""KEEP Enterprise Platform — Production Infrastructure & System Operations Endpoints.

Specification Source: devdocs/p3/p3.6.txt (Chapter 16) & docs/api/api-contract.md (Section 18)
Phase: 3.6 — Production Infrastructure, Scalability, Observability & High Availability
Role: Member 2 (Backend & Database Lead)
"""

from __future__ import annotations

from backend.app.api.dependencies.auth import AuthenticatedUser, get_current_user
from backend.app.api.dependencies.authorization import require_permission
from backend.app.api.dependencies.database import get_db
from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.infrastructure import (
    CacheFlushData,
    CacheFlushRequest,
    CreateBackupData,
    CreateBackupRequest,
    DeployTriggerData,
    DeployTriggerRequest,
    MicroserviceStatusData,
    SystemBackupsData,
    SystemHealthData,
    SystemLogEntryData,
    SystemMetricsData,
    SystemVersionData,
)
from backend.app.services.infrastructure.service import EnterpriseInfrastructureService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/system", tags=["System Operations & Infrastructure"])
infrastructure_service = EnterpriseInfrastructureService()


# ============================================================================
# 1. System Health Probes
# ============================================================================

@router.get(
    "/health",
    response_model=ApiResponse[SystemHealthData],
    status_code=status.HTTP_200_OK,
    summary="Get comprehensive platform and subsystem health status",
    description="Inspects database, cache cluster, vector store, object storage, and AI worker dependencies.",
)
async def get_system_health(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[SystemHealthData]:
    """Returns composite platform health probe and component diagnostic metrics."""
    data = await infrastructure_service.get_system_health(db)
    return ApiResponse(
        success=True,
        message="System health probe completed successfully.",
        data=data,
    )


# ============================================================================
# 2. Performance Metrics Telemetry
# ============================================================================

@router.get(
    "/metrics",
    response_model=ApiResponse[SystemMetricsData],
    status_code=status.HTTP_200_OK,
    summary="Get real-time operational telemetry and performance metrics",
    description="Captures CPU, memory, disk, network, application throughput, and cache efficiency metrics.",
)
async def get_system_metrics(
    current_user: AuthenticatedUser = Depends(require_permission("system.view")),
) -> ApiResponse[SystemMetricsData]:
    """Returns real-time server and platform performance telemetry."""
    data = infrastructure_service.get_system_metrics()
    return ApiResponse(
        success=True,
        message="System metrics retrieved successfully.",
        data=data,
    )


# ============================================================================
# 3. Centralized System Logs
# ============================================================================

@router.get(
    "/logs",
    response_model=ApiResponse[list[SystemLogEntryData]],
    status_code=status.HTTP_200_OK,
    summary="Query centralized system diagnostic and audit logs",
    description="Retrieves structured operational logs filtered by service, severity, query, and limit.",
)
async def get_system_logs(
    service_name: str | None = Query(None, description="Filter by microservice name"),
    severity: str | None = Query(None, description="Filter by severity (INFO, WARN, ERROR, FATAL)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum log records to return"),
    query: str | None = Query(None, description="Substring search query for log messages"),
    current_user: AuthenticatedUser = Depends(require_permission("system.view")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[SystemLogEntryData]]:
    """Returns centralized operational log entries."""
    data = await infrastructure_service.get_system_logs(
        db,
        service_name=service_name,
        severity=severity,
        limit=limit,
        query=query,
    )
    return ApiResponse(
        success=True,
        message="System logs retrieved successfully.",
        data=data,
    )


# ============================================================================
# 4. Deployment Triggering
# ============================================================================

@router.post(
    "/deploy",
    response_model=ApiResponse[DeployTriggerData],
    status_code=status.HTTP_200_OK,
    summary="Trigger a containerized service deployment",
    description="Dispatches a rolling, blue-green, or canary deployment with automated rollback safeguards.",
)
async def trigger_deploy(
    payload: DeployTriggerRequest,
    current_user: AuthenticatedUser = Depends(require_permission("system.deploy")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DeployTriggerData]:
    """Triggers an automated service deployment workflow."""
    data = await infrastructure_service.trigger_deployment(
        db,
        request=payload,
        user_id=current_user.id if current_user else None,
    )
    return ApiResponse(
        success=True,
        message="Deployment initiated successfully.",
        data=data,
    )


# ============================================================================
# 5. Version & Microservices Status
# ============================================================================

@router.get(
    "/version",
    response_model=ApiResponse[SystemVersionData],
    status_code=status.HTTP_200_OK,
    summary="Get active system release and version information",
    description="Returns platform semantic version, git commit hash, environment, and framework versions.",
)
async def get_system_version(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ApiResponse[SystemVersionData]:
    """Returns active platform version and runtime metadata."""
    data = infrastructure_service.get_system_version()
    return ApiResponse(
        success=True,
        message="System version information retrieved.",
        data=data,
    )


@router.get(
    "/status",
    response_model=ApiResponse[list[MicroserviceStatusData]],
    status_code=status.HTTP_200_OK,
    summary="Get operational matrix and status of all microservices",
    description="Returns healthy replicas, memory, CPU, and uptime per containerized service.",
)
async def get_system_status(
    current_user: AuthenticatedUser = Depends(require_permission("system.view")),
) -> ApiResponse[list[MicroserviceStatusData]]:
    """Returns microservice operational status matrix."""
    data = infrastructure_service.get_services_status()
    return ApiResponse(
        success=True,
        message="Microservice status matrix retrieved successfully.",
        data=data,
    )


# ============================================================================
# 6. Disaster Recovery & Backups
# ============================================================================

@router.get(
    "/backups",
    response_model=ApiResponse[SystemBackupsData],
    status_code=status.HTTP_200_OK,
    summary="Get disaster recovery backup catalog and SLA compliance metrics",
    description="Lists automated snapshots, verification status, and RPO drift.",
)
async def get_system_backups(
    current_user: AuthenticatedUser = Depends(require_permission("system.view")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[SystemBackupsData]:
    """Returns disaster recovery backup inventory and RPO/RTO metrics."""
    data = await infrastructure_service.get_system_backups(db)
    return ApiResponse(
        success=True,
        message="Disaster recovery backup inventory retrieved successfully.",
        data=data,
    )


@router.post(
    "/backups/create",
    response_model=ApiResponse[CreateBackupData],
    status_code=status.HTTP_201_CREATED,
    summary="Trigger an immediate point-in-time disaster recovery backup snapshot",
    description="Creates a verified database or full system backup snapshot.",
)
async def create_system_backup(
    payload: CreateBackupRequest,
    current_user: AuthenticatedUser = Depends(require_permission("system.backup")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CreateBackupData]:
    """Creates a new point-in-time backup snapshot."""
    data = await infrastructure_service.create_backup(db, request=payload)
    return ApiResponse(
        success=True,
        message="Manual backup snapshot created successfully.",
        data=data,
    )


# ============================================================================
# 7. Cache Administration
# ============================================================================

@router.post(
    "/cache/flush",
    response_model=ApiResponse[CacheFlushData],
    status_code=status.HTTP_200_OK,
    summary="Flush designated Redis cache namespaces",
    description="Selectively purges cache namespaces or invalidates the entire distributed cache cluster.",
)
async def flush_system_cache(
    payload: CacheFlushRequest,
    current_user: AuthenticatedUser = Depends(require_permission("system.manage")),
) -> ApiResponse[CacheFlushData]:
    """Flushes target cache namespaces."""
    data = infrastructure_service.flush_cache(payload)
    return ApiResponse(
        success=True,
        message="Target cache namespaces flushed successfully.",
        data=data,
    )
