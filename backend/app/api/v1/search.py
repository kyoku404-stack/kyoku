"""KEEP Enterprise Platform — Search Endpoints (`/api/v1/search`)."""

from fastapi import APIRouter, Depends, status

from backend.app.api.dependencies.auth import AuthenticatedUser, get_current_user
from backend.app.api.dependencies.tenant import TenantContext, get_tenant_context
from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.search import HybridSearchRequest, SearchResponse
from backend.app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])
search_service = SearchService()


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
    current_user: AuthenticatedUser = Depends(get_current_user),
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
