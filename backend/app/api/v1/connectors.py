"""KEEP Enterprise Platform — Enterprise Connector Endpoints (`/api/v1/connectors`).

Serves connector registration, authentication, listing, synchronization triggers,
operational health monitoring, and audit log inspection.

Specification: devdocs/p3/p3.1.txt Section 15 & docs/api/api-contract.md Section 13
Author: Member 2 (Backend & Database Lead)
"""

from uuid import UUID

from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.api.dependencies.authorization import require_permission
from backend.app.api.dependencies.database import get_db
from backend.app.schemas.connector import (
    ConnectorAuthenticateRequest,
    ConnectorAuthenticateResponse,
    ConnectorListResponse,
    ConnectorLogsResponse,
    ConnectorRegisterRequest,
    ConnectorRegisterResponse,
    ConnectorRemoveResponse,
    ConnectorStatusResponse,
    ConnectorSyncRequest,
    ConnectorSyncResponse,
)
from backend.app.schemas.envelope import ApiResponse
from backend.app.services.connectors.service import EnterpriseConnectorService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/connectors", tags=["Connectors"])
connector_service = EnterpriseConnectorService()


@router.post(
    "/register",
    response_model=ApiResponse[ConnectorRegisterResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new external connector",
    description="Registers an external platform connector instance with configuration settings.",
)
async def register_connector(
    req: ConnectorRegisterRequest,
    current_user: AuthenticatedUser = Depends(require_permission("connector.manage")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ConnectorRegisterResponse]:
    """Registers an external SaaS connector configuration."""
    data = await connector_service.register_connector(
        db=db,
        organization_id=current_user.organization_id,
        req=req,
    )
    return ApiResponse(
        success=True,
        message="Connector registered successfully.",
        data=data,
    )


@router.post(
    "/authenticate",
    response_model=ApiResponse[ConnectorAuthenticateResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate external platform connector",
    description="Validates and securely encrypts access credentials for a registered connector.",
)
async def authenticate_connector(
    req: ConnectorAuthenticateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("connector.manage")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ConnectorAuthenticateResponse]:
    """Authenticates a registered connector instance."""
    data = await connector_service.authenticate_connector(
        db=db,
        organization_id=current_user.organization_id,
        req=req,
    )
    return ApiResponse(
        success=True,
        message="Connector authenticated successfully.",
        data=data,
    )


@router.get(
    "/list",
    response_model=ApiResponse[ConnectorListResponse],
    status_code=status.HTTP_200_OK,
    summary="List all registered connectors",
    description="Retrieves a list of configured external connectors for the active organization.",
)
async def list_connectors(
    platform_category: str | None = Query(None, description="Optional platform category filter"),
    status_filter: str | None = Query(None, alias="status", description="Optional connector status filter"),
    current_user: AuthenticatedUser = Depends(require_permission("connector.view")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ConnectorListResponse]:
    """Lists configured connectors for the tenant."""
    data = await connector_service.list_connectors(
        db=db,
        organization_id=current_user.organization_id,
        platform_category=platform_category,
        status_filter=status_filter,
    )
    return ApiResponse(
        success=True,
        message="Connectors retrieved successfully.",
        data=data,
    )


@router.post(
    "/sync",
    response_model=ApiResponse[ConnectorSyncResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start connector synchronization",
    description="Triggers a full or incremental synchronization job for a registered connector.",
)
async def start_sync(
    req: ConnectorSyncRequest,
    current_user: AuthenticatedUser = Depends(require_permission("connector.manage")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ConnectorSyncResponse]:
    """Triggers synchronization batch for an external connector."""
    data = await connector_service.start_sync(
        db=db,
        organization_id=current_user.organization_id,
        req=req,
    )
    return ApiResponse(
        success=True,
        message="Synchronization job started successfully.",
        data=data,
    )


@router.get(
    "/status/{id}",
    response_model=ApiResponse[ConnectorStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Get connector operational status",
    description="Retrieves operational health indicators, telemetry, and active sync status.",
)
async def get_connector_status(
    id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("connector.view")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ConnectorStatusResponse]:
    """Retrieves operational telemetry for a connector."""
    data = await connector_service.get_connector_status(
        db=db,
        organization_id=current_user.organization_id,
        connector_id=id,
    )
    return ApiResponse(
        success=True,
        message="Connector status retrieved successfully.",
        data=data,
    )


@router.delete(
    "/remove/{id}",
    response_model=ApiResponse[ConnectorRemoveResponse],
    status_code=status.HTTP_200_OK,
    summary="Remove a connector",
    description="Deregisters and deletes a connector instance and its associated sync logs.",
)
async def remove_connector(
    id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("connector.manage")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ConnectorRemoveResponse]:
    """Removes a registered connector."""
    data = await connector_service.remove_connector(
        db=db,
        organization_id=current_user.organization_id,
        connector_id=id,
    )
    return ApiResponse(
        success=True,
        message="Connector removed successfully.",
        data=data,
    )


@router.get(
    "/logs",
    response_model=ApiResponse[ConnectorLogsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get synchronization audit logs",
    description="Retrieves historical synchronization execution logs with optional filtering.",
)
async def get_sync_logs(
    connector_id: UUID | None = Query(None, description="Optional connector filter"),
    limit: int = Query(50, ge=1, le=200, description="Max logs to return"),
    status_filter: str | None = Query(None, alias="status", description="Optional status filter"),
    current_user: AuthenticatedUser = Depends(require_permission("connector.view")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ConnectorLogsResponse]:
    """Queries synchronization execution logs."""
    data = await connector_service.get_sync_logs(
        db=db,
        organization_id=current_user.organization_id,
        connector_id=connector_id,
        limit=limit,
        status_filter=status_filter,
    )
    return ApiResponse(
        success=True,
        message="Connector logs retrieved successfully.",
        data=data,
    )
