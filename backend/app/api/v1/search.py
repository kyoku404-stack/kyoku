"""KEEP Enterprise Platform — Search Endpoints (`/api/v1/search`).

Provides global multi-entity text search and hybrid semantic keyword retrieval.
Derived from devdocs/p1/p1.7.txt and docs/API/api-contract.md Section 5.8.
"""

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
)
from backend.app.api.dependencies.authorization import require_permission
from backend.app.api.dependencies.database import get_db
from backend.app.api.dependencies.tenant import TenantContext, get_tenant_context
from backend.app.schemas.dashboard import GlobalSearchResponse
from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.search import HybridSearchRequest, SearchResponse
from backend.app.services.dashboard_service import DashboardService
from backend.app.services.search_service import SearchService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/search", tags=["Search"])
search_service = SearchService()
dashboard_service = DashboardService()


@router.get(
    "",
    response_model=ApiResponse[GlobalSearchResponse],
    status_code=status.HTTP_200_OK,
    summary="Global organization full-text search",
    description="Full-text search across projects, documents, users, and teams within the authenticated user's organization.",
)
async def global_search(
    q: str = Query(..., min_length=1, description="Search query string"),
    search_type: str = Query(
        default="all",
        alias="type",
        description="Filter by type: all, project, document, user, team",
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=20, description="Results per page (max 20)"),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[GlobalSearchResponse]:
    """Performs multi-entity full-text search."""
    results = await dashboard_service.global_search(
        db=db,
        current_user=current_user,
        query=q,
        search_type=search_type,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(
        success=True,
        message="Search completed successfully.",
        data=results,
    )


@router.post(
    "/hybrid",
    response_model=ApiResponse[SearchResponse],
    status_code=status.HTTP_200_OK,
    summary="Hybrid semantic + BM25 keyword search",
    description="Executes hybrid retrieval combining dense vector similarity with sparse keyword matching.",
)
async def hybrid_search(
    request: HybridSearchRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(require_permission("ai.search")),
) -> ApiResponse[SearchResponse]:
    """Executes search and returns standardized response envelope."""
    results = await search_service.hybrid_search(
        request=request,
        org_id=tenant.organization_id,
    )
    return ApiResponse(
        success=True,
        message="Search executed successfully.",
        data=results,
    )
