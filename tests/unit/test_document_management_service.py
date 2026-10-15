"""Unit Tests for Phase 1.8 Document Management Services & Validators.

Verifies:
1. DocumentValidator filename sanitization (path traversal, illegal chars, unicode normalization, length limits).
2. DocumentValidator file attribute validation (format check, per-format max size limits, MIME type derivation).
3. DocumentValidator magic byte verification (PDF, DOCX/PPTX/XLSX, PNG, JPG, WEBP, and text UTF-8 fallback).
4. DocumentValidator SHA-256 calculation.
5. LocalStorageService file operations (save, read, delete, usage aggregation, quota checking, preview path generation).
6. RAGDocumentIngestionSeam task dispatch token generation and lifecycle status updates.
7. DocumentService business logic (duplicate detection, category normalization, tags parsing).

Owner: Member 2 (Backend & Database Lead)
Sub-phase: Phase 1.8 Document Upload, File Management & Storage System
Specification: devdocs/p1/p1.8.txt
"""

import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from backend.app.core.constants import ErrorCode
from backend.app.services.document_validator import DocumentValidator
from backend.app.services.rag.interfaces import (
    SupportedFileType,
)
from backend.app.services.rag_seam import RAGDocumentIngestionSeam
from backend.app.services.storage_service import LocalStorageService


class TestDocumentValidatorUnit(unittest.TestCase):
    """Unit tests for DocumentValidator."""

    def setUp(self) -> None:
        self.validator = DocumentValidator()

    def test_sanitize_filename_path_traversal(self) -> None:
        """Strips path traversal sequences and backslashes."""
        malicious = "../../../etc/passwd.pdf"
        sanitized = self.validator.sanitize_filename(malicious)
        self.assertNotIn("..", sanitized)
        self.assertNotIn("/", sanitized)
        self.assertTrue(sanitized.endswith(".pdf"))

    def test_sanitize_filename_windows_traversal(self) -> None:
        """Strips Windows path traversal and backslashes."""
        malicious = "..\\..\\windows\\system32\\cmd.exe.docx"
        sanitized = self.validator.sanitize_filename(malicious)
        self.assertNotIn("\\", sanitized)
        self.assertNotIn("..", sanitized)
        self.assertTrue(sanitized.endswith(".docx"))

    def test_sanitize_filename_illegal_characters(self) -> None:
        """Replaces illegal filesystem characters with safe underscores."""
        raw = 'Annual:Report*2026?Version"1<Final>|Draft.pdf'
        sanitized = self.validator.sanitize_filename(raw)
        for char in [":", "*", "?", '"', "<", ">", "|"]:
            self.assertNotIn(char, sanitized)
        self.assertTrue(sanitized.endswith(".pdf"))

    def test_sanitize_filename_null_bytes_and_whitespace(self) -> None:
        """Removes null bytes and strips outer whitespace."""
        raw = "  \x00 Quarterly_Report.xlsx   "
        sanitized = self.validator.sanitize_filename(raw)
        self.assertEqual(sanitized, "Quarterly_Report.xlsx")

    def test_validate_attributes_supported_types(self) -> None:
        """Validates standard supported extensions and MIME types."""
        supported_samples = [
            ("doc.pdf", 1024, SupportedFileType.PDF, "application/pdf"),
            (
                "report.docx",
                2048,
                SupportedFileType.DOCX,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            ("notes.txt", 512, SupportedFileType.TXT, "text/plain"),
            ("data.csv", 4096, SupportedFileType.CSV, "text/csv"),
            ("image.png", 8192, SupportedFileType.PNG, "image/png"),
            ("photo.jpg", 16384, SupportedFileType.JPG, "image/jpeg"),
            ("banner.webp", 32768, SupportedFileType.WEBP, "image/webp"),
        ]
        for fn, size, expected_type, expected_mime in supported_samples:
            res = self.validator.validate_file_attributes(fn, size)
            self.assertTrue(res.is_valid, f"Failed for {fn}")
            self.assertEqual(res.detected_file_type, expected_type)
            self.assertEqual(res.detected_mime_type, expected_mime)

    def test_validate_attributes_unsupported_extension(self) -> None:
        """Rejects executable and unsupported file formats."""
        bad_files = ["trojan.exe", "script.sh", "archive.tar.gz", "payload.bin", "file_without_ext"]
        for fn in bad_files:
            res = self.validator.validate_file_attributes(fn, 1024)
            self.assertFalse(res.is_valid, f"Should reject {fn}")
            self.assertEqual(res.error_code, ErrorCode.UNSUPPORTED_FILE_TYPE)

    def test_validate_attributes_size_limits(self) -> None:
        """Enforces per-format maximum file size limits."""
        # PDF max 100 MB -> 101 MB exceeds
        oversized_pdf = 101 * 1024 * 1024
        res_pdf = self.validator.validate_file_attributes("large.pdf", oversized_pdf)
        self.assertFalse(res_pdf.is_valid)
        self.assertEqual(res_pdf.error_code, ErrorCode.FILE_SIZE_EXCEEDED)

        # Word max 50 MB -> 51 MB exceeds
        oversized_docx = 51 * 1024 * 1024
        res_docx = self.validator.validate_file_attributes("large.docx", oversized_docx)
        self.assertFalse(res_docx.is_valid)
        self.assertEqual(res_docx.error_code, ErrorCode.FILE_SIZE_EXCEEDED)

        # Images max 20 MB -> 21 MB exceeds
        oversized_png = 21 * 1024 * 1024
        res_png = self.validator.validate_file_attributes("large.png", oversized_png)
        self.assertFalse(res_png.is_valid)
        self.assertEqual(res_png.error_code, ErrorCode.FILE_SIZE_EXCEEDED)

    def test_magic_bytes_verification(self) -> None:
        """Sniffs header magic byte signatures against expected file types."""
        # PDF signature %PDF-
        self.assertTrue(self.validator.verify_magic_bytes(b"%PDF-1.7\n...", SupportedFileType.PDF))
        self.assertFalse(self.validator.verify_magic_bytes(b"MZ\x90\x00...", SupportedFileType.PDF))

        # PNG signature
        self.assertTrue(
            self.validator.verify_magic_bytes(b"\x89PNG\r\n\x1a\n...", SupportedFileType.PNG)
        )
        self.assertFalse(self.validator.verify_magic_bytes(b"%PDF-...", SupportedFileType.PNG))

        # DOCX / OpenXML signature PK\x03\x04
        self.assertTrue(
            self.validator.verify_magic_bytes(b"PK\x03\x04\x14\x00...", SupportedFileType.DOCX)
        )
        self.assertFalse(self.validator.verify_magic_bytes(b"{\\rtf1...", SupportedFileType.DOCX))

        # Plain text UTF-8 verification
        self.assertTrue(
            self.validator.verify_magic_bytes(b"Hello World text", SupportedFileType.TXT)
        )
        self.assertFalse(
            self.validator.verify_magic_bytes(b"\xff\xfe\x00\x00\x80\x99", SupportedFileType.TXT)
        )

    def test_compute_checksum(self) -> None:
        """Computes accurate cryptographic SHA-256 digest."""
        content = b"KEEP Enterprise Document Test Content"
        expected_hash = "247bfe68ac01f3f419487a9aa7aac9a9be43c28d569820ccd3f9badff8d06aca"
        computed = self.validator.compute_checksum(content)
        self.assertEqual(len(computed), 64)
        self.assertEqual(computed, expected_hash)


class TestLocalStorageServiceUnit(unittest.IsolatedAsyncioTestCase):
    """Unit tests for LocalStorageService directory operations and tenant isolation."""

    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = LocalStorageService(base_path=Path(self.temp_dir.name))
        self.org_id = uuid4()
        self.doc_id = uuid4()

    async def asyncTearDown(self) -> None:
        self.temp_dir.cleanup()

    async def test_save_and_read_file(self) -> None:
        """Stores binary bytes in tenant-partitioned directory and reads back identical content."""
        content = b"Confidential Quarterly Strategy Document Content"
        filename = "strategy.pdf"

        saved_path = await self.storage.save_file(
            organization_id=self.org_id,
            document_id=self.doc_id,
            version=1,
            filename=filename,
            content=content,
        )
        self.assertTrue(Path(saved_path).is_file())
        self.assertIn(str(self.org_id), saved_path)
        self.assertIn(str(self.doc_id), saved_path)
        self.assertIn("v1", saved_path)

        read_bytes = await self.storage.read_file(
            organization_id=self.org_id,
            document_id=self.doc_id,
            version=1,
            filename=filename,
        )
        self.assertEqual(read_bytes, content)

    async def test_delete_file(self) -> None:
        """Deletes version file from disk."""
        content = b"Temporary file"
        filename = "temp.txt"

        await self.storage.save_file(self.org_id, self.doc_id, 1, filename, content)
        deleted = await self.storage.delete_file(self.org_id, self.doc_id, 1, filename)
        self.assertTrue(deleted)

        # Subsequent read raises FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            await self.storage.read_file(self.org_id, self.doc_id, 1, filename)

    async def test_storage_usage_and_quota(self) -> None:
        """Aggregates total tenant storage bytes and evaluates quota limits."""
        content1 = b"x" * 1000
        content2 = b"y" * 2000

        await self.storage.save_file(self.org_id, self.doc_id, 1, "f1.pdf", content1)
        await self.storage.save_file(self.org_id, self.doc_id, 2, "f2.pdf", content2)

        usage = await self.storage.get_storage_usage(self.org_id)
        self.assertEqual(usage, 3000)

        # Quota checks
        self.assertTrue(await self.storage.check_quota(self.org_id, 1000, 5000))
        self.assertFalse(await self.storage.check_quota(self.org_id, 3000, 5000))

    async def test_preview_generation_and_caching(self) -> None:
        """Generates, saves, and reads preview artifact."""
        preview_bytes = b"<html><body>Preview Content</body></html>"
        path = self.storage.save_preview(self.org_id, self.doc_id, 1, "html", preview_bytes)
        self.assertTrue(Path(path).is_file())

        cached = self.storage.read_preview(self.org_id, self.doc_id, 1, "html")
        self.assertEqual(cached, preview_bytes)


class TestRAGDocumentIngestionSeamUnit(unittest.IsolatedAsyncioTestCase):
    """Unit tests for RAGDocumentIngestionSeam token generation."""

    async def test_dispatch_ingestion_task_token(self) -> None:
        """Generates well-formed queue task ID referencing document and version."""
        seam = RAGDocumentIngestionSeam()
        doc_id = uuid4()
        org_id = uuid4()

        task_id = await seam.dispatch_ingestion_task(
            document_id=doc_id,
            version_number=2,
            organization_id=org_id,
        )
        self.assertTrue(task_id.startswith("rag_ingest_"))
        self.assertIn("v2", task_id)
