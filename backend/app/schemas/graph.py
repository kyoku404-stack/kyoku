"""KEEP Enterprise Platform — Knowledge Graph Pydantic Schemas.

Covers request and response validation payloads for Knowledge Graph Construction,
Incremental Extraction, Multi-Hop Graph Traversal, Explorer Visualizations,
Subject-Matter Expertise Discovery, and Recursive Impact Analysis.
Defined in docs/API/api-contract.md (Section 11).
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GraphBuildRequest(BaseModel):
    """Payload to trigger asynchronous or synchronous full knowledge graph construction."""

    model_config = ConfigDict(from_attributes=True)

    rebuild_all: bool = Field(
        default=False,
        description="Whether to clear existing graph entities and relationships before rebuilding.",
    )
    confidence_threshold: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Minimum extraction confidence required to persist triples.",
    )
    include_documents: bool = Field(
        default=True,
        description="Whether to parse processed document chunks for entities and triples.",
    )
    include_organizational: bool = Field(
        default=True,
        description="Whether to map relational models (Users, Projects, Teams, Departments).",
    )


class GraphBuildResponse(BaseModel):
    """Telemetry report produced after graph construction."""

    model_config = ConfigDict(from_attributes=True)

    organization_id: UUID
    entities_created: int
    entities_updated: int
    relationships_created: int
    duration_seconds: float
    total_entities: int
    total_relationships: int


class GraphUpdateRequest(BaseModel):
    """Payload for incremental entity & relationship extraction from text or documents."""

    model_config = ConfigDict(from_attributes=True)

    document_id: UUID | None = Field(
        default=None,
        description="Optional source document ID associated with the text content.",
    )
    text_content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Text content to analyze for entities and relationships.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Supplementary contextual metadata (e.g. category, author).",
    )


class ExtractedEntityItem(BaseModel):
    """Extracted entity item representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    entity_type: str


class ExtractedRelationshipItem(BaseModel):
    """Extracted relationship triple representation."""

    model_config = ConfigDict(from_attributes=True)

    source: str
    relation: str
    target: str


class GraphUpdateResponse(BaseModel):
    """Result of incremental extraction and graph update."""

    model_config = ConfigDict(from_attributes=True)

    entities_extracted: int
    relationships_extracted: int
    extracted_entities: list[ExtractedEntityItem] = Field(default_factory=list)
    extracted_relationships: list[ExtractedRelationshipItem] = Field(default_factory=list)


class EntityResponse(BaseModel):
    """Entity node inspection details."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: UUID
    name: str
    entity_type: str
    properties: dict[str, Any] = Field(default_factory=dict)
    in_degree: int = 0
    out_degree: int = 0
    created_at: datetime | None = None


class OutgoingRelationshipItem(BaseModel):
    """Outgoing directed graph edge representation."""

    model_config = ConfigDict(from_attributes=True)

    relationship_id: str
    target_entity_id: str
    target_entity_name: str
    target_entity_type: str
    relation_type: str
    weight: float = 1.0


class IncomingRelationshipItem(BaseModel):
    """Incoming directed graph edge representation."""

    model_config = ConfigDict(from_attributes=True)

    relationship_id: str
    source_entity_id: str
    source_entity_name: str
    source_entity_type: str
    relation_type: str
    weight: float = 1.0


class EntityRelationshipsResponse(BaseModel):
    """Immediate adjacency neighborhood of a specific entity."""

    model_config = ConfigDict(from_attributes=True)

    entity_id: str
    outgoing_relationships: list[OutgoingRelationshipItem] = Field(default_factory=list)
    incoming_relationships: list[IncomingRelationshipItem] = Field(default_factory=list)


class GraphQueryRequest(BaseModel):
    """Parameters for executing recursive multi-hop graph queries."""

    model_config = ConfigDict(from_attributes=True)

    start_entity_id: str = Field(
        ...,
        description="Root entity identifier to begin traversal from.",
    )
    max_depth: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Maximum hop distance to explore from the root entity.",
    )
    allowed_relation_types: list[str] | None = Field(
        default=None,
        description="Optional filter whitelist of relationship edge types.",
    )
    allowed_entity_types: list[str] | None = Field(
        default=None,
        description="Optional filter whitelist of node entity types.",
    )


class GraphPathNode(BaseModel):
    """Node returned in a multi-hop traversal."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    entity_type: str
    depth: int = 0


class GraphPathEdge(BaseModel):
    """Edge returned in a multi-hop traversal."""

    model_config = ConfigDict(from_attributes=True)

    source: str
    target: str
    relation_type: str
    weight: float = 1.0


class GraphQueryResponse(BaseModel):
    """Multi-hop traversal path results."""

    model_config = ConfigDict(from_attributes=True)

    nodes: list[GraphPathNode] = Field(default_factory=list)
    edges: list[GraphPathEdge] = Field(default_factory=list)
    total_paths: int = 0
    max_depth_reached: int = 0


class ExplorerNode(BaseModel):
    """Force graph node representation for interactive frontend visualization."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str
    type: str
    val: int = 15


class ExplorerLink(BaseModel):
    """Force graph edge link representation."""

    model_config = ConfigDict(from_attributes=True)

    source: str
    target: str
    label: str
    weight: float = 1.0


class GraphMetricsResponse(BaseModel):
    """Topological graph metrics."""

    model_config = ConfigDict(from_attributes=True)

    total_entities: int = 0
    total_relationships: int = 0
    density: float = 0.0
    top_hub: str | None = None


class GraphExplorerResponse(BaseModel):
    """Full payload for the frontend Knowledge Explorer canvas."""

    model_config = ConfigDict(from_attributes=True)

    nodes: list[ExplorerNode] = Field(default_factory=list)
    links: list[ExplorerLink] = Field(default_factory=list)
    metrics: GraphMetricsResponse


class ExpertItem(BaseModel):
    """Ranked subject-matter expert profile item."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    full_name: str
    department: str | None = None
    score: float = 0.0
    authored_documents_count: int = 0
    contributed_projects: list[str] = Field(default_factory=list)
    evidence_citations: list[str] = Field(default_factory=list)


class ExpertiseResponse(BaseModel):
    """Response envelope for subject-matter expertise discovery."""

    model_config = ConfigDict(from_attributes=True)

    topic: str
    experts: list[ExpertItem] = Field(default_factory=list)


class DependencyTreeNode(BaseModel):
    """Node in an upstream/downstream impact analysis tree."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    entity_type: str
    depth: int = 1
    relation: str = ""


class RootEntityInfo(BaseModel):
    """Root entity descriptor for impact analysis."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    entity_type: str


class ImpactAnalysisResponse(BaseModel):
    """Detailed blast radius and dependency evaluation for an entity."""

    model_config = ConfigDict(from_attributes=True)

    root_entity: RootEntityInfo
    affected_departments: list[str] = Field(default_factory=list)
    dependent_projects: list[str] = Field(default_factory=list)
    impacted_tasks_count: int = 0
    severity_score: float = 0.0
    dependency_tree: list[DependencyTreeNode] = Field(default_factory=list)
