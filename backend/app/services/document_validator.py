"""KEEP Enterprise Platform — Document Validation Service (Phase 1.8).

Implements server-side file attribute inspection, magic byte sniffing,
path traversal sanitization, and cryptographic checksum calculation.
Specification: devdocs/p1/p1.8.txt Chapter 6 & docs/Architecture/document-management-architecture.md Section 3
"""

import hashlib
import posixpath
import re
import unicodedata

from backend.app.core.constants import ErrorCode
from backend.app.services.rag.interfaces import (
    FILE_TYPE_MIME_MAP,
    MAGIC_BYTE_SIGNATURES,
    MAX_FILE_SIZES,
    BaseDocumentValidator,
    DocumentValidationResult,
    SupportedFileType,
)

# Extension mapping to SupportedFileType
EXT_MAP: dict[str, SupportedFileType] = {
    "pdf": SupportedFileType.PDF,
    "docx": SupportedFileType.DOCX,
    "txt": SupportedFileType.TXT,
    "md": SupportedFileType.MD,
    "rtf": SupportedFileType.RTF,
    "pptx": SupportedFileType.PPTX,
    "xlsx": SupportedFileType.XLSX,
    "csv": SupportedFileType.CSV,
    "png": SupportedFileType.PNG,
    "jpg": SupportedFileType.JPG,
    "jpeg": SupportedFileType.JPEG,
    "webp": SupportedFileType.WEBP,
}


class DocumentValidator(BaseDocumentValidator):
    """Concrete implementation of BaseDocumentValidator for enterprise ingestion."""

    def sanitize_filename(self, filename: str) -> str:
        """Sanitizes filename against path traversal attacks and illegal characters."""
        if not filename:
            return "document"

        # Normalize unicode NFKC
        cleaned = unicodedata.normalize("NFKC", filename)

        # Remove null bytes and path components
        cleaned = cleaned.replace("\0", "")
        cleaned = posixpath.basename(cleaned)


        # Replace directory separators and backslashes
        cleaned = re.sub(r"[\\/]+", "_", cleaned)

        # Remove path traversal sequences (e.g. ..)
        cleaned = re.sub(r"\.\.+", ".", cleaned)

        # Strip illegal characters for Windows/Linux/POSIX filesystems
        cleaned = re.sub(r'[:*?"<>|;&$]', "_", cleaned)

        # Strip non-printable ASCII / control characters
        cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", cleaned)

        # Strip leading/trailing spaces and dots
        cleaned = cleaned.strip(" .")

        if not cleaned:
            cleaned = "document"

        # Enforce maximum length of 255 chars preserving extension
        if len(cleaned) > 255:
            if "." in cleaned:
                name_part, ext_part = cleaned.rsplit(".", 1)
                max_name_len = 254 - len(ext_part)
                cleaned = f"{name_part[:max_name_len]}.{ext_part}"
            else:
                cleaned = cleaned[:255]

        return cleaned

    def validate_file_attributes(
        self,
        filename: str,
        file_size: int,
        mime_type: str | None = None,
    ) -> DocumentValidationResult:
        """Validates filename extension, size limit, and assigns sanitized attributes."""
        sanitized = self.sanitize_filename(filename)

        # Extract normalized extension
        if "." not in sanitized:
            return DocumentValidationResult(
                is_valid=False,
                sanitized_filename=sanitized,
                file_size_bytes=file_size,
                error_code=ErrorCode.UNSUPPORTED_FILE_TYPE,
                error_message="Uploaded file missing file extension.",
            )

        ext = sanitized.rsplit(".", 1)[-1].lower()
        file_type = EXT_MAP.get(ext)
        if not file_type:
            allowed = sorted(EXT_MAP.keys())
            return DocumentValidationResult(
                is_valid=False,
                sanitized_filename=sanitized,
                file_size_bytes=file_size,
                error_code=ErrorCode.UNSUPPORTED_FILE_TYPE,
                error_message=f"Unsupported file type '.{ext}'. Allowed types: {allowed}",
            )

        # Verify per-format maximum size limit
        max_allowed_size = MAX_FILE_SIZES.get(file_type, 20 * 1024 * 1024)
        if file_size > max_allowed_size:
            max_mb = max_allowed_size // (1024 * 1024)
            return DocumentValidationResult(
                is_valid=False,
                sanitized_filename=sanitized,
                detected_file_type=file_type,
                file_size_bytes=file_size,
                error_code=ErrorCode.FILE_SIZE_EXCEEDED,
                error_message=(
                    f"File size {file_size} bytes exceeds maximum allowed "
                    f"limit of {max_mb} MB for {file_type.value.upper()} files."
                ),
            )

        canonical_mime = FILE_TYPE_MIME_MAP.get(file_type, "application/octet-stream")

        return DocumentValidationResult(
            is_valid=True,
            sanitized_filename=sanitized,
            detected_file_type=file_type,
            detected_mime_type=canonical_mime,
            file_size_bytes=file_size,
        )

    def verify_magic_bytes(
        self,
        header_bytes: bytes,
        expected_type: SupportedFileType,
    ) -> bool:
        """Sniffs header magic bytes to prevent MIME-type spoofing."""
        signatures = MAGIC_BYTE_SIGNATURES.get(expected_type)
        if signatures:
            for sig in signatures:
                if header_bytes.startswith(sig):
                    return True
            return False

        # For text-based formats (TXT, MD, CSV), verify valid UTF-8/ASCII
        if expected_type in {
            SupportedFileType.TXT,
            SupportedFileType.MD,
            SupportedFileType.CSV,
        }:
            try:
                header_bytes[:512].decode("utf-8")
                return True
            except UnicodeDecodeError:
                return False

        return True

    def compute_checksum(self, content: bytes) -> str:
        """Calculates SHA-256 cryptographic digest of file contents."""
        return hashlib.sha256(content).hexdigest()
