"""KEEP Enterprise Platform — AI Retrieval Authorization Filter.

Enforces resource-level authorization and tenant boundaries on RAG knowledge
candidates and Knowledge Graph entity traversals prior to LLM context assembly.
Derived from devdocs/p1/p1.6.txt Chapter 14 and docs/Architecture/authorization-architecture.md.
"""

from backend.app.services.rag.interfaces import (
    BaseAIAuthorizationFilter,
    KGEntityRecord,
    RAGSecurityContext,
    RetrievalResult,
)


class AIAuthorizationFilter(BaseAIAuthorizationFilter):
    """Concrete implementation of BaseAIAuthorizationFilter.

    Gating principles:
    1. Tenant Isolation: Rejects any candidate or entity whose organization_id does not
       match the calling user's security_context.organization_id.
    2. Document Gating: If allowed_document_ids whitelist is supplied, prunes items not in the set.
    3. Project Scoping: If candidate has a project_id, verifies project accessibility for caller.
    4. KG Entity Gating: Prunes knowledge graph entities derived from documents the user cannot access.
    """

    def filter_knowledge_candidates(
        self,
        candidates: list[RetrievalResult],
        security_context: RAGSecurityContext,
    ) -> list[RetrievalResult]:
        """Prunes RAG retrieval candidates that the caller is not authorized to read."""
        filtered: list[RetrievalResult] = []

        for candidate in candidates:
            # 1. Hard tenant boundary check
            if candidate.organization_id is not None and candidate.organization_id != security_context.organization_id:
                continue

            # 2. Document-level access whitelist check
            if (
                security_context.allowed_document_ids is not None
                and candidate.document_id not in security_context.allowed_document_ids
            ):
                continue

            # 3. Project-level membership scoping
            if (
                candidate.project_id is not None
                and not security_context.can_access_project(candidate.project_id)
            ):
                continue

            # 4. Department-level isolation check
            if (
                candidate.department_id is not None
                and not security_context.can_access_department(candidate.department_id)
            ):
                continue

            filtered.append(candidate)

        return filtered

    def authorize_kg_traversal(
        self,
        entities: list[KGEntityRecord],
        security_context: RAGSecurityContext,
    ) -> list[KGEntityRecord]:
        """Filters Knowledge Graph entities to only those from caller-accessible documents and tenant."""
        authorized: list[KGEntityRecord] = []

        for entity in entities:
            # 1. Tenant boundary check
            if entity.organization_id != security_context.organization_id:
                continue

            # 2. Source document accessibility check
            if (
                entity.source_document_id is not None
                and security_context.allowed_document_ids is not None
                and entity.source_document_id not in security_context.allowed_document_ids
            ):
                continue

            authorized.append(entity)

        return authorized


# Global singleton instance
default_ai_authorization_filter = AIAuthorizationFilter()
