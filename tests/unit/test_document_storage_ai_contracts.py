"""Unit Tests for Phase 1.8 Document Upload, File Management & Storage System Contracts.

Verifies:
1. DocumentProcessingState enumeration, terminal states, and valid/invalid state transitions.
2. DocumentCategory enumeration covering all 10 enterprise document categories.
3. SupportedFileType, FILE_TYPE_MIME_MAP, MAX_FILE_SIZES, and MAGIC_BYTE_SIGNATURES.
4. DocumentMetadata, DocumentVersionInfo, and DocumentValidationResult dataclasses.
5. Action-based document permissions (document.download, document.preview, document.version)
   and hierarchical role permission inheritance across Viewer, Employee, Manager, Admin, and SuperAdmin.
6. BaseDocumentValidator implementation: path traversal sanitization, size limits, format gating,
   magic byte sniffing, and SHA-256 checksum calculation.
7. BaseFileStorageService implementation: tenant-isolated directory layout, save/read/delete,
   quota calculation, and preview path generation.
8. BaseRAGDocumentIngestionSeam implementation: Celery task dispatch, status transitions,
   and version-scoped vector chunk registration and deactivation.

Owner: Member 1 (Project Lead & AI Architect)
Sub-phase: Phase 1.8 Document Upload, File Management & Storage System
Specification: devdocs/p1/p1.8.txt (Chapters 1–21)
Architecture: docs/Architecture/document-management-architecture.md
ADRs: ADR-023, ADR-024, ADR-025
"""

import hashlib
import re
import unittest
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.app.services.ai import (
    EMPLOYEE_PERMISSIONS,
    ORG_ADMIN_PERMISSIONS,
    PROJECT_MANAGER_PERMISSIONS,
    ROLE_PERMISSIONS,
    SUPER_ADMIN_PERMISSIONS,
    VIEWER_PERMISSIONS,
    AIPermission,
    UserRole,
)
from backend.app.services.rag import (
    FILE_TYPE_MIME_MAP,
    MAGIC_BYTE_SIGNATURES,
    MAX_FILE_SIZES,
    BaseDocumentValidator,
    BaseFileStorageService,
    BaseRAGDocumentIngestionSeam,
    DocumentCategory,
    DocumentMetadata,
    DocumentProcessingState,
    DocumentValidationResult,
    DocumentVersionInfo,
    SupportedFileType,
)


class MockDocumentValidator(BaseDocumentValidator):
    """Concrete test implementation of BaseDocumentValidator."""

    def sanitize_filename(self, filename: str) -> str:
        # Strip path traversal sequences and backslashes
        cleaned = filename.replace("\\", "/").split("/")[-1]
        # Remove illegal filename characters
        cleaned = re.sub(r'[\0:*?"<>|]', "", cleaned)
        return cleaned.strip() or "unnamed_document"

    def compute_checksum(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def verify_magic_bytes(
        self,
        header_bytes: bytes,
        expected_type: SupportedFileType,
    ) -> bool:
        signatures = MAGIC_BYTE_SIGNATURES.get(expected_type)
        if not signatures:
            # Plain text, CSV, markdown have no fixed magic bytes
            return True
        return any(header_bytes.startswith(sig) for sig in signatures)

    def validate_file_attributes(
        self,
        filename: str,
        file_size: int,
        mime_type: str | None = None,
    ) -> DocumentValidationResult:
        sanitized = self.sanitize_filename(filename)
        extension = sanitized.rsplit(".", 1)[-1].lower() if "." in sanitized else ""

        # Check supported extension
        try:
            detected_type = SupportedFileType(extension)
        except ValueError:
            return DocumentValidationResult(
                is_valid=False,
                sanitized_filename=sanitized,
                error_code="UNSUPPORTED_FILE_TYPE",
                error_message=f"File extension '.{extension}' is not supported.",
            )

        # Check file size limit
        max_size = MAX_FILE_SIZES.get(detected_type, 20 * 1024 * 1024)
        if file_size > max_size:
            return DocumentValidationResult(
                is_valid=False,
                sanitized_filename=sanitized,
                detected_file_type=detected_type,
                file_size_bytes=file_size,
                error_code="FILE_SIZE_EXCEEDED",
                error_message=f"File size {file_size} exceeds maximum limit of {max_size} bytes.",
            )

        expected_mime = FILE_TYPE_MIME_MAP[detected_type]
        return DocumentValidationResult(
            is_valid=True,
            sanitized_filename=sanitized,
            detected_file_type=detected_type,
            detected_mime_type=mime_type or expected_mime,
            file_size_bytes=file_size,
        )


class MockFileStorageService(BaseFileStorageService):
    """Concrete test implementation of BaseFileStorageService with tenant isolation."""

    def __init__(self) -> None:
        # Maps storage_path -> binary content
        self.storage: dict[str, bytes] = {}

    def _build_path(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        filename: str,
    ) -> str:
        return f"storage/{organization_id}/documents/{document_id}/v{version}/{filename}"

    async def save_file(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        filename: str,
        content: bytes,
    ) -> str:
        path = self._build_path(organization_id, document_id, version, filename)
        self.storage[path] = content
        return path

    async def get_file_path(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        filename: str,
    ) -> str:
        return self._build_path(organization_id, document_id, version, filename)

    async def read_file(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        filename: str,
    ) -> bytes:
        path = self._build_path(organization_id, document_id, version, filename)
        if path not in self.storage:
            raise FileNotFoundError(f"File at {path} does not exist.")
        return self.storage[path]

    async def delete_file(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        filename: str,
    ) -> bool:
        path = self._build_path(organization_id, document_id, version, filename)
        if path in self.storage:
            del self.storage[path]
            return True
        return False

    async def get_storage_usage(self, organization_id: UUID) -> int:
        prefix = f"storage/{organization_id}/"
        return sum(len(data) for path, data in self.storage.items() if path.startswith(prefix))

    async def check_quota(
        self,
        organization_id: UUID,
        additional_bytes: int,
        quota_limit: int,
    ) -> bool:
        current_usage = await self.get_storage_usage(organization_id)
        return (current_usage + additional_bytes) <= quota_limit

    def generate_preview_path(
        self,
        organization_id: UUID,
        document_id: UUID,
        version: int,
        preview_format: str = "pdf",
    ) -> str:
        return f"storage/{organization_id}/previews/{document_id}/v{version}/preview.{preview_format}"


class MockRAGDocumentIngestionSeam(BaseRAGDocumentIngestionSeam):
    """Concrete test implementation of BaseRAGDocumentIngestionSeam."""

    def __init__(self) -> None:
        self.tasks: dict[str, dict] = {}
        self.document_statuses: dict[UUID, DocumentProcessingState] = {}
        self.version_chunks: dict[tuple[UUID, int], list[UUID]] = {}
        self.active_chunks: set[UUID] = set()

    async def dispatch_ingestion_task(
        self,
        document_id: UUID,
        version_number: int,
        organization_id: UUID,
    ) -> str:
        task_id = f"task_{uuid4()}"
        self.tasks[task_id] = {
            "document_id": document_id,
            "version_number": version_number,
            "organization_id": organization_id,
            "status": "QUEUED",
        }
        self.document_statuses[document_id] = DocumentProcessingState.QUEUED
        return task_id

    async def update_processing_status(
        self,
        document_id: UUID,
        new_status: DocumentProcessingState,
        error_message: str | None = None,
    ) -> bool:
        current = self.document_statuses.get(document_id, DocumentProcessingState.PENDING)
        if not current.can_transition_to(new_status):
            return False
        self.document_statuses[document_id] = new_status
        return True

    async def register_version_chunks(
        self,
        document_id: UUID,
        version_number: int,
        chunk_ids: list[UUID],
    ) -> int:
        key = (document_id, version_number)
        self.version_chunks[key] = chunk_ids
        self.active_chunks.update(chunk_ids)
        return len(chunk_ids)

    async def deactivate_superseded_version_chunks(
        self,
        document_id: UUID,
        active_version: int,
    ) -> int:
        deactivated = 0
        for (doc_id, ver), chunk_ids in self.version_chunks.items():
            if doc_id == document_id and ver < active_version:
                for cid in chunk_ids:
                    if cid in self.active_chunks:
                        self.active_chunks.remove(cid)
                        deactivated += 1
        return deactivated


# ==============================================================================
# Unit Test Cases
# ==============================================================================


class TestDocumentProcessingState(unittest.TestCase):
    """Verifies DocumentProcessingState enumeration and transition logic."""

    def test_state_members(self) -> None:
        expected = {
            "PENDING",
            "VALIDATED",
            "AWAITING_PROCESSING",
            "QUEUED",
            "EXTRACTING",
            "CHUNKING",
            "EMBEDDING",
            "READY_FOR_AI",
            "UPDATED",
            "FAILED",
            "ARCHIVED",
            "DELETED",
        }
        actual = {state.value for state in DocumentProcessingState}
        self.assertEqual(expected, actual)

    def test_terminal_and_ai_ready_states(self) -> None:
        self.assertTrue(DocumentProcessingState.FAILED.is_terminal())
        self.assertTrue(DocumentProcessingState.DELETED.is_terminal())
        self.assertFalse(DocumentProcessingState.READY_FOR_AI.is_terminal())
        self.assertFalse(DocumentProcessingState.PENDING.is_terminal())

        self.assertTrue(DocumentProcessingState.READY_FOR_AI.is_ai_ready())
        self.assertFalse(DocumentProcessingState.AWAITING_PROCESSING.is_ai_ready())
        self.assertFalse(DocumentProcessingState.CHUNKING.is_ai_ready())

    def test_valid_forward_transitions(self) -> None:
        self.assertTrue(DocumentProcessingState.PENDING.can_transition_to(DocumentProcessingState.VALIDATED))
        self.assertTrue(
            DocumentProcessingState.VALIDATED.can_transition_to(DocumentProcessingState.AWAITING_PROCESSING)
        )
        self.assertTrue(
            DocumentProcessingState.AWAITING_PROCESSING.can_transition_to(DocumentProcessingState.QUEUED)
        )
        self.assertTrue(DocumentProcessingState.QUEUED.can_transition_to(DocumentProcessingState.EXTRACTING))
        self.assertTrue(DocumentProcessingState.EXTRACTING.can_transition_to(DocumentProcessingState.CHUNKING))
        self.assertTrue(DocumentProcessingState.CHUNKING.can_transition_to(DocumentProcessingState.EMBEDDING))
        self.assertTrue(DocumentProcessingState.EMBEDDING.can_transition_to(DocumentProcessingState.READY_FOR_AI))
        self.assertTrue(DocumentProcessingState.READY_FOR_AI.can_transition_to(DocumentProcessingState.UPDATED))
        self.assertTrue(DocumentProcessingState.UPDATED.can_transition_to(DocumentProcessingState.QUEUED))

    def test_failure_and_archival_transitions(self) -> None:
        self.assertTrue(DocumentProcessingState.PENDING.can_transition_to(DocumentProcessingState.FAILED))
        self.assertTrue(DocumentProcessingState.EXTRACTING.can_transition_to(DocumentProcessingState.FAILED))
        self.assertTrue(
            DocumentProcessingState.AWAITING_PROCESSING.can_transition_to(DocumentProcessingState.ARCHIVED)
        )
        self.assertTrue(
            DocumentProcessingState.ARCHIVED.can_transition_to(DocumentProcessingState.AWAITING_PROCESSING)
        )
        self.assertTrue(DocumentProcessingState.FAILED.can_transition_to(DocumentProcessingState.AWAITING_PROCESSING))
        self.assertTrue(DocumentProcessingState.READY_FOR_AI.can_transition_to(DocumentProcessingState.DELETED))

    def test_invalid_transitions(self) -> None:
        # Cannot jump from PENDING directly to READY_FOR_AI
        self.assertFalse(DocumentProcessingState.PENDING.can_transition_to(DocumentProcessingState.READY_FOR_AI))
        # Terminal DELETED cannot transition to anything
        self.assertFalse(DocumentProcessingState.DELETED.can_transition_to(DocumentProcessingState.PENDING))
        self.assertFalse(DocumentProcessingState.DELETED.can_transition_to(DocumentProcessingState.AWAITING_PROCESSING))
        # READY_FOR_AI cannot transition back to PENDING or CHUNKING
        self.assertFalse(DocumentProcessingState.READY_FOR_AI.can_transition_to(DocumentProcessingState.PENDING))
        self.assertFalse(DocumentProcessingState.READY_FOR_AI.can_transition_to(DocumentProcessingState.CHUNKING))


class TestDocumentCategoryAndTypes(unittest.TestCase):
    """Verifies DocumentCategory, SupportedFileType, MIME mapping, and size limits."""

    def test_document_categories(self) -> None:
        categories = {cat.value for cat in DocumentCategory}
        self.assertEqual(len(categories), 10)
        self.assertIn("POLICIES", categories)
        self.assertIn("REPORTS", categories)
        self.assertIn("MEETING_MINUTES", categories)
        self.assertIn("RESEARCH", categories)
        self.assertIn("LEGAL", categories)
        self.assertIn("FINANCE", categories)
        self.assertIn("HR", categories)
        self.assertIn("TECHNICAL_DOCUMENTATION", categories)
        self.assertIn("PRESENTATIONS", categories)
        self.assertIn("TRAINING_MATERIALS", categories)

    def test_supported_file_types(self) -> None:
        types = {ft.value for ft in SupportedFileType}
        self.assertIn("pdf", types)
        self.assertIn("docx", types)
        self.assertIn("txt", types)
        self.assertIn("md", types)
        self.assertIn("pptx", types)
        self.assertIn("xlsx", types)
        self.assertIn("csv", types)
        self.assertIn("png", types)
        self.assertIn("jpg", types)
        self.assertIn("jpeg", types)
        self.assertIn("webp", types)

    def test_file_type_mime_and_size_maps(self) -> None:
        for ft in SupportedFileType:
            self.assertIn(ft, FILE_TYPE_MIME_MAP)
            self.assertTrue(len(FILE_TYPE_MIME_MAP[ft]) > 0)
            self.assertIn(ft, MAX_FILE_SIZES)
            self.assertTrue(MAX_FILE_SIZES[ft] >= 20 * 1024 * 1024)

        # PDF and PPTX allow 100MB
        self.assertEqual(MAX_FILE_SIZES[SupportedFileType.PDF], 100 * 1024 * 1024)
        self.assertEqual(MAX_FILE_SIZES[SupportedFileType.PPTX], 100 * 1024 * 1024)
        # DOCX allows 50MB
        self.assertEqual(MAX_FILE_SIZES[SupportedFileType.DOCX], 50 * 1024 * 1024)

    def test_magic_byte_signatures(self) -> None:
        self.assertEqual(MAGIC_BYTE_SIGNATURES[SupportedFileType.PDF], [b"%PDF-"])
        self.assertEqual(MAGIC_BYTE_SIGNATURES[SupportedFileType.DOCX], [b"PK\x03\x04"])
        self.assertEqual(MAGIC_BYTE_SIGNATURES[SupportedFileType.PNG], [b"\x89PNG\r\n\x1a\n"])


class TestDocumentDataContracts(unittest.TestCase):
    """Verifies DocumentMetadata, DocumentVersionInfo, and DocumentValidationResult."""

    def test_document_metadata_dataclass(self) -> None:
        doc_id = uuid4()
        org_id = uuid4()
        uploader_id = uuid4()

        meta = DocumentMetadata(
            document_id=doc_id,
            organization_id=org_id,
            uploader_id=uploader_id,
            filename="architecture.pdf",
            original_filename="Architecture Spec v1.pdf",
            file_type="pdf",
            mime_type="application/pdf",
            file_size_bytes=1048576,
            checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            storage_path=f"storage/{org_id}/documents/{doc_id}/v1/architecture.pdf",
            category=DocumentCategory.TECHNICAL_DOCUMENTATION,
            tags=["architecture", "spec"],
        )

        self.assertEqual(meta.document_id, doc_id)
        self.assertEqual(meta.version_number, 1)
        self.assertEqual(meta.category, DocumentCategory.TECHNICAL_DOCUMENTATION)
        self.assertEqual(meta.status, DocumentProcessingState.AWAITING_PROCESSING)
        self.assertFalse(meta.ai_ready)
        self.assertEqual(meta.chunk_count, 0)

    def test_document_version_info_dataclass(self) -> None:
        ver_id = uuid4()
        doc_id = uuid4()
        uploader_id = uuid4()
        now = datetime.now(UTC)

        ver = DocumentVersionInfo(
            version_id=ver_id,
            document_id=doc_id,
            version_number=2,
            file_path="storage/org/doc/v2/file.pdf",
            file_size_bytes=2048000,
            checksum_sha256="abcdef1234567890",
            mime_type="application/pdf",
            uploader_id=uploader_id,
            change_notes="Updated section 3 diagrams.",
            created_at=now,
        )

        self.assertEqual(ver.version_number, 2)
        self.assertEqual(ver.change_notes, "Updated section 3 diagrams.")
        self.assertEqual(ver.created_at, now)

    def test_document_validation_result_dataclass(self) -> None:
        valid_res = DocumentValidationResult(
            is_valid=True,
            sanitized_filename="document.pdf",
            detected_file_type=SupportedFileType.PDF,
            detected_mime_type="application/pdf",
            file_size_bytes=5000,
            checksum_sha256="12345",
        )
        self.assertTrue(valid_res.is_valid)
        self.assertIsNone(valid_res.error_code)

        invalid_res = DocumentValidationResult(
            is_valid=False,
            sanitized_filename="malware.exe",
            error_code="UNSUPPORTED_FILE_TYPE",
            error_message="Unsupported format",
        )
        self.assertFalse(invalid_res.is_valid)
        self.assertEqual(invalid_res.error_code, "UNSUPPORTED_FILE_TYPE")


class TestDocumentPermissionsAndRoles(unittest.TestCase):
    """Verifies Phase 1.8 document permissions and role hierarchy inheritance."""

    def test_permission_enum_values(self) -> None:
        self.assertEqual(AIPermission.DOCUMENT_DOWNLOAD.value, "document.download")
        self.assertEqual(AIPermission.DOCUMENT_PREVIEW.value, "document.preview")
        self.assertEqual(AIPermission.DOCUMENT_VERSION.value, "document.version")

    def test_viewer_role_permissions(self) -> None:
        self.assertIn("document.read", VIEWER_PERMISSIONS)
        self.assertIn("document.download", VIEWER_PERMISSIONS)
        self.assertIn("document.preview", VIEWER_PERMISSIONS)
        # Viewer must NOT be able to create, update, delete, or version
        self.assertNotIn("document.create", VIEWER_PERMISSIONS)
        self.assertNotIn("document.update", VIEWER_PERMISSIONS)
        self.assertNotIn("document.version", VIEWER_PERMISSIONS)
        self.assertNotIn("document.delete", VIEWER_PERMISSIONS)

    def test_employee_role_permissions(self) -> None:
        # Employee inherits Viewer permissions
        self.assertTrue(VIEWER_PERMISSIONS.issubset(EMPLOYEE_PERMISSIONS))
        # Employee can create, update, and upload versions
        self.assertIn("document.create", EMPLOYEE_PERMISSIONS)
        self.assertIn("document.update", EMPLOYEE_PERMISSIONS)
        self.assertIn("document.version", EMPLOYEE_PERMISSIONS)
        # Employee cannot delete documents generally (requires PM or owner override)
        self.assertNotIn("document.delete", EMPLOYEE_PERMISSIONS)

    def test_project_manager_and_admin_permissions(self) -> None:
        # Project Manager inherits Employee and gets delete
        self.assertTrue(EMPLOYEE_PERMISSIONS.issubset(PROJECT_MANAGER_PERMISSIONS))
        self.assertIn("document.delete", PROJECT_MANAGER_PERMISSIONS)

        # OrgAdmin and SuperAdmin inherit all document permissions
        self.assertTrue(PROJECT_MANAGER_PERMISSIONS.issubset(ORG_ADMIN_PERMISSIONS))
        self.assertTrue(ORG_ADMIN_PERMISSIONS.issubset(SUPER_ADMIN_PERMISSIONS))
        self.assertTrue(ROLE_PERMISSIONS[UserRole.ORGANIZATION_ADMIN.value].issuperset(VIEWER_PERMISSIONS))


class TestMockDocumentValidator(unittest.TestCase):
    """Verifies BaseDocumentValidator behavior using MockDocumentValidator."""

    def setUp(self) -> None:
        self.validator = MockDocumentValidator()

    def test_filename_sanitization_and_path_traversal(self) -> None:
        # Traversal attempts
        self.assertEqual(self.validator.sanitize_filename("../../etc/passwd.pdf"), "passwd.pdf")
        self.assertEqual(self.validator.sanitize_filename("..\\..\\windows\\system32\\cmd.exe.docx"), "cmd.exe.docx")
        # Reserved OS characters
        self.assertEqual(self.validator.sanitize_filename('report:2026*"test"?.pdf'), "report2026test.pdf")
        # Empty filename fallback
        self.assertEqual(self.validator.sanitize_filename("../../../"), "unnamed_document")

    def test_checksum_computation(self) -> None:
        data = b"Hello, KEEP Enterprise Document System!"
        expected = hashlib.sha256(data).hexdigest()
        self.assertEqual(self.validator.compute_checksum(data), expected)

    def test_magic_byte_verification(self) -> None:
        valid_pdf_header = b"%PDF-1.7 header content"
        invalid_pdf_header = b"\x7fELF binary executable"
        self.assertTrue(self.validator.verify_magic_bytes(valid_pdf_header, SupportedFileType.PDF))
        self.assertFalse(self.validator.verify_magic_bytes(invalid_pdf_header, SupportedFileType.PDF))

        valid_png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        self.assertTrue(self.validator.verify_magic_bytes(valid_png_header, SupportedFileType.PNG))
        self.assertFalse(self.validator.verify_magic_bytes(valid_pdf_header, SupportedFileType.PNG))

    def test_validate_attributes_success(self) -> None:
        res = self.validator.validate_file_attributes("Quarterly_Report.pdf", 25 * 1024 * 1024)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.detected_file_type, SupportedFileType.PDF)
        self.assertEqual(res.detected_mime_type, "application/pdf")
        self.assertEqual(res.sanitized_filename, "Quarterly_Report.pdf")

    def test_validate_attributes_unsupported_type(self) -> None:
        res = self.validator.validate_file_attributes("script.sh", 1024)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.error_code, "UNSUPPORTED_FILE_TYPE")

    def test_validate_attributes_size_exceeded(self) -> None:
        # 105MB PDF exceeds 100MB limit
        res = self.validator.validate_file_attributes("huge.pdf", 105 * 1024 * 1024)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.error_code, "FILE_SIZE_EXCEEDED")


class TestMockFileStorageService(unittest.IsolatedAsyncioTestCase):
    """Verifies BaseFileStorageService behavior using MockFileStorageService."""

    async def asyncSetUp(self) -> None:
        self.storage = MockFileStorageService()
        self.org_id = uuid4()
        self.doc_id = uuid4()

    async def test_save_read_and_delete_file(self) -> None:
        content = b"PDF binary stream test content."
        filename = "contract.pdf"

        # Save
        saved_path = await self.storage.save_file(
            self.org_id, self.doc_id, version=1, filename=filename, content=content
        )
        expected_path = f"storage/{self.org_id}/documents/{self.doc_id}/v1/{filename}"
        self.assertEqual(saved_path, expected_path)

        # Read
        read_bytes = await self.storage.read_file(self.org_id, self.doc_id, version=1, filename=filename)
        self.assertEqual(read_bytes, content)

        # Delete
        deleted = await self.storage.delete_file(self.org_id, self.doc_id, version=1, filename=filename)
        self.assertTrue(deleted)

        # Read after delete raises FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            await self.storage.read_file(self.org_id, self.doc_id, version=1, filename=filename)

    async def test_tenant_storage_usage_and_quota(self) -> None:
        quota = 1000  # 1000 bytes quota
        file_bytes = b"X" * 400

        # Save 400 bytes
        await self.storage.save_file(self.org_id, self.doc_id, 1, "f1.txt", file_bytes)
        usage = await self.storage.get_storage_usage(self.org_id)
        self.assertEqual(usage, 400)

        # Additional 500 bytes allowed (400 + 500 <= 1000)
        self.assertTrue(await self.storage.check_quota(self.org_id, 500, quota))
        # Additional 700 bytes rejected (400 + 700 > 1000)
        self.assertFalse(await self.storage.check_quota(self.org_id, 700, quota))

    def test_preview_path_generation(self) -> None:
        path = self.storage.generate_preview_path(self.org_id, self.doc_id, version=2, preview_format="html")
        expected = f"storage/{self.org_id}/previews/{self.doc_id}/v2/preview.html"
        self.assertEqual(path, expected)


class TestMockRAGDocumentIngestionSeam(unittest.IsolatedAsyncioTestCase):
    """Verifies BaseRAGDocumentIngestionSeam linking Phase 1.8 to Phase 2."""

    async def asyncSetUp(self) -> None:
        self.seam = MockRAGDocumentIngestionSeam()
        self.doc_id = uuid4()
        self.org_id = uuid4()

    async def test_dispatch_ingestion_task(self) -> None:
        task_id = await self.seam.dispatch_ingestion_task(self.doc_id, version_number=1, organization_id=self.org_id)
        self.assertTrue(task_id.startswith("task_"))
        self.assertEqual(self.seam.document_statuses[self.doc_id], DocumentProcessingState.QUEUED)

    async def test_processing_status_state_transitions(self) -> None:
        # Initial: QUEUED
        await self.seam.dispatch_ingestion_task(self.doc_id, version_number=1, organization_id=self.org_id)

        # Transition QUEUED -> EXTRACTING -> CHUNKING -> EMBEDDING -> READY_FOR_AI
        self.assertTrue(await self.seam.update_processing_status(self.doc_id, DocumentProcessingState.EXTRACTING))
        self.assertTrue(await self.seam.update_processing_status(self.doc_id, DocumentProcessingState.CHUNKING))
        self.assertTrue(await self.seam.update_processing_status(self.doc_id, DocumentProcessingState.EMBEDDING))
        self.assertTrue(await self.seam.update_processing_status(self.doc_id, DocumentProcessingState.READY_FOR_AI))
        self.assertEqual(self.seam.document_statuses[self.doc_id], DocumentProcessingState.READY_FOR_AI)

        # Illegal backward transition directly to PENDING should fail
        self.assertFalse(await self.seam.update_processing_status(self.doc_id, DocumentProcessingState.PENDING))

    async def test_version_chunk_registration_and_superseded_deactivation(self) -> None:
        # Version 1 chunks
        v1_chunks = [uuid4(), uuid4(), uuid4()]
        registered_v1 = await self.seam.register_version_chunks(self.doc_id, version_number=1, chunk_ids=v1_chunks)
        self.assertEqual(registered_v1, 3)
        for c in v1_chunks:
            self.assertIn(c, self.seam.active_chunks)

        # Version 2 chunks uploaded
        v2_chunks = [uuid4(), uuid4()]
        await self.seam.register_version_chunks(self.doc_id, version_number=2, chunk_ids=v2_chunks)
        for c in v2_chunks:
            self.assertIn(c, self.seam.active_chunks)

        # Supersede v1: deactivates v1 chunks
        deactivated = await self.seam.deactivate_superseded_version_chunks(self.doc_id, active_version=2)
        self.assertEqual(deactivated, 3)

        # Verify v1 chunks are removed from active pool while v2 remain
        for c in v1_chunks:
            self.assertNotIn(c, self.seam.active_chunks)
        for c in v2_chunks:
            self.assertIn(c, self.seam.active_chunks)


if __name__ == "__main__":
    unittest.main()
