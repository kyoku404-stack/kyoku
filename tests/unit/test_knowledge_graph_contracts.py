"""Unit Test Suite for KEEP Knowledge Graph Typed Domain Contracts (Phase 2.4).

Verifies the ontology enums, canonical normalization algorithms,
heuristic entity extractors, relationship extractors, and GraphRAG contracts.

Specification: devdocs/p2/p2.4.txt & docs/Architecture/knowledge-graph-enterprise-intelligence.md
Author: Member 1 (Project Lead & AI Architect)
"""

import unittest
from uuid import uuid4

from backend.app.services.graph.contracts import (
    DefaultEntityExtractor,
    DefaultEntityNormalizer,
    DefaultGraphRAGAugmenter,
    DefaultRelationshipExtractor,
    EntityType,
    ExpertiseRank,
    GraphEdge,
    GraphMetrics,
    GraphNode,
    ImpactAnalysisResult,
    RelationType,
)


class TestKnowledgeGraphContracts(unittest.TestCase):
    """Unit tests for Phase 2.4 Knowledge Graph domain contracts and algorithms."""

    def setUp(self) -> None:
        self.normalizer = DefaultEntityNormalizer()
        self.extractor = DefaultEntityExtractor(normalizer=self.normalizer)
        self.rel_extractor = DefaultRelationshipExtractor()
        self.rag_augmenter = DefaultGraphRAGAugmenter(extractor=self.extractor)

    def test_01_ontology_enums_and_taxonomies(self) -> None:
        """Verify presence and validity of all core entity and relation taxonomies."""
        # Entity Types
        self.assertEqual(EntityType.ORGANIZATION, "ORGANIZATION")
        self.assertEqual(EntityType.DEPARTMENT, "DEPARTMENT")
        self.assertEqual(EntityType.PROJECT, "PROJECT")
        self.assertEqual(EntityType.POLICY, "POLICY")
        self.assertEqual(EntityType.EMPLOYEE, "EMPLOYEE")
        self.assertEqual(EntityType.TECHNOLOGY, "TECHNOLOGY")
        self.assertEqual(EntityType.TOPIC, "TOPIC")

        # Relation Types
        self.assertEqual(RelationType.WORKS_IN, "WORKS_IN")
        self.assertEqual(RelationType.LEADS, "LEADS")
        self.assertEqual(RelationType.AUTHORED, "AUTHORED")
        self.assertEqual(RelationType.CONTAINS, "CONTAINS")
        self.assertEqual(RelationType.APPLIES_TO, "APPLIES_TO")
        self.assertEqual(RelationType.DEPENDS_ON, "DEPENDS_ON")
        self.assertEqual(RelationType.EXPERT_IN, "EXPERT_IN")

    def test_02_entity_normalization_and_alias_resolution(self) -> None:
        """Verify unicode cleaning, whitespace trimming, and acronym resolution."""
        # Acronym & Alias resolution
        self.assertEqual(self.normalizer.normalize_name("k8s", EntityType.TECHNOLOGY), "Kubernetes")
        self.assertEqual(self.normalizer.normalize_name("KUBERNETES", EntityType.TECHNOLOGY), "Kubernetes")
        self.assertEqual(self.normalizer.normalize_name("hr", EntityType.DEPARTMENT), "Human Resources")
        self.assertEqual(self.normalizer.normalize_name("people ops", EntityType.DEPARTMENT), "Human Resources")
        self.assertEqual(self.normalizer.normalize_name("eng", EntityType.DEPARTMENT), "Engineering")

        # Alias equivalence
        self.assertTrue(self.normalizer.are_aliases("k8s", "Kubernetes"))
        self.assertTrue(self.normalizer.are_aliases("hr", "Human Resources"))
        self.assertFalse(self.normalizer.are_aliases("Docker", "Kubernetes"))

    def test_03_entity_extraction_heuristics(self) -> None:
        """Verify extraction of Projects, Policies, Departments, and Technologies from text."""
        sample_text = (
            "The Project Titan migration is governed by Information Security Policy. "
            "Led by Alice from the Engineering department, the team utilizes Kubernetes and PostgreSQL."
        )
        entities = self.extractor.extract_entities(sample_text)
        names = {e.name for e in entities}
        types = {e.entity_type for e in entities}

        self.assertIn("Project Titan", names)
        self.assertIn("Information Security Policy", names)
        self.assertIn("Engineering", names)
        self.assertIn("Kubernetes", names)
        self.assertIn("Alice", names)

        self.assertIn(EntityType.PROJECT, types)
        self.assertIn(EntityType.POLICY, types)
        self.assertIn(EntityType.DEPARTMENT, types)
        self.assertIn(EntityType.TECHNOLOGY, types)
        self.assertIn(EntityType.EMPLOYEE, types)

    def test_04_relationship_extraction_pipeline(self) -> None:
        """Verify extraction of semantic relations between identified entities."""
        text = "Alice leads Project Titan. Information Security Policy applies to Engineering department."
        entities = self.extractor.extract_entities(text)
        relationships = self.rel_extractor.extract_relationships(text, entities)

        self.assertGreaterEqual(len(relationships), 2)
        rel_map = {(r.source_name, r.relation_type, r.target_name) for r in relationships}

        self.assertIn(("Alice", RelationType.LEADS, "Project Titan"), rel_map)
        self.assertIn(("Information Security Policy", RelationType.APPLIES_TO, "Engineering"), rel_map)

    def test_05_value_objects_and_data_models(self) -> None:
        """Verify graph node, edge, and metrics data structures."""
        node_id = uuid4()
        node = GraphNode(
            id=node_id,
            name="Cloud Infrastructure",
            entity_type=EntityType.TOPIC,
            properties={"tier": "production"},
            in_degree=5,
            out_degree=2,
        )
        self.assertEqual(node.name, "Cloud Infrastructure")
        self.assertEqual(node.in_degree, 5)

        edge_id = uuid4()
        target_id = uuid4()
        edge = GraphEdge(
            id=edge_id,
            source_id=node_id,
            target_id=target_id,
            relation_type=RelationType.DEPENDS_ON,
            weight=0.95,
        )
        self.assertEqual(edge.relation_type, RelationType.DEPENDS_ON)
        self.assertEqual(edge.weight, 0.95)

        metrics = GraphMetrics(
            total_entities=150,
            total_relationships=320,
            density=0.014,
            top_hub="Engineering",
            orphan_count=3,
        )
        self.assertEqual(metrics.total_entities, 150)
        self.assertEqual(metrics.top_hub, "Engineering")

    def test_06_impact_and_expertise_models(self) -> None:
        """Verify ImpactAnalysisResult and ExpertiseRank data models."""
        impact = ImpactAnalysisResult(
            root_entity_id=uuid4(),
            root_entity_name="Core Auth Standard",
            root_entity_type=EntityType.POLICY,
            affected_departments=["Engineering", "Operations"],
            dependent_projects=["Project Titan"],
            impacted_tasks_count=12,
            severity_score=0.88,
            dependency_tree=[{"name": "Project Titan", "depth": 1}],
        )
        self.assertEqual(impact.root_entity_name, "Core Auth Standard")
        self.assertEqual(len(impact.affected_departments), 2)
        self.assertEqual(impact.severity_score, 0.88)

        expert = ExpertiseRank(
            user_id=uuid4(),
            full_name="Alice Alpha",
            department="Engineering",
            score=9.2,
            authored_documents_count=5,
            contributed_projects=["Project Titan"],
            evidence_citations=["Security Handbook v1"],
        )
        self.assertEqual(expert.full_name, "Alice Alpha")
        self.assertEqual(expert.score, 9.2)

    def test_07_graph_rag_context_augmentation(self) -> None:
        """Verify GraphRAG context injection envelope formulation."""
        query = "What is the policy for Project Titan deployment?"
        rag_ctx = self.rag_augmenter.augment_rag_context(query)

        self.assertIn("Project Titan", rag_ctx.entities_found)
        self.assertGreaterEqual(len(rag_ctx.subgraph_triples), 1)
        self.assertIn("[KNOWLEDGE GRAPH CONTEXT]", rag_ctx.context_string)
        self.assertIn("Project Titan", rag_ctx.context_string)


if __name__ == "__main__":
    unittest.main()
