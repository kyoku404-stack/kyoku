"""KEEP Enterprise Platform — Knowledge Graph & Enterprise Intelligence API Router (Phase 2.4).

Exposes RESTful endpoints for constructing knowledge graphs, incremental extraction,
multi-hop graph queries, interactive explorer topology, subject-matter expertise discovery,
and recursive downstream impact analysis.
Specification: docs/API/api-contract.md Section 11 & devdocs/p2/p2.4.txt.
Owner: Member 2 (Backend & Database Lead)
"""

from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
)
from backend.app.api.dependencies.authorization import require_permission
from backend.app.api.dependencies.database import get_db
from backend.app.api.dependencies.tenant import TenantContext, get_tenant_context
from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.graph import (
    EntityRelationshipsResponse,
    EntityResponse,
    ExpertiseResponse,
    GraphBuildRequest,
    GraphBuildResponse,
    GraphExplorerResponse,
    GraphQueryRequest,
    GraphQueryResponse,
    GraphUpdateRequest,
    GraphUpdateResponse,
    ImpactAnalysisResponse,
)
from backend.app.services.ai.interfaces import AIPermission
from backend.app.services.graph.service import KnowledgeGraphService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/graph", tags=["Knowledge Graph & Enterprise Intelligence"])
graph_service = KnowledgeGraphService()


@router.post(
    "/build",
    response_model=ApiResponse[GraphBuildResponse],
    status_code=status.HTTP_200_OK,
    summary="Build knowledge graph",
    description="Constructs or rebuilds the enterprise knowledge graph from organizational records and document chunks.",
)
async def build_knowledge_graph(
    request: GraphBuildRequest,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.GRAPH_BUILD)),
) -> ApiResponse[GraphBuildResponse]:
    """Triggers knowledge graph construction."""
    result = await db.run_sync(
        lambda sync_session: graph_service.build_graph(
            db=sync_session,
            organization_id=tenant.organization_id,
            rebuild_all=request.rebuild_all,
            confidence_threshold=request.confidence_threshold,
            include_documents=request.include_documents,
            include_organizational=request.include_organizational,
        )
    )
    return ApiResponse(
        success=True,
        message="Knowledge graph build completed successfully.",
        data=result,
    )


@router.post(
    "/update",
    response_model=ApiResponse[GraphUpdateResponse],
    status_code=status.HTTP_200_OK,
    summary="Incrementally update knowledge graph",
    description="Extracts named entities and relationship triples from newly ingested text or document content.",
)
async def update_knowledge_graph(
    request: GraphUpdateRequest,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.GRAPH_BUILD)),
) -> ApiResponse[GraphUpdateResponse]:
    """Processes incremental text and updates graph triples."""
    result = await db.run_sync(
        lambda sync_session: graph_service.update_graph_incremental(
            db=sync_session,
            organization_id=tenant.organization_id,
            text_content=request.text_content,
            document_id=request.document_id,
            metadata=request.metadata,
        )
    )
    return ApiResponse(
        success=True,
        message="Incremental graph update completed.",
        data=result,
    )


@router.get(
    "/entity/{id}",
    response_model=ApiResponse[EntityResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve entity details",
    description="Fetches properties, entity type, and in/out degrees for a designated knowledge graph node.",
)
async def get_entity_details(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.GRAPH_READ)),
) -> ApiResponse[EntityResponse]:
    """Inspects a single knowledge graph entity."""
    result = await db.run_sync(
        lambda sync_session: graph_service.get_entity(
            db=sync_session,
            organization_id=tenant.organization_id,
            entity_id=id,
        )
    )
    return ApiResponse(
        success=True,
        message="Entity details retrieved successfully.",
        data=result,
    )


@router.get(
    "/relationships/{id}",
    response_model=ApiResponse[EntityRelationshipsResponse],
    status_code=status.HTTP_200_OK,
    summary="View entity relationships",
    description="Retrieves immediate incoming and outgoing directed graph edges for an entity node.",
)
async def get_entity_relationships(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.GRAPH_READ)),
) -> ApiResponse[EntityRelationshipsResponse]:
    """Fetches immediate directed relationship edges for an entity."""
    result = await db.run_sync(
        lambda sync_session: graph_service.get_entity_relationships(
            db=sync_session,
            organization_id=tenant.organization_id,
            entity_id=id,
        )
    )
    return ApiResponse(
        success=True,
        message="Entity relationships retrieved successfully.",
        data=result,
    )


@router.post(
    "/query",
    response_model=ApiResponse[GraphQueryResponse],
    status_code=status.HTTP_200_OK,
    summary="Execute multi-hop graph query",
    description="Traverses connected enterprise entities up to a specified depth with cycle prevention.",
)
async def execute_graph_query(
    request: GraphQueryRequest,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.GRAPH_READ)),
) -> ApiResponse[GraphQueryResponse]:
    """Executes multi-hop breadth-first traversal."""
    result = await db.run_sync(
        lambda sync_session: graph_service.execute_query(
            db=sync_session,
            organization_id=tenant.organization_id,
            start_entity_id=request.start_entity_id,
            max_depth=request.max_depth,
            allowed_relation_types=request.allowed_relation_types,
            allowed_entity_types=request.allowed_entity_types,
        )
    )
    return ApiResponse(
        success=True,
        message="Graph query executed successfully.",
        data=result,
    )


@router.get(
    "/explorer",
    response_model=ApiResponse[GraphExplorerResponse],
    status_code=status.HTTP_200_OK,
    summary="Knowledge explorer visualization data",
    description="Fetches node and link topology alongside graph metrics (density, hubs) for canvas visualization.",
)
async def get_explorer_data(
    entity_type: str | None = Query(default=None, description="Optional entity type filter"),
    limit: int = Query(default=100, ge=1, le=500, description="Max node count"),
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.GRAPH_READ)),
) -> ApiResponse[GraphExplorerResponse]:
    """Provides topological payload for the frontend Knowledge Explorer canvas."""
    result = await db.run_sync(
        lambda sync_session: graph_service.get_explorer_data(
            db=sync_session,
            organization_id=tenant.organization_id,
            entity_type=entity_type,
            limit=limit,
        )
    )
    return ApiResponse(
        success=True,
        message="Explorer data retrieved successfully.",
        data=result,
    )


@router.get(
    "/expertise",
    response_model=ApiResponse[ExpertiseResponse],
    status_code=status.HTTP_200_OK,
    summary="Subject-matter expertise discovery",
    description="Discovers and ranks organizational personnel by subject-matter expertise based on graph linkages.",
)
async def discover_expertise(
    topic: str = Query(..., min_length=1, max_length=200, description="Target domain or topic name"),
    limit: int = Query(default=5, ge=1, le=20, description="Max ranked experts to return"),
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.GRAPH_INTELLIGENCE)),
) -> ApiResponse[ExpertiseResponse]:
    """Discovers subject-matter expertise for a topic."""
    result = await db.run_sync(
        lambda sync_session: graph_service.discover_expertise(
            db=sync_session,
            organization_id=tenant.organization_id,
            topic=topic,
            limit=limit,
        )
    )
    return ApiResponse(
        success=True,
        message="Expertise discovery completed successfully.",
        data=result,
    )


@router.get(
    "/impact/{entity_id}",
    response_model=ApiResponse[ImpactAnalysisResponse],
    status_code=status.HTTP_200_OK,
    summary="Recursive impact analysis",
    description="Evaluates the downstream blast radius, affected departments, and dependent projects of an entity.",
)
async def analyze_impact(
    entity_id: UUID,
    max_depth: int = Query(default=3, ge=1, le=5, description="Max depth of dependency traversal"),
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.GRAPH_INTELLIGENCE)),
) -> ApiResponse[ImpactAnalysisResponse]:
    """Analyzes downstream dependency impact for a given entity."""
    result = await db.run_sync(
        lambda sync_session: graph_service.analyze_impact(
            db=sync_session,
            organization_id=tenant.organization_id,
            entity_id=entity_id,
            max_depth=max_depth,
        )
    )
    return ApiResponse(
        success=True,
        message="Impact analysis completed successfully.",
        data=result,
    )
