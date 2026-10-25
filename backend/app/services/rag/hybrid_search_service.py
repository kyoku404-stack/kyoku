"""Hybrid Search Service combining dense vector similarity and sparse keyword search.

Owner: Member 2 (Backend & Database Lead)
Domain: /backend/app/services/rag
Specification: devdocs/p2/p2.2.txt (Chapters 6 & 7)
Architecture: docs/Architecture/ai-rag-engine.md
ADR: ADR-035 (Reciprocal Rank Fusion)
"""

import math
import re
from typing import Any
from uuid import UUID

from backend.app.models.document import Document
from backend.app.models.knowledge import DocumentChunk
from backend.app.services.rag.contracts import (
    DefaultRRFHybridFuser,
    HybridCandidateChunk,
    HybridSearchConfig,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class HybridSearchService:
    """Orchestrates multi-tenant dense vector search, sparse keyword search, and RRF rank fusion."""

    def __init__(self, fuser: DefaultRRFHybridFuser | None = None):
        self.fuser = fuser or DefaultRRFHybridFuser()

    @staticmethod
    def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2, strict=False))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        return max(-1.0, min(1.0, dot / (norm1 * norm2)))

    async def search(
        self,
        db: AsyncSession,
        query: str,
        query_vector: list[float] | None,
        organization_id: UUID,
        config: HybridSearchConfig | None = None,
        department_id: UUID | None = None,
        project_id: UUID | None = None,
    ) -> list[HybridCandidateChunk]:
        """Executes tenant-isolated hybrid retrieval and fuses candidate rankings via RRF."""
        active_config = config or HybridSearchConfig()

        # Join DocumentChunk with Document to guarantee organization tenant isolation
        stmt = (
            select(DocumentChunk, Document)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(
                Document.organization_id == organization_id,
                Document.deleted_at.is_(None),
            )
        )

        if project_id and hasattr(Document, "project_id"):
            stmt = stmt.where(Document.project_id == project_id)

        result = await db.execute(stmt)
        rows = result.all()

        if not rows:
            return []

        all_chunks: list[tuple[DocumentChunk, Document]] = rows

        # 1. Dense Vector Search scoring
        dense_candidates: list[HybridCandidateChunk] = []
        if query_vector:
            scored_dense: list[tuple[float, DocumentChunk, Document]] = []
            for chunk, doc in all_chunks:
                if chunk.embedding is not None:
                    # In PostgreSQL with pgvector, vector ops can be used directly;
                    # fallback in-memory cosine similarity guarantees compatibility in SQLite/mock test environments
                    sim = self._cosine_similarity(query_vector, chunk.embedding)
                    scored_dense.append((sim, chunk, doc))

            # Sort descending by cosine similarity
            scored_dense.sort(key=lambda item: item[0], reverse=True)
            for sim, chunk, doc in scored_dense[: active_config.candidate_limit]:
                dense_candidates.append(
                    self._to_candidate(chunk, doc, dense_sim=sim, sparse_score=0.0)
                )

        # 2. Sparse Lexical Search scoring
        query_tokens = set(re.findall(r"\w+", query.lower()))
        scored_sparse: list[tuple[float, DocumentChunk, Document]] = []

        for chunk, doc in all_chunks:
            chunk_tokens = re.findall(r"\w+", chunk.content.lower())
            if not chunk_tokens:
                continue

            # Term frequency & keyword overlap scoring
            overlap = sum(1 for tok in chunk_tokens if tok in query_tokens)
            if overlap > 0:
                score = overlap / len(chunk_tokens) * 10.0
                # Exact phrase bonus
                if query.lower() in chunk.content.lower():
                    score += 5.0
                scored_sparse.append((score, chunk, doc))

        # Sort descending by sparse lexical score
        scored_sparse.sort(key=lambda item: item[0], reverse=True)
        sparse_candidates: list[HybridCandidateChunk] = []
        for score, chunk, doc in scored_sparse[: active_config.candidate_limit]:
            sparse_candidates.append(
                self._to_candidate(chunk, doc, dense_sim=0.0, sparse_score=score)
            )

        # 3. Reciprocal Rank Fusion (RRF)
        fused = self.fuser.fuse(
            dense_results=dense_candidates,
            sparse_results=sparse_candidates,
            config=active_config,
        )
        return fused

    @staticmethod
    def _to_candidate(
        chunk: DocumentChunk,
        doc: Document,
        dense_sim: float,
        sparse_score: float,
    ) -> HybridCandidateChunk:
        meta: dict[str, Any] = chunk.metadata_json if isinstance(chunk.metadata_json, dict) else {}
        page_num = meta.get("page_number")
        section = meta.get("section_title")

        # Inject document scope metadata
        dept_id = getattr(doc, "department_id", None)
        proj_id = getattr(doc, "project_id", None)
        if dept_id:
            meta["department_id"] = str(dept_id)
        if proj_id:
            meta["project_id"] = str(proj_id)
        meta["document_title"] = doc.title

        return HybridCandidateChunk(
            chunk_id=chunk.id,
            document_id=doc.id,
            document_title=doc.title,
            document_version_id=chunk.document_version_id,
            page_number=page_num,
            section_title=section,
            content=chunk.content,
            dense_similarity=dense_sim,
            sparse_score=sparse_score,
            metadata=meta,
            created_at=chunk.created_at,
        )
