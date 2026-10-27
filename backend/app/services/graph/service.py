"""KEEP Enterprise Platform — Knowledge Graph Service.

Implements graph construction, relationship mapping, multi-hop traversal,
explorer visualization metrics, subject-matter expertise discovery, and
recursive impact analysis for enterprise intelligence.
"""

import logging
import time
import uuid
from typing import Any

from backend.app.core.exceptions import BadRequestException, NotFoundException
from backend.app.models.department import Department
from backend.app.models.document import Document
from backend.app.models.knowledge import DocumentChunk, KgEntity, KgRelationship
from backend.app.models.organization import Organization
from backend.app.models.project import Project
from backend.app.models.task import Task
from backend.app.models.team import Team
from backend.app.models.user import User
from backend.app.schemas.graph import (
    DependencyTreeNode,
    EntityRelationshipsResponse,
    EntityResponse,
    ExpertiseResponse,
    ExpertItem,
    ExplorerLink,
    ExplorerNode,
    ExtractedEntityItem,
    ExtractedRelationshipItem,
    GraphBuildResponse,
    GraphExplorerResponse,
    GraphMetricsResponse,
    GraphPathEdge,
    GraphPathNode,
    GraphQueryResponse,
    GraphUpdateResponse,
    ImpactAnalysisResponse,
    IncomingRelationshipItem,
    OutgoingRelationshipItem,
    RootEntityInfo,
)
from backend.app.services.graph.contracts import (
    DefaultEntityExtractor,
    DefaultEntityNormalizer,
    DefaultRelationshipExtractor,
    EntityType,
    RelationType,
)
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Service layer orchestrating Knowledge Graph construction and enterprise intelligence queries."""

    def __init__(
        self,
        entity_extractor: DefaultEntityExtractor | None = None,
        relationship_extractor: DefaultRelationshipExtractor | None = None,
        normalizer: DefaultEntityNormalizer | None = None,
    ) -> None:
        self.normalizer = normalizer or DefaultEntityNormalizer()
        self.entity_extractor = entity_extractor or DefaultEntityExtractor(normalizer=self.normalizer)
        self.relationship_extractor = relationship_extractor or DefaultRelationshipExtractor()

    def _parse_uuid(self, val: str | uuid.UUID, field_name: str = "ID") -> uuid.UUID:
        if isinstance(val, uuid.UUID):
            return val
        try:
            return uuid.UUID(str(val))
        except (ValueError, TypeError) as err:
            raise BadRequestException(f"Invalid {field_name} format: '{val}'. Must be a valid UUID.") from err

    def build_graph(
        self,
        db: Session,
        organization_id: uuid.UUID | str,
        rebuild_all: bool = False,
        confidence_threshold: float = 0.70,
        include_documents: bool = True,
        include_organizational: bool = True,
    ) -> GraphBuildResponse:
        """Construct knowledge graph from organizational records and document contents."""
        org_id = self._parse_uuid(organization_id, "organization_id")
        start_time = time.perf_counter()

        entities_created = 0
        entities_updated = 0
        relationships_created = 0

        if rebuild_all:
            # Delete existing relationships and entities for this org
            db.execute(delete(KgRelationship).where(KgRelationship.organization_id == org_id))
            db.execute(delete(KgEntity).where(KgEntity.organization_id == org_id))
            db.flush()

        # Entity lookup cache: (normalized_name.lower(), entity_type) -> KgEntity
        existing_entities_stmt = select(KgEntity).where(KgEntity.organization_id == org_id)
        existing_entities = list(db.scalars(existing_entities_stmt).all())
        entity_cache: dict[tuple[str, str], KgEntity] = {
            (e.name.strip().lower(), e.entity_type): e for e in existing_entities
        }
        id_entity_cache: dict[uuid.UUID, KgEntity] = {e.id: e for e in existing_entities}

        def get_or_create_entity(
            name: str,
            entity_type: str,
            properties: dict[str, Any] | None = None,
            specific_id: uuid.UUID | None = None,
        ) -> KgEntity:
            nonlocal entities_created, entities_updated
            norm_name = self.normalizer.normalize_name(name)
            key = (norm_name.strip().lower(), entity_type)

            if specific_id and specific_id in id_entity_cache:
                entity = id_entity_cache[specific_id]
                if properties:
                    merged = dict(entity.properties_json or {})
                    merged.update(properties)
                    entity.properties_json = merged
                    entities_updated += 1
                return entity

            if key in entity_cache:
                entity = entity_cache[key]
                if properties:
                    merged = dict(entity.properties_json or {})
                    merged.update(properties)
                    entity.properties_json = merged
                    entities_updated += 1
                return entity

            entity_id = specific_id or uuid.uuid4()
            entity = KgEntity(
                id=entity_id,
                organization_id=org_id,
                name=norm_name,
                entity_type=entity_type,
                properties_json=properties or {},
            )
            db.add(entity)
            db.flush()
            entity_cache[key] = entity
            id_entity_cache[entity.id] = entity
            entities_created += 1
            return entity

        # Relationship lookup cache: (source_id, target_id, relation_type) -> KgRelationship
        existing_rel_stmt = select(KgRelationship).where(KgRelationship.organization_id == org_id)
        existing_rels = list(db.scalars(existing_rel_stmt).all())
        rel_cache: set[tuple[uuid.UUID, uuid.UUID, str]] = {
            (r.source_entity_id, r.target_entity_id, r.relation_type) for r in existing_rels
        }

        def create_relationship_if_absent(
            source_id: uuid.UUID,
            target_id: uuid.UUID,
            relation_type: str,
            weight: float = 1.0,
            properties: dict[str, Any] | None = None,
        ) -> None:
            nonlocal relationships_created
            if source_id == target_id:
                return  # Skip self-loops for standard ontology
            key = (source_id, target_id, relation_type)
            if key in rel_cache:
                return

            rel = KgRelationship(
                organization_id=org_id,
                source_entity_id=source_id,
                target_entity_id=target_id,
                relation_type=relation_type,
                weight=weight,
                properties_json=properties or {},
            )
            db.add(rel)
            rel_cache.add(key)
            relationships_created += 1

        # 1. Organizational structure mapping
        if include_organizational:
            org = db.scalar(select(Organization).where(Organization.id == org_id))
            org_node = None
            if org:
                org_node = get_or_create_entity(
                    name=org.name,
                    entity_type=EntityType.ORGANIZATION.value,
                    properties={"domain": org.domain},
                    specific_id=org.id,
                )

            # Departments
            departments = list(db.scalars(select(Department).where(Department.organization_id == org_id)).all())
            dept_nodes: dict[uuid.UUID, KgEntity] = {}
            for dept in departments:
                d_node = get_or_create_entity(
                    name=dept.name,
                    entity_type=EntityType.DEPARTMENT.value,
                    properties={"description": dept.description},
                    specific_id=dept.id,
                )
                dept_nodes[dept.id] = d_node
                if org_node:
                    create_relationship_if_absent(d_node.id, org_node.id, RelationType.BELONGS_TO.value)

            # Teams
            teams = list(db.scalars(select(Team).where(Team.organization_id == org_id)).all())
            team_nodes: dict[uuid.UUID, KgEntity] = {}
            for team in teams:
                t_node = get_or_create_entity(
                    name=team.name,
                    entity_type=EntityType.TEAM.value,
                    properties={"description": team.description},
                    specific_id=team.id,
                )
                team_nodes[team.id] = t_node
                if team.department_id and team.department_id in dept_nodes:
                    create_relationship_if_absent(
                        t_node.id, dept_nodes[team.department_id].id, RelationType.BELONGS_TO.value
                    )
                elif org_node:
                    create_relationship_if_absent(t_node.id, org_node.id, RelationType.BELONGS_TO.value)

            # Users / Employees
            users = list(db.scalars(select(User).where(User.organization_id == org_id)).all())
            user_nodes: dict[uuid.UUID, KgEntity] = {}
            for u in users:
                user_name = u.full_name or u.email.split("@")[0]
                u_node = get_or_create_entity(
                    name=user_name,
                    entity_type=EntityType.EMPLOYEE.value,
                    properties={"email": u.email, "role": u.role},
                    specific_id=u.id,
                )
                user_nodes[u.id] = u_node
                if u.department_id and u.department_id in dept_nodes:
                    create_relationship_if_absent(
                        u_node.id, dept_nodes[u.department_id].id, RelationType.MEMBER_OF.value
                    )

            # Link department managers
            for dept in departments:
                if dept.manager_id and dept.manager_id in user_nodes and dept.id in dept_nodes:
                    create_relationship_if_absent(
                        user_nodes[dept.manager_id].id,
                        dept_nodes[dept.id].id,
                        RelationType.LEADS.value,
                    )

            # Projects
            projects = list(db.scalars(select(Project).where(Project.organization_id == org_id)).all())
            project_nodes: dict[uuid.UUID, KgEntity] = {}
            for proj in projects:
                p_node = get_or_create_entity(
                    name=proj.name,
                    entity_type=EntityType.PROJECT.value,
                    properties={"status": proj.status, "priority": proj.priority},
                    specific_id=proj.id,
                )
                project_nodes[proj.id] = p_node

                if proj.team_id and proj.team_id in team_nodes:
                    create_relationship_if_absent(
                        p_node.id, team_nodes[proj.team_id].id, RelationType.OWNED_BY.value
                    )
                if proj.owner_id and proj.owner_id in user_nodes:
                    create_relationship_if_absent(
                        user_nodes[proj.owner_id].id, p_node.id, RelationType.LEADS.value
                    )

                # Project contributors
                for contrib in getattr(proj, "users", []):
                    if contrib.id in user_nodes:
                        create_relationship_if_absent(
                            user_nodes[contrib.id].id, p_node.id, RelationType.CONTRIBUTES_TO.value
                        )

            # Tasks
            if project_nodes:
                project_ids = list(project_nodes.keys())
                tasks = list(db.scalars(select(Task).where(Task.project_id.in_(project_ids))).all())
                for t in tasks:
                    t_node = get_or_create_entity(
                        name=t.title,
                        entity_type=EntityType.TASK.value,
                        properties={"status": t.status, "priority": t.priority},
                        specific_id=t.id,
                    )
                    if t.project_id in project_nodes:
                        create_relationship_if_absent(
                            t_node.id, project_nodes[t.project_id].id, RelationType.PART_OF.value
                        )

        # 2. Documents and chunk text entity extraction
        if include_documents:
            docs = list(db.scalars(select(Document).where(Document.organization_id == org_id)).all())
            doc_nodes: dict[uuid.UUID, KgEntity] = {}
            for doc in docs:
                doc_title = doc.title or doc.filename or "Untitled Document"
                d_node = get_or_create_entity(
                    name=doc_title,
                    entity_type=EntityType.DOCUMENT.value,
                    properties={"filename": doc.filename, "category": doc.category},
                    specific_id=doc.id,
                )
                doc_nodes[doc.id] = d_node

                if doc.project_id and doc.project_id in project_nodes:
                    create_relationship_if_absent(
                        d_node.id, project_nodes[doc.project_id].id, RelationType.REFERENCES.value
                    )
                if doc.uploader_id and doc.uploader_id in user_nodes:
                    create_relationship_if_absent(
                        user_nodes[doc.uploader_id].id, d_node.id, RelationType.AUTHORS.value
                    )

                # Extract entities & relationships from chunks
                chunks = list(
                    db.scalars(
                        select(DocumentChunk)
                        .where(DocumentChunk.document_id == doc.id)
                        .order_by(DocumentChunk.chunk_index)
                        .limit(20)
                    ).all()
                )
                for chunk in chunks:
                    if not chunk.content:
                        continue
                    extracted_entities = self.entity_extractor.extract(
                        chunk.content, min_confidence=confidence_threshold
                    )
                    chunk_entity_nodes: list[KgEntity] = []
                    for e_spec in extracted_entities:
                        c_node = get_or_create_entity(
                            name=e_spec.name,
                            entity_type=e_spec.entity_type.value,
                            properties={"confidence": e_spec.confidence, "source_document_id": str(doc.id)},
                        )
                        chunk_entity_nodes.append(c_node)
                        create_relationship_if_absent(
                            d_node.id, c_node.id, RelationType.MENTIONS.value, weight=e_spec.confidence
                        )

                    extracted_triples = self.relationship_extractor.extract(
                        chunk.content,
                        known_entities=extracted_entities,
                        min_confidence=confidence_threshold,
                    )
                    for triple in extracted_triples:
                        s_norm = self.normalizer.normalize_name(triple.source_name)
                        t_norm = self.normalizer.normalize_name(triple.target_name)
                        s_node = get_or_create_entity(s_norm, EntityType.CONCEPT.value)
                        t_node = get_or_create_entity(t_norm, EntityType.CONCEPT.value)
                        create_relationship_if_absent(
                            s_node.id,
                            t_node.id,
                            triple.relation_type.value,
                            weight=triple.confidence,
                        )

        db.commit()

        total_entities = db.scalar(
            select(func.count(KgEntity.id)).where(KgEntity.organization_id == org_id)
        ) or 0
        total_relationships = db.scalar(
            select(func.count(KgRelationship.id)).where(KgRelationship.organization_id == org_id)
        ) or 0
        duration = round(time.perf_counter() - start_time, 2)

        logger.info(
            "Knowledge graph build complete for org %s: %d created, %d rels, took %.2fs",
            org_id,
            entities_created,
            relationships_created,
            duration,
        )

        return GraphBuildResponse(
            organization_id=org_id,
            entities_created=entities_created,
            entities_updated=entities_updated,
            relationships_created=relationships_created,
            duration_seconds=duration,
            total_entities=total_entities,
            total_relationships=total_relationships,
        )

    def update_graph_incremental(
        self,
        db: Session,
        organization_id: uuid.UUID | str,
        text_content: str,
        document_id: uuid.UUID | str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GraphUpdateResponse:
        """Incrementally extract and upsert entities and relationships from newly provided text or document."""
        org_id = self._parse_uuid(organization_id, "organization_id")
        doc_uuid = self._parse_uuid(document_id, "document_id") if document_id else None

        extracted_entities = self.entity_extractor.extract(text_content, min_confidence=0.60)
        extracted_rels = self.relationship_extractor.extract(
            text_content, known_entities=extracted_entities, min_confidence=0.60
        )

        entity_items: list[ExtractedEntityItem] = []
        node_map: dict[str, KgEntity] = {}

        # If document_id provided, ensure document entity exists
        doc_entity = None
        if doc_uuid:
            doc_entity = db.scalar(
                select(KgEntity).where(
                    KgEntity.organization_id == org_id,
                    KgEntity.id == doc_uuid,
                )
            )

        for e_spec in extracted_entities:
            norm_name = self.normalizer.normalize_name(e_spec.name)
            # Find or create
            entity = db.scalar(
                select(KgEntity).where(
                    KgEntity.organization_id == org_id,
                    func.lower(KgEntity.name) == norm_name.lower(),
                    KgEntity.entity_type == e_spec.entity_type.value,
                )
            )
            if not entity:
                entity = KgEntity(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    name=norm_name,
                    entity_type=e_spec.entity_type.value,
                    properties_json={
                        "confidence": e_spec.confidence,
                        **(metadata or {}),
                    },
                )
                db.add(entity)
                db.flush()
            node_map[norm_name.lower()] = entity
            entity_items.append(
                ExtractedEntityItem(
                    id=str(entity.id),
                    name=entity.name,
                    entity_type=entity.entity_type,
                )
            )
            if doc_entity:
                # Add MENTIONS relation
                existing_m = db.scalar(
                    select(KgRelationship).where(
                        KgRelationship.organization_id == org_id,
                        KgRelationship.source_entity_id == doc_entity.id,
                        KgRelationship.target_entity_id == entity.id,
                        KgRelationship.relation_type == RelationType.MENTIONS.value,
                    )
                )
                if not existing_m:
                    db.add(
                        KgRelationship(
                            organization_id=org_id,
                            source_entity_id=doc_entity.id,
                            target_entity_id=entity.id,
                            relation_type=RelationType.MENTIONS.value,
                            weight=e_spec.confidence,
                        )
                    )

        rel_items: list[ExtractedRelationshipItem] = []
        for r_spec in extracted_rels:
            s_norm = self.normalizer.normalize_name(r_spec.source_name)
            t_norm = self.normalizer.normalize_name(r_spec.target_name)

            s_entity = node_map.get(s_norm.lower())
            if not s_entity:
                s_entity = db.scalar(
                    select(KgEntity).where(
                        KgEntity.organization_id == org_id,
                        func.lower(KgEntity.name) == s_norm.lower(),
                    )
                )
                if not s_entity:
                    s_entity = KgEntity(
                        id=uuid.uuid4(),
                        organization_id=org_id,
                        name=s_norm,
                        entity_type=EntityType.CONCEPT.value,
                        properties_json={},
                    )
                    db.add(s_entity)
                    db.flush()
                node_map[s_norm.lower()] = s_entity

            t_entity = node_map.get(t_norm.lower())
            if not t_entity:
                t_entity = db.scalar(
                    select(KgEntity).where(
                        KgEntity.organization_id == org_id,
                        func.lower(KgEntity.name) == t_norm.lower(),
                    )
                )
                if not t_entity:
                    t_entity = KgEntity(
                        id=uuid.uuid4(),
                        organization_id=org_id,
                        name=t_norm,
                        entity_type=EntityType.CONCEPT.value,
                        properties_json={},
                    )
                    db.add(t_entity)
                    db.flush()
                node_map[t_norm.lower()] = t_entity

            if s_entity.id != t_entity.id:
                existing_rel = db.scalar(
                    select(KgRelationship).where(
                        KgRelationship.organization_id == org_id,
                        KgRelationship.source_entity_id == s_entity.id,
                        KgRelationship.target_entity_id == t_entity.id,
                        KgRelationship.relation_type == r_spec.relation_type.value,
                    )
                )
                if not existing_rel:
                    db.add(
                        KgRelationship(
                            organization_id=org_id,
                            source_entity_id=s_entity.id,
                            target_entity_id=t_entity.id,
                            relation_type=r_spec.relation_type.value,
                            weight=r_spec.confidence,
                        )
                    )

            rel_items.append(
                ExtractedRelationshipItem(
                    source=s_entity.name,
                    relation=r_spec.relation_type.value,
                    target=t_entity.name,
                )
            )

        db.commit()

        return GraphUpdateResponse(
            entities_extracted=len(entity_items),
            relationships_extracted=len(rel_items),
            extracted_entities=entity_items,
            extracted_relationships=rel_items,
        )

    def get_entity(
        self,
        db: Session,
        organization_id: uuid.UUID | str,
        entity_id: uuid.UUID | str,
    ) -> EntityResponse:
        """Retrieve single entity node details, in/out degrees, and properties."""
        org_id = self._parse_uuid(organization_id, "organization_id")
        e_id = self._parse_uuid(entity_id, "entity_id")

        entity = db.scalar(
            select(KgEntity).where(
                KgEntity.organization_id == org_id,
                KgEntity.id == e_id,
            )
        )
        if not entity:
            raise NotFoundException(f"Graph entity with ID '{entity_id}' not found.")

        in_degree = db.scalar(
            select(func.count(KgRelationship.id)).where(
                KgRelationship.organization_id == org_id,
                KgRelationship.target_entity_id == e_id,
            )
        ) or 0
        out_degree = db.scalar(
            select(func.count(KgRelationship.id)).where(
                KgRelationship.organization_id == org_id,
                KgRelationship.source_entity_id == e_id,
            )
        ) or 0

        return EntityResponse(
            id=str(entity.id),
            organization_id=entity.organization_id,
            name=entity.name,
            entity_type=entity.entity_type,
            properties=entity.properties_json or {},
            in_degree=in_degree,
            out_degree=out_degree,
            created_at=entity.created_at,
        )

    def get_entity_relationships(
        self,
        db: Session,
        organization_id: uuid.UUID | str,
        entity_id: uuid.UUID | str,
    ) -> EntityRelationshipsResponse:
        """Retrieve all incoming and outgoing edges for an entity."""
        org_id = self._parse_uuid(organization_id, "organization_id")
        e_id = self._parse_uuid(entity_id, "entity_id")

        # Validate entity exists
        entity = db.scalar(
            select(KgEntity).where(
                KgEntity.organization_id == org_id,
                KgEntity.id == e_id,
            )
        )
        if not entity:
            raise NotFoundException(f"Graph entity with ID '{entity_id}' not found.")

        # Outgoing
        out_stmt = (
            select(KgRelationship, KgEntity)
            .join(KgEntity, KgRelationship.target_entity_id == KgEntity.id)
            .where(
                KgRelationship.organization_id == org_id,
                KgRelationship.source_entity_id == e_id,
            )
        )
        out_rows = db.execute(out_stmt).all()
        outgoing = [
            OutgoingRelationshipItem(
                relationship_id=str(rel.id),
                target_entity_id=str(target.id),
                target_entity_name=target.name,
                target_entity_type=target.entity_type,
                relation_type=rel.relation_type,
                weight=rel.weight,
            )
            for rel, target in out_rows
        ]

        # Incoming
        in_stmt = (
            select(KgRelationship, KgEntity)
            .join(KgEntity, KgRelationship.source_entity_id == KgEntity.id)
            .where(
                KgRelationship.organization_id == org_id,
                KgRelationship.target_entity_id == e_id,
            )
        )
        in_rows = db.execute(in_stmt).all()
        incoming = [
            IncomingRelationshipItem(
                relationship_id=str(rel.id),
                source_entity_id=str(source.id),
                source_entity_name=source.name,
                source_entity_type=source.entity_type,
                relation_type=rel.relation_type,
                weight=rel.weight,
            )
            for rel, source in in_rows
        ]

        return EntityRelationshipsResponse(
            entity_id=str(entity.id),
            outgoing_relationships=outgoing,
            incoming_relationships=incoming,
        )

    def execute_query(
        self,
        db: Session,
        organization_id: uuid.UUID | str,
        start_entity_id: str,
        max_depth: int = 2,
        allowed_relation_types: list[str] | None = None,
        allowed_entity_types: list[str] | None = None,
    ) -> GraphQueryResponse:
        """Perform multi-hop traversal with cycle prevention starting from a designated entity node."""
        org_id = self._parse_uuid(organization_id, "organization_id")
        start_uuid = self._parse_uuid(start_entity_id, "start_entity_id")
        clamped_depth = max(1, min(max_depth, 5))

        root_entity = db.scalar(
            select(KgEntity).where(
                KgEntity.organization_id == org_id,
                KgEntity.id == start_uuid,
            )
        )
        if not root_entity:
            raise NotFoundException(f"Start entity with ID '{start_entity_id}' not found.")

        visited_node_ids: set[uuid.UUID] = {root_entity.id}
        frontier: list[tuple[uuid.UUID, int]] = [(root_entity.id, 0)]

        nodes_result: dict[uuid.UUID, GraphPathNode] = {
            root_entity.id: GraphPathNode(
                id=str(root_entity.id),
                name=root_entity.name,
                entity_type=root_entity.entity_type,
                depth=0,
            )
        }
        edges_result: list[GraphPathEdge] = []
        edge_keys: set[tuple[str, str, str]] = set()

        max_depth_reached = 0

        while frontier:
            curr_id, curr_depth = frontier.pop(0)
            if curr_depth >= clamped_depth:
                continue

            # Query outgoing edges
            out_stmt = (
                select(KgRelationship, KgEntity)
                .join(KgEntity, KgRelationship.target_entity_id == KgEntity.id)
                .where(
                    KgRelationship.organization_id == org_id,
                    KgRelationship.source_entity_id == curr_id,
                )
            )
            if allowed_relation_types:
                out_stmt = out_stmt.where(KgRelationship.relation_type.in_(allowed_relation_types))
            if allowed_entity_types:
                out_stmt = out_stmt.where(KgEntity.entity_type.in_(allowed_entity_types))

            for rel, target in db.execute(out_stmt).all():
                edge_key = (str(curr_id), str(target.id), rel.relation_type)
                if edge_key not in edge_keys:
                    edge_keys.add(edge_key)
                    edges_result.append(
                        GraphPathEdge(
                            source=str(curr_id),
                            target=str(target.id),
                            relation_type=rel.relation_type,
                            weight=rel.weight,
                        )
                    )
                if target.id not in visited_node_ids:
                    visited_node_ids.add(target.id)
                    next_depth = curr_depth + 1
                    max_depth_reached = max(max_depth_reached, next_depth)
                    nodes_result[target.id] = GraphPathNode(
                        id=str(target.id),
                        name=target.name,
                        entity_type=target.entity_type,
                        depth=next_depth,
                    )
                    frontier.append((target.id, next_depth))

            # Query incoming edges (undirected exploration for complete neighborhood)
            in_stmt = (
                select(KgRelationship, KgEntity)
                .join(KgEntity, KgRelationship.source_entity_id == KgEntity.id)
                .where(
                    KgRelationship.organization_id == org_id,
                    KgRelationship.target_entity_id == curr_id,
                )
            )
            if allowed_relation_types:
                in_stmt = in_stmt.where(KgRelationship.relation_type.in_(allowed_relation_types))
            if allowed_entity_types:
                in_stmt = in_stmt.where(KgEntity.entity_type.in_(allowed_entity_types))

            for rel, source in db.execute(in_stmt).all():
                edge_key = (str(source.id), str(curr_id), rel.relation_type)
                if edge_key not in edge_keys:
                    edge_keys.add(edge_key)
                    edges_result.append(
                        GraphPathEdge(
                            source=str(source.id),
                            target=str(curr_id),
                            relation_type=rel.relation_type,
                            weight=rel.weight,
                        )
                    )
                if source.id not in visited_node_ids:
                    visited_node_ids.add(source.id)
                    next_depth = curr_depth + 1
                    max_depth_reached = max(max_depth_reached, next_depth)
                    nodes_result[source.id] = GraphPathNode(
                        id=str(source.id),
                        name=source.name,
                        entity_type=source.entity_type,
                        depth=next_depth,
                    )
                    frontier.append((source.id, next_depth))

        return GraphQueryResponse(
            nodes=list(nodes_result.values()),
            edges=edges_result,
            total_paths=len(edges_result),
            max_depth_reached=max_depth_reached,
        )

    def get_explorer_data(
        self,
        db: Session,
        organization_id: uuid.UUID | str,
        entity_type: str | None = None,
        limit: int = 100,
    ) -> GraphExplorerResponse:
        """Fetch node and link topology for the frontend interactive Knowledge Explorer canvas."""
        org_id = self._parse_uuid(organization_id, "organization_id")
        clamped_limit = max(1, min(limit, 500))

        # Query entities
        e_stmt = select(KgEntity).where(KgEntity.organization_id == org_id)
        if entity_type:
            e_stmt = e_stmt.where(KgEntity.entity_type == entity_type)
        e_stmt = e_stmt.limit(clamped_limit)
        entities = list(db.scalars(e_stmt).all())

        if not entities:
            return GraphExplorerResponse(
                nodes=[],
                links=[],
                metrics=GraphMetricsResponse(
                    total_entities=0,
                    total_relationships=0,
                    density=0.0,
                    top_hub=None,
                ),
            )

        entity_ids = {e.id for e in entities}
        node_degrees: dict[uuid.UUID, int] = {e.id: 0 for e in entities}

        # Query relationships among these entities
        r_stmt = select(KgRelationship).where(
            KgRelationship.organization_id == org_id,
            KgRelationship.source_entity_id.in_(entity_ids),
            KgRelationship.target_entity_id.in_(entity_ids),
        )
        relationships = list(db.scalars(r_stmt).all())

        links: list[ExplorerLink] = []
        for r in relationships:
            node_degrees[r.source_entity_id] = node_degrees.get(r.source_entity_id, 0) + 1
            node_degrees[r.target_entity_id] = node_degrees.get(r.target_entity_id, 0) + 1
            links.append(
                ExplorerLink(
                    source=str(r.source_entity_id),
                    target=str(r.target_entity_id),
                    label=r.relation_type,
                    weight=r.weight,
                )
            )

        nodes: list[ExplorerNode] = [
            ExplorerNode(
                id=str(e.id),
                label=e.name,
                type=e.entity_type,
                val=10 + min(50, node_degrees.get(e.id, 0) * 5),
            )
            for e in entities
        ]

        total_nodes = len(nodes)
        total_edges = len(links)
        density = (2.0 * total_edges) / (total_nodes * (total_nodes - 1)) if total_nodes > 1 else 0.0

        top_hub_entity_id = max(node_degrees, key=node_degrees.get) if node_degrees else None
        top_hub_name = None
        if top_hub_entity_id:
            hub_ent = next((e for e in entities if e.id == top_hub_entity_id), None)
            if hub_ent:
                top_hub_name = hub_ent.name

        return GraphExplorerResponse(
            nodes=nodes,
            links=links,
            metrics=GraphMetricsResponse(
                total_entities=total_nodes,
                total_relationships=total_edges,
                density=round(density, 4),
                top_hub=top_hub_name,
            ),
        )

    def discover_expertise(
        self,
        db: Session,
        organization_id: uuid.UUID | str,
        topic: str,
        limit: int = 5,
    ) -> ExpertiseResponse:
        """Rank organizational personnel by subject-matter expertise based on graph co-occurrence."""
        org_id = self._parse_uuid(organization_id, "organization_id")
        norm_topic = self.normalizer.normalize_name(topic)
        clamped_limit = max(1, min(limit, 20))

        # 1. Look for topic entities in kg_entities
        topic_entities = list(
            db.scalars(
                select(KgEntity).where(
                    KgEntity.organization_id == org_id,
                    func.lower(KgEntity.name).contains(norm_topic.lower()),
                )
            ).all()
        )
        topic_entity_ids = {t.id for t in topic_entities}

        # 2. Look for documents referencing or mentioning this topic
        relevant_doc_ids: set[uuid.UUID] = set()
        if topic_entity_ids:
            doc_rels = list(
                db.scalars(
                    select(KgRelationship.source_entity_id).where(
                        KgRelationship.organization_id == org_id,
                        KgRelationship.target_entity_id.in_(topic_entity_ids),
                        KgRelationship.relation_type == RelationType.MENTIONS.value,
                    )
                ).all()
            )
            relevant_doc_ids.update(doc_rels)

        # Also search Document table directly for keywords in title
        matching_docs = list(
            db.scalars(
                select(Document).where(
                    Document.organization_id == org_id,
                    func.lower(Document.title).contains(norm_topic.lower()),
                )
            ).all()
        )
        for md in matching_docs:
            relevant_doc_ids.add(md.id)

        # 3. Find candidate users
        users = list(db.scalars(select(User).where(User.organization_id == org_id)).all())
        dept_lookup = {
            d.id: d.name
            for d in db.scalars(select(Department).where(Department.organization_id == org_id)).all()
        }

        user_scores: list[ExpertItem] = []

        for u in users:
            authored_docs: list[Document] = []
            if relevant_doc_ids:
                authored_docs = list(
                    db.scalars(
                        select(Document).where(
                            Document.id.in_(relevant_doc_ids),
                            Document.uploader_id == u.id,
                        )
                    ).all()
                )

            # Find projects associated with user and topic
            proj_stmt = (
                select(Project)
                .where(
                    Project.organization_id == org_id,
                    (Project.owner_id == u.id) | (Project.users.any(User.id == u.id)),
                )
            )
            user_projects = list(db.scalars(proj_stmt).all())
            topic_projects = [
                p.name for p in user_projects if norm_topic.lower() in p.name.lower() or (p.description and norm_topic.lower() in p.description.lower())
            ]

            authored_count = len(authored_docs)
            project_count = len(topic_projects)

            # Base score calculation
            score = round(min(10.0, (authored_count * 3.0) + (project_count * 2.0)), 1)
            job_title = getattr(u, "job_title", None) or ""
            if score == 0.0 and (norm_topic.lower() in job_title.lower() or norm_topic.lower() in (u.role or "").lower()):
                score = 3.5

            if score > 0.0:
                citations = [d.title or d.filename for d in authored_docs if d.title or d.filename]
                user_scores.append(
                    ExpertItem(
                        user_id=str(u.id),
                        full_name=u.full_name or u.email.split("@")[0],
                        department=dept_lookup.get(u.department_id) if u.department_id else None,
                        score=score,
                        authored_documents_count=authored_count,
                        contributed_projects=topic_projects or [p.name for p in user_projects[:2]],
                        evidence_citations=citations[:3],
                    )
                )

        user_scores.sort(key=lambda x: x.score, reverse=True)

        # Fallback if no specific matches found: return highest ranking users in the org
        if not user_scores and users:
            for u in users[:clamped_limit]:
                user_scores.append(
                    ExpertItem(
                        user_id=str(u.id),
                        full_name=u.full_name or u.email.split("@")[0],
                        department=dept_lookup.get(u.department_id) if u.department_id else None,
                        score=1.0,
                        authored_documents_count=0,
                        contributed_projects=[],
                        evidence_citations=[],
                    )
                )

        return ExpertiseResponse(
            topic=topic,
            experts=user_scores[:clamped_limit],
        )

    def analyze_impact(
        self,
        db: Session,
        organization_id: uuid.UUID | str,
        entity_id: uuid.UUID | str,
        max_depth: int = 3,
    ) -> ImpactAnalysisResponse:
        """Compute the downstream blast radius, dependent projects, and affected departments."""
        org_id = self._parse_uuid(organization_id, "organization_id")
        e_uuid = self._parse_uuid(entity_id, "entity_id")

        root = db.scalar(
            select(KgEntity).where(
                KgEntity.organization_id == org_id,
                KgEntity.id == e_uuid,
            )
        )
        if not root:
            raise NotFoundException(f"Root entity with ID '{entity_id}' not found.")

        # Breadth-first traversal down dependent relationships
        impact_relations = {
            RelationType.GOVERNED_BY.value,
            RelationType.DEPENDS_ON.value,
            RelationType.APPLIES_TO.value,
            RelationType.PART_OF.value,
            RelationType.BLOCKED_BY.value,
            RelationType.REFERENCES.value,
            RelationType.BELONGS_TO.value,
            RelationType.OWNED_BY.value,
        }

        visited: set[uuid.UUID] = {root.id}
        frontier: list[tuple[uuid.UUID, int]] = [(root.id, 0)]
        tree: list[DependencyTreeNode] = []

        affected_departments: set[str] = set()
        dependent_projects: set[str] = set()
        impacted_tasks_count = 0

        while frontier:
            curr_id, curr_depth = frontier.pop(0)
            if curr_depth >= max_depth:
                continue

            # Check outgoing relationships
            stmt = (
                select(KgRelationship, KgEntity)
                .join(KgEntity, KgRelationship.target_entity_id == KgEntity.id)
                .where(
                    KgRelationship.organization_id == org_id,
                    KgRelationship.source_entity_id == curr_id,
                    KgRelationship.relation_type.in_(impact_relations),
                )
            )
            for rel, target in db.execute(stmt).all():
                if target.id not in visited:
                    visited.add(target.id)
                    next_depth = curr_depth + 1
                    frontier.append((target.id, next_depth))
                    tree.append(
                        DependencyTreeNode(
                            id=str(target.id),
                            name=target.name,
                            entity_type=target.entity_type,
                            depth=next_depth,
                            relation=rel.relation_type,
                        )
                    )
                    if target.entity_type == EntityType.DEPARTMENT.value:
                        affected_departments.add(target.name)
                    elif target.entity_type == EntityType.PROJECT.value:
                        dependent_projects.add(target.name)
                    elif target.entity_type == EntityType.TASK.value:
                        impacted_tasks_count += 1

            # Also check incoming relationships that point to this entity as a dependency
            in_stmt = (
                select(KgRelationship, KgEntity)
                .join(KgEntity, KgRelationship.source_entity_id == KgEntity.id)
                .where(
                    KgRelationship.organization_id == org_id,
                    KgRelationship.target_entity_id == curr_id,
                    KgRelationship.relation_type.in_(impact_relations),
                )
            )
            for rel, source in db.execute(in_stmt).all():
                if source.id not in visited:
                    visited.add(source.id)
                    next_depth = curr_depth + 1
                    frontier.append((source.id, next_depth))
                    tree.append(
                        DependencyTreeNode(
                            id=str(source.id),
                            name=source.name,
                            entity_type=source.entity_type,
                            depth=next_depth,
                            relation=rel.relation_type,
                        )
                    )
                    if source.entity_type == EntityType.DEPARTMENT.value:
                        affected_departments.add(source.name)
                    elif source.entity_type == EntityType.PROJECT.value:
                        dependent_projects.add(source.name)
                    elif source.entity_type == EntityType.TASK.value:
                        impacted_tasks_count += 1

        total_impacted = len(visited) - 1
        severity_score = round(min(1.0, 0.2 + (total_impacted * 0.15)), 2)

        return ImpactAnalysisResponse(
            root_entity=RootEntityInfo(
                id=str(root.id),
                name=root.name,
                entity_type=root.entity_type,
            ),
            affected_departments=sorted(affected_departments),
            dependent_projects=sorted(dependent_projects),
            impacted_tasks_count=impacted_tasks_count,
            severity_score=severity_score,
            dependency_tree=tree,
        )
