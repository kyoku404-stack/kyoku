"""KEEP Enterprise Platform — Document & Version Repositories (Phase 1.8).

Implements the repository pattern for Document container entities and immutable
DocumentVersion snapshots with tenant boundary filtering, search, sorting, and pagination.
Specification: devdocs/p1/p1.8.txt & docs/database/database-schema.md
"""

from typing import Any
from uuid import UUID

from backend.app.models.document import Document
from backend.app.models.document_version import DocumentVersion
from backend.app.repositories.base import BaseRepository
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class DocumentRepository(BaseRepository[Document, Any, Any]):
    """Repository handling Document metadata entity operations."""

    def __init__(self, model: type[Document] | None = None) -> None:
        super().__init__(model or Document)

    async def get_by_id(
        self,
        db: AsyncSession,
        document_id: UUID,
        organization_id: UUID | None = None,
        include_versions: bool = False,
    ) -> Document | None:
        """Retrieves a single document by ID, optionally scoped to tenant and with versions."""
        stmt = select(Document).where(Document.id == document_id)
        if organization_id is not None:
            stmt = stmt.where(Document.organization_id == organization_id)

        if include_versions:
            stmt = stmt.options(
                selectinload(Document.versions),
                selectinload(Document.uploader),
                selectinload(Document.project),
            )
        else:
            stmt = stmt.options(
                selectinload(Document.uploader),
                selectinload(Document.project),
            )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_checksum(
        self,
        db: AsyncSession,
        organization_id: UUID,
        checksum_sha256: str,
    ) -> Document | None:
        """Finds an active document with an identical cryptographic checksum within the tenant."""
        stmt = (
            select(Document)
            .where(
                Document.organization_id == organization_id,
                Document.checksum_sha256 == checksum_sha256,
                Document.is_deleted == False,
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        db: AsyncSession,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        category: str | None = None,
        file_type: str | None = None,
        project_id: UUID | None = None,
        uploader_id: UUID | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Document], int]:
        """Lists tenant documents with dynamic filtering, full-text search, and pagination."""
        query = select(Document).where(
            Document.organization_id == organization_id,
            Document.is_deleted == False,
        )

        if status:
            query = query.where(Document.status == status)
        if category:
            query = query.where(Document.category == category)
        if file_type:
            # Match normalized extension or substring
            clean_type = file_type.lstrip(".").lower()
            query = query.where(Document.file_type == clean_type)
        if project_id:
            query = query.where(Document.project_id == project_id)
        if uploader_id:
            query = query.where(Document.uploader_id == uploader_id)
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Document.title.ilike(term),
                    Document.filename.ilike(term),
                    Document.original_filename.ilike(term),
                )
            )

        # Count total matching rows
        count_stmt = select(func.count()).select_from(query.subquery())
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        # Sorting
        sort_col = getattr(Document, sort_by, Document.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        # Pagination & Eager loading
        offset = (page - 1) * page_size
        query = (
            query.offset(offset)
            .limit(page_size)
            .options(
                selectinload(Document.uploader),
                selectinload(Document.project),
            )
        )

        result = await db.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def get_by_tenant(
        self,
        db: AsyncSession,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Document]:
        """Retrieves documents isolated to a specific organization tenant (backward-compat)."""
        stmt = (
            select(Document)
            .where(
                Document.organization_id == organization_id,
                Document.is_deleted == False,
            )
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(Document.uploader),
                selectinload(Document.project),
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


class DocumentVersionRepository(BaseRepository[DocumentVersion, Any, Any]):
    """Repository handling immutable DocumentVersion snapshot operations."""

    def __init__(self, model: type[DocumentVersion] | None = None) -> None:
        super().__init__(model or DocumentVersion)

    async def get_version(
        self,
        db: AsyncSession,
        document_id: UUID,
        version_number: int,
    ) -> DocumentVersion | None:
        """Retrieves a specific version snapshot of a document."""
        stmt = select(DocumentVersion).where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version_number,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_versions(
        self,
        db: AsyncSession,
        document_id: UUID,
    ) -> list[DocumentVersion]:
        """Returns all version revisions of a document in descending chronological order."""
        stmt = (
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
