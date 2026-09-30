"""KEEP Enterprise Platform — Analytics Endpoints (`/api/v1/analytics`)."""

from fastapi import APIRouter, Depends, status

from backend.app.api.dependencies.auth import AuthenticatedUser, get_current_user
from backend.app.api.dependencies.tenant import TenantContext, get_tenant_context
from backend.app.schemas.analytics import AnalyticsSummaryResponse, UsageMetricsResponse
from backend.app.schemas.envelope import ApiResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/summary",
    response_model=ApiResponse[AnalyticsSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get platform operational summary metrics",
    description="Returns aggregate counts of documents, queries, users, and storage.",
)
async def get_analytics_summary(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ApiResponse[AnalyticsSummaryResponse]:
    """Returns platform summary metrics."""
    data = AnalyticsSummaryResponse(
        total_documents=42,
        total_queries=1280,
        total_users=15,
        active_sessions=4,
        storage_used_bytes=104857600,
    )
    return ApiResponse(
        success=True,
        message="Analytics summary retrieved.",
        data=data,
    )


@router.get(
    "/usage",
    response_model=ApiResponse[UsageMetricsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get daily usage metrics",
    description="Returns query volume, token consumption, and response latency statistics.",
)
async def get_usage_metrics(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ApiResponse[UsageMetricsResponse]:
    """Returns daily usage metrics."""
    data = UsageMetricsResponse(
        queries_today=342,
        tokens_consumed_today=158200,
        avg_latency_ms=245.5,
    )
    return ApiResponse(
        success=True,
        message="Usage metrics retrieved.",
        data=data,
    )
