"""KEEP Enterprise Platform — File Storage Service (Phase 1.8).

Implements multi-tenant physical storage abstraction, organization isolation,
storage quota calculations, and preview generation path resolution.
Specification: devdocs/p1/p1.8.txt Chapters 7 & 8 & docs/Architecture/document-management-architecture.md Section 4
"""

import os
from pathlib import Path
from uuid import UUID

from backend.app.core.config import settings
from backend.app.services.rag.interfaces import BaseFileStorageService


class LocalStorageService(BaseFileStorageService):
    """Local filesystem implementation of BaseFileStorageService with tenant directory isolation."""

    def __init__(self, base_path: str | Path | None = None) -> None:
        self.base_path = Path(
            base_path or getattr(settings, "STORAGE_ROOT", "./storage")
        ).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_tenant_root(self, organization_id: UUID) -> Path:
        """Returns the organization's isolated root directory."""
        return self.base_path / str(organization_id)

    def _get_document_version_dir(
        self, organization_id: UUID, document_id: UUID, version: int
    ) -> Path:
        """Returns directory: storage/{org_id}/documents/{doc_id}/v{version}/."""
        return (
            self._get_tenant_root(organization_id)
            / "documents"
            / str(document_id)
            / f"v{version}"
        )

    def _get_previews_dir(
        self, organization_id: UUID, document_id: UUID, version: int
    ) -> Path:
        """Returns directory: storage/{org_id}/previews/{doc_id}/v{version}/."""
        return (
            self._get_tenant_root(organization_id)
            / "previews"
            / str(document_id)
            / f"v{version}"
        )

    async def save_file(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        filename: str,
        content: bytes,
    ) -> str:
        """Stores binary document content in organization-isolated path and returns storage path."""
        target_dir = self._get_document_version_dir(
            organization_id, document_id, version
        )
        target_dir.mkdir(parents=True, exist_ok=True)

        target_file = target_dir / filename
        target_file.write_bytes(content)
        return str(target_file)

    async def get_file_path(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        filename: str,
    ) -> str:
        """Resolves physical filesystem path for a document version."""
        target_file = (
            self._get_document_version_dir(organization_id, document_id, version)
            / filename
        )
        return str(target_file)

    async def read_file(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        filename: str,
    ) -> bytes:
        """Reads binary document bytes for streaming download or preview generation."""
        target_file = Path(
            await self.get_file_path(organization_id, document_id, version, filename)
        )
        if not target_file.is_file():
            raise FileNotFoundError(f"Stored file not found: {target_file}")
        return target_file.read_bytes()

    async def delete_file(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        filename: str,
    ) -> bool:
        """Deletes binary document version from physical storage."""
        target_file = Path(
            await self.get_file_path(organization_id, document_id, version, filename)
        )
        if target_file.is_file():
            target_file.unlink()
            return True
        return False

    async def get_storage_usage(self, organization_id: UUID) -> int:
        """Aggregates total bytes stored for the given organization tenant."""
        tenant_root = self._get_tenant_root(organization_id)
        if not tenant_root.is_dir():
            return 0

        total_bytes = 0
        for dirpath, _, filenames in os.walk(tenant_root):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_bytes += os.path.getsize(fp)
        return total_bytes

    async def check_quota(
        self,
        organization_id: UUID,
        additional_bytes: int,
        quota_limit: int,
    ) -> bool:
        """Verifies if tenant storage quota allows storing additional bytes."""
        current_usage = await self.get_storage_usage(organization_id)
        return (current_usage + additional_bytes) <= quota_limit

    def generate_preview_path(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        preview_format: str = "pdf",
    ) -> str:
        """Generates tenant-isolated path for cached preview artifact."""
        preview_dir = self._get_previews_dir(organization_id, document_id, version)
        preview_dir.mkdir(parents=True, exist_ok=True)
        return str(preview_dir / f"preview.{preview_format}")

    def save_preview(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        preview_format: str,
        content: bytes,
    ) -> str:
        """Saves generated preview artifact into preview cache."""
        path = Path(
            self.generate_preview_path(
                organization_id, document_id, version, preview_format
            )
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)

    def read_preview(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        preview_format: str,
    ) -> bytes | None:
        """Reads cached preview artifact if available."""
        path = Path(
            self.generate_preview_path(
                organization_id, document_id, version, preview_format
            )
        )
        if path.is_file():
            return path.read_bytes()
        return None
