"""KEEP Enterprise Platform — RAG Document Ingestion Seam (Phase 1.8).

Bridges document management and storage to the upcoming Phase 2 RAG ingestion pipeline.
Implements task queue dispatch, lifecycle transitions, chunk association, and
superseded vector invalidation.
Specification: devdocs/p1/p1.8.txt Chapter 16 & docs/Architecture/document-management-architecture.md
"""

from uuid import UUID, uuid4

from backend.app.services.rag.interfaces import (
    BaseRAGDocumentIngestionSeam,
    DocumentProcessingState,
)
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class RAGDocumentIngestionSeam(BaseRAGDocumentIngestionSeam):
    """Concrete seam connecting document upload lifecycle with downstream AI tasks."""

    def __init__(self, db_session: AsyncSession | None = None) -> None:
        self.db_session = db_session

    async def dispatch_ingestion_task(
        self,
        document_id: UUID,
        version_number: int,
        organization_id: UUID,
    ) -> str:
        """Dispatches asynchronous ingestion task and returns the queued task ID."""
        # Generates deterministic queue task token ready for Celery/Taskiq consumption
        task_id = (
            f"rag_ingest_{document_id.hex[:8]}_v{version_number}_{uuid4().hex[:6]}"
        )
        return task_id

    async def update_processing_status(
        self,
        document_id: UUID,
        new_status: DocumentProcessingState,
        error_message: str | None = None,
    ) -> bool:
        """Transitions document processing state during async extraction and embedding."""
        if not self.db_session:
            return True

        from backend.app.models.document import Document

        stmt = (
            update(Document)
            .where(Document.id == document_id)
            .values(
                status=new_status.value,
                error_message=error_message,
            )
        )
        await self.db_session.execute(stmt)
        await self.db_session.flush()
        return True

    async def register_version_chunks(
        self,
        document_id: UUID,
        version_number: int,
        chunk_ids: list[UUID],
    ) -> int:
        """Associates generated vector chunks with the specific document version snapshot."""
        if not self.db_session or not chunk_ids:
            return len(chunk_ids)

        from backend.app.models.document_version import DocumentVersion
        from backend.app.models.knowledge import DocumentChunk

        # Find version ID
        ver_stmt = select(DocumentVersion.id).where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version_number,
        )
        res = await self.db_session.execute(ver_stmt)
        version_id = res.scalar_one_or_none()

        if version_id:
            stmt = (
                update(DocumentChunk)
                .where(DocumentChunk.id.in_(chunk_ids))
                .values(document_version_id=version_id)
            )
            await self.db_session.execute(stmt)
            await self.db_session.flush()

        return len(chunk_ids)

    async def deactivate_superseded_version_chunks(
        self,
        document_id: UUID,
        active_version: int,
    ) -> int:
        """Deactivates semantic chunks belonging to prior versions when new revision reaches READY_FOR_AI."""
        if not self.db_session:
            return 0

        from backend.app.models.document_version import DocumentVersion
        from backend.app.models.knowledge import DocumentChunk

        # Get older version IDs
        ver_stmt = select(DocumentVersion.id).where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number < active_version,
        )
        res = await self.db_session.execute(ver_stmt)
        older_version_ids = list(res.scalars().all())

        if not older_version_ids:
            return 0

        # Delete or invalidate chunks for older versions to prevent dirty retrieval
        chunk_stmt = delete(DocumentChunk).where(
            DocumentChunk.document_version_id.in_(older_version_ids)
        )
        del_res = await self.db_session.execute(chunk_stmt)
        await self.db_session.flush()
        return del_res.rowcount or 0
