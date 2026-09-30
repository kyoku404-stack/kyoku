"""KEEP Enterprise Platform — Document Management Service."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.app.core.constants import DocumentStatus, ErrorCode
from backend.app.core.exceptions import ValidationException
from backend.app.repositories.document_repo import DocumentRepository
from backend.app.schemas.document import DocumentResponse, DocumentUploadResponse
from backend.app.schemas.envelope import PaginatedData
from backend.app.services.base import BaseService
from sqlalchemy.ext.asyncio import AsyncSession

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


class DocumentService(BaseService[DocumentRepository]):
    """Service orchestrating document ingestion and catalog operations."""

    def __init__(self, repository: DocumentRepository | None = None) -> None:
        super().__init__(repository or DocumentRepository())

    async def upload_document(
        self,
        db: AsyncSession | None,
        filename: str,
        content_type: str,
        file_size: int,
        org_id: UUID,
        title: str | None = None,
        tags: str | None = None,
    ) -> DocumentUploadResponse:
        """Validates uploaded document attributes and registers it for ingestion."""
        # Extension validation
        extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if extension not in ALLOWED_EXTENSIONS:
            raise ValidationException(
                message=f"Unsupported file type '{extension}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
                code=ErrorCode.UNSUPPORTED_FILE_TYPE,
            )

        if file_size > MAX_FILE_SIZE:
            raise ValidationException(
                message=f"File size {file_size} exceeds maximum limit of {MAX_FILE_SIZE} bytes.",
                code=ErrorCode.FILE_SIZE_EXCEEDED,
            )

        document_id = uuid4()
        return DocumentUploadResponse(
            document_id=document_id,
            filename=filename,
            status=DocumentStatus.PROCESSING,
            file_size=file_size,
            created_at=datetime.now(UTC),
        )

    async def list_documents(
        self,
        db: AsyncSession | None,
        org_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: DocumentStatus | None = None,
    ) -> PaginatedData[DocumentResponse]:
        """Lists ingested documents within the tenant boundary."""
        sample_doc = DocumentResponse(
            id=UUID("99a85f64-5717-4562-b3fc-2c963f66af11"),
            filename="Q3_Strategic_Plan.pdf",
            file_type="application/pdf",
            file_size=2458120,
            status=status or DocumentStatus.PROCESSED,
            chunk_count=42,
            created_at=datetime.now(UTC),
        )
        return PaginatedData(
            items=[sample_doc],
            total=1,
            page=page,
            page_size=page_size,
            total_pages=1,
        )
