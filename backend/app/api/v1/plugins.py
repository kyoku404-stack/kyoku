"""KEEP Enterprise Platform — Plugin SDK, Extension Framework & Developer Ecosystem Endpoints.

Phase: 3.5
Owner: Member 2 (Backend & Database Lead)
Domain: /backend/app/api/v1/plugins.py
Specification: devdocs/p3/p3.5.txt & docs/api/api-contract.md (Section 17)
"""

from typing import Any

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
)
from backend.app.api.dependencies.database import get_db
from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.plugin import (
    PluginAnalyticsResponse,
    PluginConfigUpdateRequest,
    PluginExecuteRequest,
    PluginExecutionLogResponse,
    PluginExecutionResponse,
    PluginInstallRequest,
    PluginItemResponse,
    PluginMarketplaceItemResponse,
    PluginPublishRequest,
    PluginStatusToggleRequest,
    PluginUninstallRequest,
    PluginUpdateRequest,
)
from backend.app.services.plugins.service import EnterprisePluginService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/plugins", tags=["Plugins & Extensions"])
plugin_service = EnterprisePluginService()


# ============================================================================
# Marketplace Endpoints
# ============================================================================


@router.get(
    "/marketplace",
    response_model=ApiResponse[list[PluginMarketplaceItemResponse]],
    status_code=status.HTTP_200_OK,
    summary="Browse Plugin Marketplace Catalog",
)
async def browse_marketplace(
    search: str | None = Query(None, description="Search by name, description or developer"),
    category: str | None = Query(None, description="Category filter (AI, INTEGRATION, etc)"),
    verified_only: bool = Query(False, description="Filter for VERIFIED and CERTIFIED only"),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[PluginMarketplaceItemResponse]]:
    """Query marketplace catalog with verified badges and install status for caller's organization."""
    catalog = await plugin_service.browse_marketplace(
        db=db,
        org_id=current_user.organization_id,
        search=search,
        category=category,
        verified_only=verified_only,
    )
    return ApiResponse(
        success=True,
        message="Marketplace catalog retrieved successfully.",
        data=[PluginMarketplaceItemResponse.model_validate(item) for item in catalog],
    )


@router.post(
    "/marketplace/publish",
    response_model=ApiResponse[dict[str, Any]],
    status_code=status.HTTP_201_CREATED,
    summary="Publish Plugin to Marketplace",
)
async def publish_marketplace_plugin(
    payload: PluginPublishRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    """Register or update a plugin manifest in the global marketplace catalog."""
    result = await plugin_service.publish_marketplace_plugin(
        db=db,
        user_id=current_user.id,
        payload=payload,
    )
    return ApiResponse(
        success=True,
        message=f"Plugin '{payload.name}' published successfully.",
        data=result,
    )


# ============================================================================
# Lifecycle Endpoints
# ============================================================================


@router.post(
    "/install",
    response_model=ApiResponse[PluginItemResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Install Plugin into Organization",
)
async def install_plugin(
    payload: PluginInstallRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PluginItemResponse]:
    """Install and configure a plugin for the tenant organization."""
    installed = await plugin_service.install_plugin(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        payload=payload,
    )
    return ApiResponse(
        success=True,
        message=f"Plugin '{payload.plugin_id}' installed successfully.",
        data=PluginItemResponse.model_validate(installed),
    )


@router.get(
    "/list",
    response_model=ApiResponse[list[PluginItemResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Installed Plugins",
)
async def list_installed_plugins(
    category: str | None = Query(None, description="Category filter"),
    status_filter: str | None = Query(None, alias="status", description="Status filter"),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[PluginItemResponse]]:
    """Retrieve all installed plugins configured for the caller's organization."""
    items = await plugin_service.list_installed_plugins(
        db=db,
        org_id=current_user.organization_id,
        category=category,
        status_filter=status_filter,
    )
    return ApiResponse(
        success=True,
        message="Installed plugins retrieved successfully.",
        data=[PluginItemResponse.model_validate(item) for item in items],
    )


@router.post(
    "/enable",
    response_model=ApiResponse[PluginItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Enable Plugin",
)
async def enable_plugin(
    payload: PluginStatusToggleRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PluginItemResponse]:
    """Activate an installed plugin in the organization."""
    updated = await plugin_service.enable_plugin(
        db=db,
        org_id=current_user.organization_id,
        plugin_id=payload.plugin_id,
    )
    return ApiResponse(
        success=True,
        message=f"Plugin '{payload.plugin_id}' activated successfully.",
        data=PluginItemResponse.model_validate(updated),
    )


@router.post(
    "/disable",
    response_model=ApiResponse[PluginItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Disable Plugin",
)
async def disable_plugin(
    payload: PluginStatusToggleRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PluginItemResponse]:
    """Deactivate an installed plugin in the organization."""
    updated = await plugin_service.disable_plugin(
        db=db,
        org_id=current_user.organization_id,
        plugin_id=payload.plugin_id,
    )
    return ApiResponse(
        success=True,
        message=f"Plugin '{payload.plugin_id}' deactivated successfully.",
        data=PluginItemResponse.model_validate(updated),
    )


@router.post(
    "/update",
    response_model=ApiResponse[PluginItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Update Plugin Version",
)
async def update_plugin_version(
    payload: PluginUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PluginItemResponse]:
    """Upgrade or downgrade installed plugin version."""
    updated = await plugin_service.update_plugin_version(
        db=db,
        org_id=current_user.organization_id,
        payload=payload,
    )
    return ApiResponse(
        success=True,
        message=f"Plugin '{payload.plugin_id}' updated to version '{payload.target_version}'.",
        data=PluginItemResponse.model_validate(updated),
    )


@router.post(
    "/uninstall",
    response_model=ApiResponse[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Uninstall Plugin",
)
async def uninstall_plugin(
    payload: PluginUninstallRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    """Remove a plugin installation and optionally purge all associated telemetry logs."""
    result = await plugin_service.uninstall_plugin(
        db=db,
        org_id=current_user.organization_id,
        plugin_id=payload.plugin_id,
        purge_data=payload.purge_data,
    )
    return ApiResponse(
        success=True,
        message=result["message"],
        data=result,
    )


# ============================================================================
# Telemetry & Analytics
# ============================================================================


@router.get(
    "/logs",
    response_model=ApiResponse[list[PluginExecutionLogResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get Plugin Execution Logs",
)
async def get_execution_logs(
    plugin_id: str | None = Query(None, description="Optional plugin ID filter"),
    status_filter: str | None = Query(None, alias="status", description="Status filter"),
    limit: int = Query(50, ge=1, le=200, description="Max logs to return"),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[PluginExecutionLogResponse]]:
    """Retrieve execution history audit trail for the organization's plugins."""
    logs = await plugin_service.list_execution_logs(
        db=db,
        org_id=current_user.organization_id,
        plugin_id=plugin_id,
        status_filter=status_filter,
        limit=limit,
    )
    return ApiResponse(
        success=True,
        message="Plugin execution logs retrieved successfully.",
        data=[PluginExecutionLogResponse.model_validate(log) for log in logs],
    )


@router.get(
    "/analytics",
    response_model=ApiResponse[PluginAnalyticsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Plugin Operational Analytics",
)
async def get_plugin_analytics(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PluginAnalyticsResponse]:
    """Retrieve operational KPIs, error rates, average latency and category breakdown."""
    analytics = await plugin_service.get_plugin_analytics(
        db=db,
        org_id=current_user.organization_id,
    )
    return ApiResponse(
        success=True,
        message="Plugin analytics retrieved successfully.",
        data=PluginAnalyticsResponse.model_validate(analytics),
    )


# ============================================================================
# Specific Plugin Endpoints
# ============================================================================


@router.get(
    "/{plugin_id}",
    response_model=ApiResponse[PluginItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Plugin Details",
)
async def get_plugin(
    plugin_id: str,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PluginItemResponse]:
    """Retrieve full configuration and status details for an installed plugin."""
    plugin = await plugin_service.get_plugin(
        db=db,
        org_id=current_user.organization_id,
        plugin_id=plugin_id,
    )
    return ApiResponse(
        success=True,
        message="Plugin details retrieved successfully.",
        data=PluginItemResponse.model_validate(plugin),
    )


@router.post(
    "/{plugin_id}/config",
    response_model=ApiResponse[PluginItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Update Plugin Configuration",
)
async def update_plugin_config(
    plugin_id: str,
    payload: PluginConfigUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PluginItemResponse]:
    """Update runtime configuration settings for an installed plugin."""
    updated = await plugin_service.update_plugin_configuration(
        db=db,
        org_id=current_user.organization_id,
        plugin_id=plugin_id,
        payload=payload,
    )
    return ApiResponse(
        success=True,
        message=f"Configuration for plugin '{plugin_id}' updated successfully.",
        data=PluginItemResponse.model_validate(updated),
    )


@router.post(
    "/{plugin_id}/execute",
    response_model=ApiResponse[PluginExecutionResponse],
    status_code=status.HTTP_200_OK,
    summary="Execute Plugin Action",
)
async def execute_plugin_action(
    plugin_id: str,
    payload: PluginExecuteRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PluginExecutionResponse]:
    """Execute a capability action within a sandboxed runtime environment."""
    execution = await plugin_service.execute_plugin_action(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        plugin_id=plugin_id,
        payload=payload,
    )
    return ApiResponse(
        success=True,
        message=f"Action '{payload.action}' executed successfully.",
        data=PluginExecutionResponse.model_validate(execution),
    )
