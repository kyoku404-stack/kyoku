"""Typed Domain Contracts & Reference Components for KEEP Knowledge Graph (Phase 2.4).

Defines core enterprise ontology, entity taxonomies, relationship classifications,
traversal models, impact analysis specs, expertise discovery, and GraphRAG contracts.

Specification: devdocs/p2/p2.4.txt & docs/Architecture/knowledge-graph-enterprise-intelligence.md
Author: Member 1 (Project Lead & AI Architect)
"""

import re
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, ClassVar
from uuid import UUID

# -----------------------------------------------------------------------------
# 1. Enterprise Ontology Enumerations
# -----------------------------------------------------------------------------


class EntityType(StrEnum):
    """Categorization of entities within the KEEP Enterprise Knowledge Graph."""

    # Organizational
    ORGANIZATION = "ORGANIZATION"
    DEPARTMENT = "DEPARTMENT"
    TEAM = "TEAM"
    EMPLOYEE = "EMPLOYEE"

    # Knowledge
    DOCUMENT = "DOCUMENT"
    POLICY = "POLICY"
    SOP = "SOP"
    MEETING = "MEETING"
    REPORT = "REPORT"
    RESEARCH_PAPER = "RESEARCH_PAPER"

    # Operational
    PROJECT = "PROJECT"
    TASK = "TASK"
    MILESTONE = "MILESTONE"
    RISK = "RISK"
    DECISION = "DECISION"

    # Technical & Conceptual
    TECHNOLOGY = "TECHNOLOGY"
    TOPIC = "TOPIC"


class RelationType(StrEnum):
    """Semantic relationship verbs defining directed graph edges."""

    WORKS_IN = "WORKS_IN"
    LEADS = "LEADS"
    PARTICIPATES_IN = "PARTICIPATES_IN"
    AUTHORED = "AUTHORED"
    CONTAINS = "CONTAINS"
    REFERENCES = "REFERENCES"
    APPLIES_TO = "APPLIES_TO"
    DEPENDS_ON = "DEPENDS_ON"
    DISCUSSED = "DISCUSSED"
    EXPERT_IN = "EXPERT_IN"
    GOVERNED_BY = "GOVERNED_BY"
    BLOCKS = "BLOCKS"
    REPORTS_TO = "REPORTS_TO"


# -----------------------------------------------------------------------------
# 2. Data Transfer Specifications & Value Objects
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class EntitySpec:
    """Specification of an extracted or normalized entity node."""

    name: str
    entity_type: EntityType
    properties: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass(frozen=True)
class RelationshipSpec:
    """Specification of an extracted semantic relationship edge."""

    source_name: str
    source_type: EntityType
    relation_type: RelationType
    target_name: str
    target_type: EntityType
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphNode:
    """In-memory representation of an active graph entity."""

    id: UUID
    name: str
    entity_type: EntityType
    properties: dict[str, Any] = field(default_factory=dict)
    in_degree: int = 0
    out_degree: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class GraphEdge:
    """In-memory representation of a directed semantic edge."""

    id: UUID
    source_id: UUID
    target_id: UUID
    relation_type: RelationType
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class GraphTraversalPath:
    """Represents a discovered multi-hop path through the graph."""

    path_entity_ids: list[UUID]
    path_names: list[str]
    relation_sequence: list[RelationType]
    total_weight: float
    depth: int


@dataclass
class GraphQueryResult:
    """Encapsulates the complete subgraph result of a traversal query."""

    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    total_paths: int
    max_depth_reached: int


@dataclass
class ExpertiseRank:
    """Subject matter expert identification result."""

    user_id: UUID
    full_name: str
    department: str
    score: float
    authored_documents_count: int
    contributed_projects: list[str]
    evidence_citations: list[str]


@dataclass
class ImpactAnalysisResult:
    """Downstream blast radius analysis for an organizational change."""

    root_entity_id: UUID
    root_entity_name: str
    root_entity_type: EntityType
    affected_departments: list[str]
    dependent_projects: list[str]
    impacted_tasks_count: int
    severity_score: float
    dependency_tree: list[dict[str, Any]]


@dataclass
class GraphMetrics:
    """High-level structural health KPIs for an enterprise knowledge graph."""

    total_entities: int
    total_relationships: int
    density: float
    top_hub: str
    orphan_count: int = 0


@dataclass
class GraphRAGContext:
    """Contextual subgraph envelope injected into RAG synthesis prompts."""

    entities_found: list[str]
    subgraph_triples: list[dict[str, str]]
    context_string: str


# -----------------------------------------------------------------------------
# 3. Abstract Service Contracts
# -----------------------------------------------------------------------------


class BaseEntityNormalizer(ABC):
    """Abstract interface for canonical string normalization and entity deduplication."""

    @abstractmethod
    def normalize_name(self, name: str, entity_type: EntityType) -> str:
        """Normalizes name string into canonical format."""

    @abstractmethod
    def are_aliases(self, name1: str, name2: str) -> bool:
        """Determines if two name variations refer to the same canonical entity."""


class BaseEntityExtractor(ABC):
    """Abstract interface for extracting typed entity mentions from document content."""

    @abstractmethod
    def extract_entities(self, text: str) -> list[EntitySpec]:
        """Extracts entity candidates from unstructured text."""


class BaseRelationshipExtractor(ABC):
    """Abstract interface for detecting semantic relations between entities."""

    @abstractmethod
    def extract_relationships(
        self, text: str, entities: list[EntitySpec]
    ) -> list[RelationshipSpec]:
        """Extracts directed relationships from text with reference to identified entities."""


class BaseGraphTraversalEngine(ABC):
    """Abstract interface for multi-hop graph walks and cycle-safe path discovery."""

    @abstractmethod
    def traverse(
        self,
        start_id: UUID,
        max_depth: int = 2,
        allowed_relations: list[RelationType] | None = None,
        allowed_types: list[EntityType] | None = None,
    ) -> GraphQueryResult:
        """Executes multi-hop traversal from a root entity."""


class BaseImpactAnalyzer(ABC):
    """Abstract interface for recursive downstream blast radius impact analysis."""

    @abstractmethod
    def analyze_impact(self, root_id: UUID, max_depth: int = 3) -> ImpactAnalysisResult:
        """Calculates downstream dependencies affected by mutations to root_id."""


class BaseExpertiseDiscoveryEngine(ABC):
    """Abstract interface for topic-based subject matter expert identification."""

    @abstractmethod
    def discover_experts(self, topic: str, limit: int = 5) -> list[ExpertiseRank]:
        """Finds top ranked contributors for a given topic."""


class BaseGraphRAGAugmenter(ABC):
    """Abstract interface for Graph-Enhanced RAG context assembly."""

    @abstractmethod
    def augment_rag_context(self, query: str) -> GraphRAGContext:
        """Generates contextual subgraph envelope for query augmentation."""


# -----------------------------------------------------------------------------
# 4. Concrete Reference Implementations
# -----------------------------------------------------------------------------


class DefaultEntityNormalizer(BaseEntityNormalizer):
    """Production reference entity normalizer handling unicode, aliases, and acronyms."""

    ALIAS_MAP: ClassVar[dict[str, str]] = {
        "k8s": "Kubernetes",
        "kubernetes": "Kubernetes",
        "hr": "Human Resources",
        "human resources": "Human Resources",
        "people ops": "Human Resources",
        "eng": "Engineering",
        "engineering": "Engineering",
        "sop": "Standard Operating Procedure",
        "ai": "Artificial Intelligence",
        "rag": "Retrieval-Augmented Generation",
        "secops": "Security Operations",
    }

    def normalize_name(self, name: str, entity_type: EntityType) -> str:
        if not name:
            return ""
        # 1. NFKC Unicode normalization
        clean = unicodedata.normalize("NFKC", name).strip()
        # 2. Collapse internal whitespace
        clean = re.sub(r"\s+", " ", clean)

        # 3. Check alias dictionary
        lower = clean.lower()
        if lower in self.ALIAS_MAP:
            return self.ALIAS_MAP[lower]

        # 4. Title case for names and departments if not acronym
        if len(clean) > 4 and clean.isupper():
            return clean
        if entity_type in (EntityType.DEPARTMENT, EntityType.TOPIC, EntityType.ROLE if hasattr(EntityType, "ROLE") else EntityType.TEAM):
            return clean.title()

        return clean

    def are_aliases(self, name1: str, name2: str) -> bool:
        norm1 = self.normalize_name(name1, EntityType.TOPIC).lower()
        norm2 = self.normalize_name(name2, EntityType.TOPIC).lower()
        return norm1 == norm2


class DefaultEntityExtractor(BaseEntityExtractor):
    """Heuristic rule and pattern-based entity extractor for Phase 2.4."""

    def __init__(self, normalizer: BaseEntityNormalizer | None = None) -> None:
        self.normalizer = normalizer or DefaultEntityNormalizer()

    def extract_entities(self, text: str) -> list[EntitySpec]:
        if not text:
            return []

        results: list[EntitySpec] = []
        seen: set[tuple[str, EntityType]] = set()

        # 1. Project Patterns: "Project X", "X Project"
        for match in re.finditer(r"\bProject\s+([A-Z][A-Za-z0-9_-]+)\b", text, re.IGNORECASE):
            raw = f"Project {match.group(1).title()}"
            name = self.normalizer.normalize_name(raw, EntityType.PROJECT)
            key = (name.lower(), EntityType.PROJECT)
            if key not in seen:
                seen.add(key)
                results.append(EntitySpec(name=name, entity_type=EntityType.PROJECT, confidence=0.95))

        # 2. Policy / Standard Patterns: "X Policy", "X Standard", "SOP X"
        for match in re.finditer(r"\b([A-Z][A-Za-z0-9_\s]{2,30}?)\s+(Policy|Standard|Guidelines|SOP)\b", text):
            raw = f"{match.group(1).title()} {match.group(2).title()}"
            name = self.normalizer.normalize_name(raw, EntityType.POLICY)
            key = (name.lower(), EntityType.POLICY)
            if key not in seen:
                seen.add(key)
                results.append(EntitySpec(name=name, entity_type=EntityType.POLICY, confidence=0.90))

        # 3. Department Mentions: Engineering, Legal, Human Resources, Operations, Marketing, Product
        dept_pattern = r"\b(Engineering|Human Resources|HR|Legal|Operations|Product|Marketing|Finance|Security)\b"
        for match in re.finditer(dept_pattern, text, re.IGNORECASE):
            name = self.normalizer.normalize_name(match.group(1), EntityType.DEPARTMENT)
            key = (name.lower(), EntityType.DEPARTMENT)
            if key not in seen:
                seen.add(key)
                results.append(EntitySpec(name=name, entity_type=EntityType.DEPARTMENT, confidence=0.95))

        # 4. Technologies & Topics: Kubernetes, Docker, Python, FastAPI, PostgreSQL, Cybersecurity, GDPR
        tech_pattern = r"\b(Kubernetes|K8s|Docker|PostgreSQL|Python|FastAPI|React|TypeScript|Cybersecurity|GDPR|OAuth2|JWT|pgvector)\b"
        for match in re.finditer(tech_pattern, text, re.IGNORECASE):
            name = self.normalizer.normalize_name(match.group(1), EntityType.TECHNOLOGY)
            key = (name.lower(), EntityType.TECHNOLOGY)
            if key not in seen:
                seen.add(key)
                results.append(EntitySpec(name=name, entity_type=EntityType.TECHNOLOGY, confidence=0.92))

        # 5. Person / Employee Mentions: "Alice", "Bob", "Dr. X"
        for match in re.finditer(r"\b(?:[Ll]ed by|[Aa]uthored by|[Aa]ssigned to|[Cc]ontact)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", text):
            raw = match.group(1)
            name = self.normalizer.normalize_name(raw, EntityType.EMPLOYEE)
            key = (name.lower(), EntityType.EMPLOYEE)
            if key not in seen:
                seen.add(key)
                results.append(EntitySpec(name=name, entity_type=EntityType.EMPLOYEE, confidence=0.88))

        return results


class DefaultRelationshipExtractor(BaseRelationshipExtractor):
    """Extracts semantic relational triples between discovered entity nodes."""

    def extract_relationships(
        self, text: str, entities: list[EntitySpec]
    ) -> list[RelationshipSpec]:
        if not text or len(entities) < 2:
            return []

        relationships: list[RelationshipSpec] = []
        # 1. Employee LEADS Project: "[Person] leads/led [Project]"
        leads_matches = re.finditer(
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:leads|is leading|led|managed)\s+(Project\s+[A-Za-z0-9_-]+)\b",
            text,
            re.IGNORECASE,
        )
        for m in leads_matches:
            person = m.group(1).title()
            proj = m.group(2).title()
            relationships.append(
                RelationshipSpec(
                    source_name=person,
                    source_type=EntityType.EMPLOYEE,
                    relation_type=RelationType.LEADS,
                    target_name=proj,
                    target_type=EntityType.PROJECT,
                    weight=0.95,
                )
            )

        # 2. Project / Policy APPLIES_TO Department: "[Project/Policy] applies to [Department]"
        applies_matches = re.finditer(
            r"\b(Project\s+[A-Za-z0-9_-]+|[A-Za-z\s]+Policy)\s+(?:applies to|governs|affects)\s+(?:the\s+)?([A-Za-z\s]+?)\s+(?:department|team)?\b",
            text,
            re.IGNORECASE,
        )
        for m in applies_matches:
            src = m.group(1).strip()
            target_dept = m.group(2).strip().title()
            relationships.append(
                RelationshipSpec(
                    source_name=src,
                    source_type=EntityType.PROJECT if "Project" in src else EntityType.POLICY,
                    relation_type=RelationType.APPLIES_TO,
                    target_name=target_dept,
                    target_type=EntityType.DEPARTMENT,
                    weight=0.90,
                )
            )

        # 3. Employee WORKS_IN Department: "[Person] in [Department]"
        works_matches = re.finditer(
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:works in|from the|of the)\s+([A-Za-z\s]+?)\s+department\b",
            text,
            re.IGNORECASE,
        )
        for m in works_matches:
            person = m.group(1).title()
            dept = m.group(2).strip().title()
            relationships.append(
                RelationshipSpec(
                    source_name=person,
                    source_type=EntityType.EMPLOYEE,
                    relation_type=RelationType.WORKS_IN,
                    target_name=dept,
                    target_type=EntityType.DEPARTMENT,
                    weight=0.88,
                )
            )

        # 4. Fallback co-occurrence for known entity pairs in same sentence
        for e1 in entities:
            for e2 in entities:
                if e1.name == e2.name:
                    continue
                if e1.entity_type == EntityType.PROJECT and e2.entity_type == EntityType.DEPARTMENT:
                    if f"{e1.name} in {e2.name}" in text or f"{e1.name} for {e2.name}" in text:
                        relationships.append(
                            RelationshipSpec(
                                source_name=e1.name,
                                source_type=EntityType.PROJECT,
                                relation_type=RelationType.APPLIES_TO,
                                target_name=e2.name,
                                target_type=EntityType.DEPARTMENT,
                                weight=0.80,
                            )
                        )
                elif (
                    e1.entity_type == EntityType.EMPLOYEE
                    and e2.entity_type == EntityType.TECHNOLOGY
                    and (f"{e1.name} specializes in {e2.name}" in text or f"{e1.name} expert in {e2.name}" in text)
                ):
                    relationships.append(
                        RelationshipSpec(
                            source_name=e1.name,
                            source_type=EntityType.EMPLOYEE,
                            relation_type=RelationType.EXPERT_IN,
                            target_name=e2.name,
                            target_type=EntityType.TECHNOLOGY,
                            weight=0.92,
                        )
                    )

        return relationships


class DefaultGraphRAGAugmenter(BaseGraphRAGAugmenter):
    """Reference GraphRAG context enrichment engine."""

    def __init__(self, extractor: BaseEntityExtractor | None = None) -> None:
        self.extractor = extractor or DefaultEntityExtractor()

    def augment_rag_context(self, query: str) -> GraphRAGContext:
        extracted = self.extractor.extract_entities(query)
        names = [e.name for e in extracted]

        # Formulate synthesized subgraph triples from detected entities
        triples: list[dict[str, str]] = []
        for name in names:
            if "Policy" in name:
                triples.append({
                    "source": name,
                    "relation": RelationType.APPLIES_TO.value,
                    "target": "Engineering Department",
                })
            elif "Project" in name:
                triples.append({
                    "source": name,
                    "relation": RelationType.CONTAINS.value,
                    "target": "Technical Architecture Document",
                })
            else:
                triples.append({
                    "source": name,
                    "relation": RelationType.REFERENCES.value,
                    "target": "Enterprise Knowledge Base",
                })

        context_lines = ["[KNOWLEDGE GRAPH CONTEXT]"]
        for t in triples:
            context_lines.append(f"- {t['source']} {t['relation']} {t['target']}")

        return GraphRAGContext(
            entities_found=names,
            subgraph_triples=triples,
            context_string="\n".join(context_lines),
        )
