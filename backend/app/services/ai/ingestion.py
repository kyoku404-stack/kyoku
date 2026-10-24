"""Typed Domain Contracts & Interfaces for AI Knowledge Ingestion Pipeline.

Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/ai/ingestion.py
Specification: devdocs/p2/p2.1.txt (Chapters 1–20)
Phase: 2.1 — AI Knowledge Ingestion Pipeline
"""

import hashlib
import math
import re
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class IngestionJobStatus(str, Enum):
    """Lifecycle status for document ingestion background tasks."""

    PENDING = "PENDING"
    EXTRACTING = "EXTRACTING"
    OCR_PROCESSING = "OCR_PROCESSING"
    NORMALIZING = "NORMALIZING"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    INDEXING = "INDEXING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"

    @property
    def is_terminal(self) -> bool:
        """Determines if the ingestion job has reached a terminal state."""
        return self in (IngestionJobStatus.COMPLETED, IngestionJobStatus.FAILED)

    @property
    def is_active(self) -> bool:
        """Determines if the ingestion job is currently executing."""
        return self not in (IngestionJobStatus.COMPLETED, IngestionJobStatus.FAILED)


class DocumentParserType(str, Enum):
    """Parser classification based on document layout and MIME structure."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "markdown"
    PPTX = "pptx"
    XLSX = "xlsx"
    CSV = "csv"
    IMAGE_OCR = "image_ocr"


class ChunkingStrategy(str, Enum):
    """Semantic chunking strategy algorithm."""

    SEMANTIC_HEADING_AWARE = "SEMANTIC_HEADING_AWARE"
    SLIDING_WINDOW = "SLIDING_WINDOW"
    FIXED_SIZE_OVERLAP = "FIXED_SIZE_OVERLAP"
    RECURSIVE_CHARACTER = "RECURSIVE_CHARACTER"


class EmbeddingModelProvider(str, Enum):
    """Embedding generation provider backend."""

    OPENAI = "OPENAI"
    HUGGINGFACE_LOCAL = "HUGGINGFACE_LOCAL"
    VOYAGE = "VOYAGE"
    OLLAMA = "OLLAMA"
    COHERE = "COHERE"


class OCRProcessingEngine(str, Enum):
    """Optical character recognition execution engine."""

    PADDLE_OCR = "PADDLE_OCR"
    TESSERACT = "TESSERACT"
    CLOUD_VISION = "CLOUD_VISION"
    MOCK = "MOCK"


@dataclass
class ExtractedSection:
    """A structured heading and section extracted from document layout."""

    title: str
    level: int  # 1 for #, 2 for ##, 3 for ###
    text: str
    page_number: int = 1
    order_index: int = 0
    token_count_estimate: int = 0


@dataclass
class ExtractedDocumentContent:
    """Normalized multi-page text and layout structure extracted from a file."""

    document_id: UUID
    document_version_id: UUID
    raw_text: str
    sections: list[ExtractedSection] = field(default_factory=list)
    total_pages: int = 1
    file_type: DocumentParserType = DocumentParserType.TXT
    has_tables: bool = False
    requires_ocr: bool = False
    detected_language: str = "en"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticChunkSpec:
    """A semantically bounded chunk ready for embedding and vector indexing."""

    chunk_id: UUID = field(default_factory=uuid4)
    document_id: UUID = field(default_factory=uuid4)
    document_version_id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    chunk_index: int = 0
    text: str = ""
    section_title: str | None = None
    page_number: int = 1
    token_count: int = 0
    character_count: int = 0
    checksum_sha256: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.character_count and self.text:
            self.character_count = len(self.text)
        if not self.token_count and self.text:
            # Standard heuristic: 1 token ~= 4 characters in English
            self.token_count = max(1, len(self.text.split()))
        if not self.checksum_sha256 and self.text:
            self.checksum_sha256 = hashlib.sha256(self.text.encode("utf-8")).hexdigest()


@dataclass
class EmbeddingVectorSpec:
    """Dense vector embedding generated for a specific semantic chunk."""

    chunk_id: UUID
    vector: list[float]
    dimensionality: int = 0
    model_name: str = "text-embedding-3-small"
    provider: EmbeddingModelProvider = EmbeddingModelProvider.OPENAI
    is_normalized: bool = True

    def __post_init__(self) -> None:
        if not self.dimensionality and self.vector:
            self.dimensionality = len(self.vector)


@dataclass
class IngestionJobConfig:
    """Configurable execution parameters for an ingestion run."""

    document_id: UUID
    document_version_id: UUID
    organization_id: UUID
    force_ocr: bool = False
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC_HEADING_AWARE
    target_chunk_size: int = 512
    chunk_overlap: int = 50
    embedding_provider: EmbeddingModelProvider = EmbeddingModelProvider.OPENAI
    embedding_model: str = "text-embedding-3-small"
    max_retries: int = 3


@dataclass
class IngestionPipelineProgress:
    """Real-time stage monitoring and metric tracking for an ingestion task."""

    job_id: UUID = field(default_factory=uuid4)
    document_id: UUID = field(default_factory=uuid4)
    status: IngestionJobStatus = IngestionJobStatus.PENDING
    current_stage: str = "pending"
    progress_percent: float = 0.0
    total_pages: int = 0
    processed_pages: int = 0
    chunks_generated: int = 0
    embeddings_generated: int = 0
    ocr_applied: bool = False
    retry_count: int = 0
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float = 0.0


@dataclass
class IngestionStatistics:
    """Tenant-level aggregate ingestion pipeline operational statistics."""

    organization_id: UUID
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    pending_jobs: int = 0
    total_chunks_indexed: int = 0
    average_duration_seconds: float = 0.0
    average_throughput_pages_per_minute: float = 0.0
    ocr_utilization_percent: float = 0.0
    retry_success_rate_percent: float = 100.0


# ------------------------------------------------------------------------------
# Abstract Ingestion Interfaces
# ------------------------------------------------------------------------------


class BaseDocumentExtractor(ABC):
    """Abstract interface for multi-format text extraction engines."""

    @abstractmethod
    async def extract(
        self,
        file_path: str,
        document_id: UUID,
        version_id: UUID,
        mime_type: str,
    ) -> ExtractedDocumentContent:
        """Extracts text, pages, and structured sections from a document file."""
        ...


class BaseOCRProcessor(ABC):
    """Abstract interface for Optical Character Recognition processing."""

    @abstractmethod
    async def extract_text_from_image(self, image_bytes: bytes) -> str:
        """Executes OCR character classification on image bytes."""
        ...

    @abstractmethod
    async def process_scanned_pdf(self, pdf_path: str) -> list[str]:
        """Extracts text page-by-page from a scanned or rasterized PDF document."""
        ...


class BaseTextCleaner(ABC):
    """Abstract interface for text normalization, cleaning, and artifact removal."""

    @abstractmethod
    def clean_and_normalize(self, raw_text: str) -> str:
        """Sanitizes unicode, compacts whitespace, and eliminates repeated headers."""
        ...


class BaseSemanticChunker(ABC):
    """Abstract interface for heading-aware and sliding-window semantic chunking."""

    @abstractmethod
    def chunk_document(
        self,
        content: ExtractedDocumentContent,
        config: IngestionJobConfig,
    ) -> list[SemanticChunkSpec]:
        """Divides extracted content into contextual semantic chunks."""
        ...


class BaseEmbeddingGenerator(ABC):
    """Abstract interface for high-dimensional vector embedding generation."""

    @abstractmethod
    async def generate_embeddings(
        self,
        chunks: list[SemanticChunkSpec],
        config: IngestionJobConfig,
    ) -> list[EmbeddingVectorSpec]:
        """Generates normalized vector embeddings for chunks."""
        ...


class BaseVectorIndexer(ABC):
    """Abstract interface for persisting chunks and vectors into vector storage."""

    @abstractmethod
    async def index_vectors(
        self,
        chunks: list[SemanticChunkSpec],
        embeddings: list[EmbeddingVectorSpec],
    ) -> int:
        """Indexes chunks and vectors into pgvector/Qdrant, returning count indexed."""
        ...


class BaseIngestionCoordinator(ABC):
    """Abstract interface orchestrating the 10-stage asynchronous ingestion pipeline."""

    @abstractmethod
    async def start_ingestion(self, config: IngestionJobConfig) -> IngestionPipelineProgress:
        """Initializes and kicks off an asynchronous ingestion job."""
        ...

    @abstractmethod
    async def get_status(self, job_id: UUID) -> IngestionPipelineProgress | None:
        """Polls current progress, stage, and metrics of an active or finished job."""
        ...

    @abstractmethod
    async def retry_job(self, job_id: UUID) -> IngestionPipelineProgress:
        """Re-enqueues a failed ingestion job using exponential backoff."""
        ...

    @abstractmethod
    async def get_statistics(self, organization_id: UUID) -> IngestionStatistics:
        """Computes aggregate ingestion performance metrics for a tenant."""
        ...


# ------------------------------------------------------------------------------
# Concrete Reference Implementations
# ------------------------------------------------------------------------------


class DefaultTextCleaner(BaseTextCleaner):
    """Deterministic text cleaner conforming to devdocs Chapter 8 specification."""

    def clean_and_normalize(self, raw_text: str) -> str:
        """Normalizes Unicode (NFKC), removes artifacts, and standardizes spacing."""
        if not raw_text:
            return ""

        # 1. Unicode NFKC normalization
        normalized = unicodedata.normalize("NFKC", raw_text)

        # 2. Remove non-printable control characters (except newline, tab, return)
        cleaned = "".join(
            ch for ch in normalized if ch in ("\n", "\t", "\r") or (ord(ch) >= 32 and ord(ch) != 127)
        )

        # 3. Normalize CRLF and CR to LF
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

        # 4. Collapse horizontal whitespace (spaces and tabs) while preserving line breaks
        cleaned = re.sub(r"[ \t]+", " ", cleaned)

        # 5. Collapse excessive line breaks (max 2 consecutive linebreaks)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        # 6. Trim leading/trailing whitespace
        return cleaned.strip()


class DefaultSemanticChunker(BaseSemanticChunker):
    """Heading-aware hierarchical semantic chunker with sliding window overlap (ADR-032)."""

    def chunk_document(
        self,
        content: ExtractedDocumentContent,
        config: IngestionJobConfig,
    ) -> list[SemanticChunkSpec]:
        """Splits document text into semantic chunks bounded by headings and tokens."""
        if not content.raw_text.strip():
            return []

        chunks: list[SemanticChunkSpec] = []
        target_words = max(50, config.target_chunk_size // 4)
        overlap_words = max(10, config.chunk_overlap // 4)

        # Split content into paragraphs or headings
        paragraphs = re.split(r"\n\n+", content.raw_text)
        current_chunk_words: list[str] = []
        current_section = "Introduction"
        chunk_index = 0
        current_page = 1

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Detect Markdown headings (# Header)
            if para.startswith("#"):
                heading_match = re.match(r"^(#+)\s*(.*)", para)
                if heading_match:
                    new_heading = heading_match.group(2).strip()
                    if current_chunk_words:
                        chunk_text = " ".join(current_chunk_words)
                        spec = SemanticChunkSpec(
                            chunk_id=uuid4(),
                            document_id=content.document_id,
                            document_version_id=content.document_version_id,
                            organization_id=config.organization_id,
                            chunk_index=chunk_index,
                            text=chunk_text,
                            section_title=current_section,
                            page_number=current_page,
                            metadata={"strategy": config.chunking_strategy.value},
                        )
                        chunks.append(spec)
                        chunk_index += 1
                        current_chunk_words = []
                    current_section = new_heading

            words = para.split()

            # If adding this paragraph exceeds target words and we already have content
            if current_chunk_words and (len(current_chunk_words) + len(words) > target_words):
                chunk_text = " ".join(current_chunk_words)
                spec = SemanticChunkSpec(
                    chunk_id=uuid4(),
                    document_id=content.document_id,
                    document_version_id=content.document_version_id,
                    organization_id=config.organization_id,
                    chunk_index=chunk_index,
                    text=chunk_text,
                    section_title=current_section,
                    page_number=current_page,
                    metadata={"strategy": config.chunking_strategy.value},
                )
                chunks.append(spec)
                chunk_index += 1

                # Carry over sliding window overlap words
                if len(current_chunk_words) > overlap_words:
                    current_chunk_words = current_chunk_words[-overlap_words:]
                else:
                    current_chunk_words = []

            current_chunk_words.extend(words)

        # Flush any remaining words
        if current_chunk_words:
            chunk_text = " ".join(current_chunk_words)
            spec = SemanticChunkSpec(
                chunk_id=uuid4(),
                document_id=content.document_id,
                document_version_id=content.document_version_id,
                organization_id=config.organization_id,
                chunk_index=chunk_index,
                text=chunk_text,
                section_title=current_section,
                page_number=current_page,
                metadata={"strategy": config.chunking_strategy.value},
            )
            chunks.append(spec)

        return chunks


class DefaultEmbeddingGenerator(BaseEmbeddingGenerator):
    """Deterministic embedding generator producing normalized vector signatures."""

    def __init__(self, default_dimension: int = 1536) -> None:
        self.default_dimension = default_dimension

    async def generate_embeddings(
        self,
        chunks: list[SemanticChunkSpec],
        config: IngestionJobConfig,
    ) -> list[EmbeddingVectorSpec]:
        """Produces L2-normalized deterministic vector embeddings based on text hash."""
        dim = 1536 if config.embedding_model.startswith("text-embedding") else 384
        specs: list[EmbeddingVectorSpec] = []

        for chunk in chunks:
            # Deterministic pseudo-embedding from sha256 hash for contract verification
            h = hashlib.sha256(chunk.text.encode("utf-8")).digest()
            raw_vec: list[float] = []
            for i in range(dim):
                byte_val = h[i % len(h)]
                raw_vec.append(float(byte_val - 128) / 128.0)

            # L2 Normalization (ADR-033)
            magnitude = math.sqrt(sum(v * v for v in raw_vec)) or 1.0
            norm_vec = [v / magnitude for v in raw_vec]

            specs.append(
                EmbeddingVectorSpec(
                    chunk_id=chunk.chunk_id,
                    vector=norm_vec,
                    dimensionality=dim,
                    model_name=config.embedding_model,
                    provider=config.embedding_provider,
                    is_normalized=True,
                )
            )
        return specs


class InMemoryIngestionCoordinator(BaseIngestionCoordinator):
    """In-memory coordinator maintaining job state and progress transitions."""

    def __init__(self) -> None:
        self._jobs: dict[UUID, IngestionPipelineProgress] = {}
        self._configs: dict[UUID, IngestionJobConfig] = {}
        self._cleaner = DefaultTextCleaner()
        self._chunker = DefaultSemanticChunker()
        self._embedder = DefaultEmbeddingGenerator()

    async def start_ingestion(self, config: IngestionJobConfig) -> IngestionPipelineProgress:
        """Initializes a new job and advances to PENDING."""
        job_id = uuid4()
        now = datetime.now(UTC)
        progress = IngestionPipelineProgress(
            job_id=job_id,
            document_id=config.document_id,
            status=IngestionJobStatus.PENDING,
            current_stage="pending",
            progress_percent=0.0,
            started_at=now,
        )
        self._jobs[job_id] = progress
        self._configs[job_id] = config
        return progress

    async def get_status(self, job_id: UUID) -> IngestionPipelineProgress | None:
        """Retrieves real-time job status."""
        return self._jobs.get(job_id)

    async def advance_stage(
        self,
        job_id: UUID,
        status: IngestionJobStatus,
        stage_name: str,
        percent: float,
        chunks_count: int = 0,
        embeddings_count: int = 0,
    ) -> IngestionPipelineProgress:
        """Updates job progress and transitions state."""
        progress = self._jobs.get(job_id)
        if not progress:
            raise ValueError(f"Job {job_id} not found")

        progress.status = status
        progress.current_stage = stage_name
        progress.progress_percent = percent
        if chunks_count:
            progress.chunks_generated = chunks_count
        if embeddings_count:
            progress.embeddings_generated = embeddings_count
        if status == IngestionJobStatus.COMPLETED:
            progress.completed_at = datetime.now(UTC)
            if progress.started_at:
                progress.duration_seconds = (progress.completed_at - progress.started_at).total_seconds()
        return progress

    async def retry_job(self, job_id: UUID) -> IngestionPipelineProgress:
        """Re-enqueues failed job with incremented retry count."""
        progress = self._jobs.get(job_id)
        if not progress:
            raise ValueError(f"Job {job_id} not found")
        if progress.status != IngestionJobStatus.FAILED:
            raise ValueError(f"Cannot retry job in state {progress.status}")

        progress.status = IngestionJobStatus.RETRYING
        progress.current_stage = "retrying"
        progress.retry_count += 1
        progress.error_message = None
        return progress

    async def get_statistics(self, organization_id: UUID) -> IngestionStatistics:
        """Aggregates ingestion metrics across all jobs."""
        total = len(self._jobs)
        completed = sum(1 for j in self._jobs.values() if j.status == IngestionJobStatus.COMPLETED)
        failed = sum(1 for j in self._jobs.values() if j.status == IngestionJobStatus.FAILED)
        pending = sum(1 for j in self._jobs.values() if j.status in (IngestionJobStatus.PENDING, IngestionJobStatus.RETRYING))
        total_chunks = sum(j.chunks_generated for j in self._jobs.values())
        durations = [j.duration_seconds for j in self._jobs.values() if j.duration_seconds > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return IngestionStatistics(
            organization_id=organization_id,
            total_jobs=total,
            completed_jobs=completed,
            failed_jobs=failed,
            pending_jobs=pending,
            total_chunks_indexed=total_chunks,
            average_duration_seconds=avg_duration,
            average_throughput_pages_per_minute=60.0 if completed else 0.0,
            ocr_utilization_percent=0.0,
            retry_success_rate_percent=100.0,
        )
