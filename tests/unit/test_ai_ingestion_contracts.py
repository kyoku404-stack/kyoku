"""Unit Tests for Phase 2.1 AI Knowledge Ingestion Pipeline Contracts & Interfaces.

Owner: Member 1 (Project Lead & AI Architect)
Domain: /tests/unit/test_ai_ingestion_contracts.py
Specification: devdocs/p2/p2.1.txt & ADR-032 / ADR-033 / ADR-034
"""

import math
import unittest
from uuid import uuid4

import pytest

from backend.app.services.ai.ingestion import (
    ChunkingStrategy,
    DefaultEmbeddingGenerator,
    DefaultSemanticChunker,
    DefaultTextCleaner,
    DocumentParserType,
    EmbeddingModelProvider,
    EmbeddingVectorSpec,
    ExtractedDocumentContent,
    IngestionJobConfig,
    IngestionJobStatus,
    InMemoryIngestionCoordinator,
    OCRProcessingEngine,
    SemanticChunkSpec,
)


class TestAIIngestionContracts(unittest.IsolatedAsyncioTestCase):
    """Validates Phase 2.1 typed domain contracts, cleaner logic, chunker, and coordinator."""

    def test_ingestion_job_status_properties(self) -> None:
        """Verify IngestionJobStatus enums and lifecycle property evaluations."""
        self.assertEqual(len(IngestionJobStatus), 10)

        # Terminal status evaluation
        self.assertTrue(IngestionJobStatus.COMPLETED.is_terminal)
        self.assertTrue(IngestionJobStatus.FAILED.is_terminal)
        self.assertFalse(IngestionJobStatus.PENDING.is_terminal)
        self.assertFalse(IngestionJobStatus.CHUNKING.is_terminal)
        self.assertFalse(IngestionJobStatus.RETRYING.is_terminal)

        # Active status evaluation
        self.assertTrue(IngestionJobStatus.EXTRACTING.is_active)
        self.assertTrue(IngestionJobStatus.OCR_PROCESSING.is_active)
        self.assertTrue(IngestionJobStatus.NORMALIZING.is_active)
        self.assertTrue(IngestionJobStatus.EMBEDDING.is_active)
        self.assertTrue(IngestionJobStatus.INDEXING.is_active)
        self.assertFalse(IngestionJobStatus.COMPLETED.is_active)
        self.assertFalse(IngestionJobStatus.FAILED.is_active)

    def test_document_parser_types_and_strategies(self) -> None:
        """Verify supported parser types, chunking algorithms, and embedding providers."""
        self.assertEqual(DocumentParserType.PDF.value, "pdf")
        self.assertEqual(DocumentParserType.DOCX.value, "docx")
        self.assertEqual(DocumentParserType.TXT.value, "txt")
        self.assertEqual(DocumentParserType.MARKDOWN.value, "markdown")
        self.assertEqual(DocumentParserType.PPTX.value, "pptx")
        self.assertEqual(DocumentParserType.XLSX.value, "xlsx")
        self.assertEqual(DocumentParserType.CSV.value, "csv")
        self.assertEqual(DocumentParserType.IMAGE_OCR.value, "image_ocr")

        self.assertIn("SEMANTIC_HEADING_AWARE", [s.value for s in ChunkingStrategy])
        self.assertIn("SLIDING_WINDOW", [s.value for s in ChunkingStrategy])

        self.assertIn("OPENAI", [p.value for p in EmbeddingModelProvider])
        self.assertIn("HUGGINGFACE_LOCAL", [p.value for p in EmbeddingModelProvider])

        self.assertIn("PADDLE_OCR", [o.value for o in OCRProcessingEngine])
        self.assertIn("TESSERACT", [o.value for o in OCRProcessingEngine])

    def test_semantic_chunk_spec_auto_calculation(self) -> None:
        """Verify SemanticChunkSpec automatically computes character count, token count, and sha256."""
        sample_text = "KEEP Enterprise Intelligence transforms multi-format knowledge into dense vectors."
        chunk = SemanticChunkSpec(
            document_id=uuid4(),
            organization_id=uuid4(),
            chunk_index=0,
            text=sample_text,
            section_title="Architecture",
        )

        self.assertEqual(chunk.character_count, len(sample_text))
        self.assertEqual(chunk.token_count, len(sample_text.split()))
        self.assertEqual(len(chunk.checksum_sha256), 64)
        self.assertIsInstance(chunk.checksum_sha256, str)

    def test_embedding_vector_spec_validation(self) -> None:
        """Verify EmbeddingVectorSpec determines dimensionality and retains normalization flag."""
        vector_data = [0.1, -0.2, 0.3, -0.4, 0.5]
        spec = EmbeddingVectorSpec(
            chunk_id=uuid4(),
            vector=vector_data,
            model_name="test-embedding-model",
            provider=EmbeddingModelProvider.OPENAI,
            is_normalized=True,
        )

        self.assertEqual(spec.dimensionality, 5)
        self.assertTrue(spec.is_normalized)
        self.assertEqual(spec.model_name, "test-embedding-model")

    def test_default_text_cleaner_unicode_and_whitespace(self) -> None:
        """Verify DefaultTextCleaner sanitizes control characters, unicode, and whitespace."""
        cleaner = DefaultTextCleaner()

        raw_noisy_text = (
            "  KEEP   Enterprise \t Platform \r\n\r\n\r\n\r\n"
            "Section \x00 One: \u00A0 Clean   Knowledge \n\n\n\n\n"
            "Final \t line.   "
        )
        cleaned = cleaner.clean_and_normalize(raw_noisy_text)

        self.assertNotIn("\x00", cleaned)
        self.assertNotIn("\r", cleaned)
        self.assertNotIn("   ", cleaned)
        self.assertNotIn("\n\n\n", cleaned)
        self.assertTrue(cleaned.startswith("KEEP Enterprise Platform"))
        self.assertTrue(cleaned.endswith("Final line."))

    def test_default_semantic_chunker_heading_aware_split(self) -> None:
        """Verify DefaultSemanticChunker splits text across markdown headings with section tracking."""
        chunker = DefaultSemanticChunker()
        doc_id = uuid4()
        version_id = uuid4()
        org_id = uuid4()

        markdown_content = (
            "# Executive Summary\n\n"
            "KEEP bridges unstructured organizational knowledge and automated decision-making. "
            "It links documents, users, teams, projects, departments, and policies.\n\n"
            "## Architecture Overview\n\n"
            "The platform architecture consists of a FastAPI backend, React frontend, "
            "PostgreSQL 16 relational database with pgvector, and Redis asynchronous workers.\n\n"
            "## Security and Compliance\n\n"
            "Zero-trust security models enforce multi-tenant isolation, role-based access control, "
            "and immutable audit logging across all enterprise assets."
        )

        content = ExtractedDocumentContent(
            document_id=doc_id,
            document_version_id=version_id,
            raw_text=markdown_content,
            file_type=DocumentParserType.MARKDOWN,
            total_pages=3,
        )

        config = IngestionJobConfig(
            document_id=doc_id,
            document_version_id=version_id,
            organization_id=org_id,
            chunking_strategy=ChunkingStrategy.SEMANTIC_HEADING_AWARE,
            target_chunk_size=100,  # small target to force splits
            chunk_overlap=20,
        )

        chunks = chunker.chunk_document(content, config)

        self.assertGreaterEqual(len(chunks), 2)
        section_titles = [c.section_title for c in chunks]
        self.assertTrue(any("Executive Summary" in str(t) or "Architecture Overview" in str(t) for t in section_titles))

        for idx, chunk in enumerate(chunks):
            self.assertEqual(chunk.document_id, doc_id)
            self.assertEqual(chunk.organization_id, org_id)
            self.assertEqual(chunk.chunk_index, idx)
            self.assertGreater(chunk.token_count, 0)

    def test_default_semantic_chunker_empty_content(self) -> None:
        """Verify semantic chunker safely handles empty input text."""
        chunker = DefaultSemanticChunker()
        content = ExtractedDocumentContent(
            document_id=uuid4(),
            document_version_id=uuid4(),
            raw_text="    \n\n   ",
            file_type=DocumentParserType.TXT,
        )
        config = IngestionJobConfig(
            document_id=content.document_id,
            document_version_id=content.document_version_id,
            organization_id=uuid4(),
        )
        chunks = chunker.chunk_document(content, config)
        self.assertEqual(len(chunks), 0)

    @pytest.mark.asyncio
    async def test_default_embedding_generator_l2_normalization(self) -> None:
        """Verify DefaultEmbeddingGenerator generates mathematically L2-normalized vectors."""
        generator = DefaultEmbeddingGenerator()
        doc_id = uuid4()
        org_id = uuid4()

        chunks = [
            SemanticChunkSpec(
                document_id=doc_id,
                organization_id=org_id,
                text="Artificial Intelligence knowledge graph extraction and vector similarity.",
            ),
            SemanticChunkSpec(
                document_id=doc_id,
                organization_id=org_id,
                text="Zero-trust role-based access control and tenant isolation.",
            ),
        ]

        config = IngestionJobConfig(
            document_id=doc_id,
            document_version_id=uuid4(),
            organization_id=org_id,
            embedding_model="text-embedding-3-small",
        )

        specs = await generator.generate_embeddings(chunks, config)

        self.assertEqual(len(specs), 2)
        for spec in specs:
            self.assertEqual(spec.dimensionality, 1536)
            self.assertTrue(spec.is_normalized)
            # Verify ||v||_2 ~= 1.0 (L2 unit circle)
            norm = math.sqrt(sum(x * x for x in spec.vector))
            self.assertAlmostEqual(norm, 1.0, places=4)

    @pytest.mark.asyncio
    async def test_in_memory_ingestion_coordinator_lifecycle(self) -> None:
        """Verify InMemoryIngestionCoordinator full lifecycle, state transitions, and retries."""
        coordinator = InMemoryIngestionCoordinator()
        org_id = uuid4()
        doc_id = uuid4()
        version_id = uuid4()

        config = IngestionJobConfig(
            document_id=doc_id,
            document_version_id=version_id,
            organization_id=org_id,
            target_chunk_size=512,
        )

        # 1. Start ingestion
        progress = await coordinator.start_ingestion(config)
        self.assertEqual(progress.status, IngestionJobStatus.PENDING)
        self.assertEqual(progress.progress_percent, 0.0)
        self.assertEqual(progress.document_id, doc_id)

        # 2. Poll status
        polled = await coordinator.get_status(progress.job_id)
        self.assertIsNotNone(polled)
        assert polled is not None
        self.assertEqual(polled.job_id, progress.job_id)

        # 3. Advance through stages
        await coordinator.advance_stage(
            progress.job_id,
            status=IngestionJobStatus.CHUNKING,
            stage_name="semantic_chunking",
            percent=50.0,
            chunks_count=12,
        )
        updated = await coordinator.get_status(progress.job_id)
        assert updated is not None
        self.assertEqual(updated.status, IngestionJobStatus.CHUNKING)
        self.assertEqual(updated.progress_percent, 50.0)
        self.assertEqual(updated.chunks_generated, 12)

        # 4. Advance to COMPLETED
        await coordinator.advance_stage(
            progress.job_id,
            status=IngestionJobStatus.COMPLETED,
            stage_name="indexing_complete",
            percent=100.0,
            embeddings_count=12,
        )
        completed = await coordinator.get_status(progress.job_id)
        assert completed is not None
        self.assertEqual(completed.status, IngestionJobStatus.COMPLETED)
        self.assertEqual(completed.progress_percent, 100.0)
        self.assertEqual(completed.embeddings_generated, 12)
        self.assertIsNotNone(completed.completed_at)

        # 5. Check statistics
        stats = await coordinator.get_statistics(org_id)
        self.assertEqual(stats.total_jobs, 1)
        self.assertEqual(stats.completed_jobs, 1)
        self.assertEqual(stats.failed_jobs, 0)
        self.assertEqual(stats.total_chunks_indexed, 12)

    @pytest.mark.asyncio
    async def test_in_memory_ingestion_coordinator_retry_flow(self) -> None:
        """Verify retry behavior of failed ingestion jobs."""
        coordinator = InMemoryIngestionCoordinator()
        config = IngestionJobConfig(
            document_id=uuid4(),
            document_version_id=uuid4(),
            organization_id=uuid4(),
        )

        progress = await coordinator.start_ingestion(config)
        job_id = progress.job_id

        # Mark as FAILED
        await coordinator.advance_stage(
            job_id,
            status=IngestionJobStatus.FAILED,
            stage_name="ocr_timeout",
            percent=30.0,
        )

        # Retry failed job
        retried = await coordinator.retry_job(job_id)
        self.assertEqual(retried.status, IngestionJobStatus.RETRYING)
        self.assertEqual(retried.retry_count, 1)

        # Attempting to retry a non-failed job must raise ValueError
        with self.assertRaises(ValueError):
            await coordinator.retry_job(job_id)


if __name__ == "__main__":
    unittest.main()
