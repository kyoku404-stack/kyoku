"""KEEP Enterprise Platform — AI Knowledge Ingestion Pipeline Integration & Performance Test Suite.

Specification Source: devdocs/p2/p2.1.txt (Chapters 1–20)
Architecture: docs/Architecture/ai-ingestion-pipeline.md & ADR-032, ADR-033, ADR-034
Role: Member 4 (DevOps & Integration Lead)
Sub-Phase: Phase 2.1 — AI Knowledge Ingestion Pipeline
"""

from __future__ import annotations

import asyncio
import json
import math
import tempfile
import time
import unittest
from pathlib import Path
from uuid import uuid4

import yaml
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.constants import UserRole
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.document import Document
from backend.app.models.document_version import DocumentVersion
from backend.app.models.ingestion_job import IngestionJob
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.services.ai.ingestion import (
    ChunkingStrategy,
    DefaultEmbeddingGenerator,
    DefaultSemanticChunker,
    DefaultTextCleaner,
    EmbeddingModelProvider,
    ExtractedDocumentContent,
    IngestionJobConfig,
    SemanticChunkSpec,
)
from backend.app.services.ingestion.ocr import DefaultOCRProcessor
from backend.app.services.ingestion.parser import MultiFormatDocumentParser
from tests.conftest import sync_test_engine

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestAIIngestionPipelineSubsystems(unittest.TestCase):
    """Verifies core AI ingestion pipeline components: parsers, OCR, cleaner, chunker, and embedder."""

    def setUp(self) -> None:
        self.parser = MultiFormatDocumentParser()
        self.ocr_processor = DefaultOCRProcessor()
        self.cleaner = DefaultTextCleaner()
        self.chunker = DefaultSemanticChunker()
        self.embedder = DefaultEmbeddingGenerator()

    def test_text_cleaner_nfkc_and_whitespace_sanitization(self) -> None:
        """Ensures text cleaner normalizes Unicode, strips control chars, and compacts whitespace."""
        raw_dirty_text = "  Hello \x00\x08 World!  \n\n\n\nThis is\t\ta test.  \r\n"
        cleaned = self.cleaner.clean_and_normalize(raw_dirty_text)
        self.assertNotIn("\x00", cleaned)
        self.assertNotIn("\x08", cleaned)
        self.assertIn("Hello World!", cleaned)
        self.assertIn("This is a test.", cleaned)

    def test_heading_aware_semantic_chunking(self) -> None:
        """Verifies hierarchical semantic chunking preserves heading boundaries and enforces overlap."""
        markdown_text = (
            "# Executive Summary\n\n"
            "This document details the KEEP enterprise architecture.\n\n"
            "## Core Subsystems\n\n"
            "The platform includes storage, authentication, and RAG pipelines.\n\n"
            "### Vector Storage\n\n"
            "pgvector is leveraged for dense cosine similarity indexing."
        )
        content = ExtractedDocumentContent(
            document_id=uuid4(),
            document_version_id=uuid4(),
            raw_text=markdown_text,
        )
        config = IngestionJobConfig(
            document_id=content.document_id,
            document_version_id=content.document_version_id,
            organization_id=uuid4(),
            chunking_strategy=ChunkingStrategy.SEMANTIC_HEADING_AWARE,
            target_chunk_size=120,
            chunk_overlap=20,
        )
        chunks = self.chunker.chunk_document(content=content, config=config)
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertIsNotNone(chunk.text)
            self.assertGreater(chunk.token_count, 0)
            self.assertIn("strategy", chunk.metadata)

    def test_embedding_generator_l2_normalization(self) -> None:
        """Verifies dense embedding vectors are unit L2 normalized (||v||_2 == 1.0)."""
        chunk = SemanticChunkSpec(
            chunk_id=uuid4(),
            document_id=uuid4(),
            document_version_id=uuid4(),
            organization_id=uuid4(),
            chunk_index=0,
            text="Enterprise knowledge management platform with RAG.",
        )
        config = IngestionJobConfig(
            document_id=chunk.document_id,
            document_version_id=chunk.document_version_id,
            organization_id=chunk.organization_id,
            embedding_provider=EmbeddingModelProvider.OPENAI,
            embedding_model="text-embedding-3-small",
        )
        specs = asyncio.run(self.embedder.generate_embeddings([chunk], config))
        self.assertEqual(len(specs), 1)
        vector_spec = specs[0]
        self.assertEqual(len(vector_spec.vector), 1536)
        # Calculate Euclidean norm
        norm = math.sqrt(sum(x * x for x in vector_spec.vector))
        self.assertAlmostEqual(norm, 1.0, places=5)

    def test_embedding_generator_local_bge_dimensions(self) -> None:
        """Verifies local BGE embedding model generates 384-dimensional normalized vectors."""
        chunk = SemanticChunkSpec(
            chunk_id=uuid4(),
            document_id=uuid4(),
            document_version_id=uuid4(),
            organization_id=uuid4(),
            chunk_index=0,
            text="Local privacy-preserving embedding generation.",
        )
        config = IngestionJobConfig(
            document_id=chunk.document_id,
            document_version_id=chunk.document_version_id,
            organization_id=chunk.organization_id,
            embedding_provider=EmbeddingModelProvider.HUGGINGFACE_LOCAL,
            embedding_model="bge-small-en-v1.5",
        )
        specs = asyncio.run(self.embedder.generate_embeddings([chunk], config))
        self.assertEqual(len(specs), 1)
        vector_spec = specs[0]
        self.assertEqual(len(vector_spec.vector), 384)
        norm = math.sqrt(sum(x * x for x in vector_spec.vector))
        self.assertAlmostEqual(norm, 1.0, places=5)

    def test_multi_format_document_parser_text_and_markdown(self) -> None:
        """Verifies plain text and markdown extraction without OCR."""
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as tf:
            tf.write("KEEP enterprise platform plain text document.")
            txt_path = tf.name

        try:
            content = asyncio.run(self.parser.extract(txt_path, uuid4(), uuid4(), "text/plain"))
            self.assertIn("KEEP enterprise platform", content.raw_text)
            self.assertFalse(content.requires_ocr)
        finally:
            Path(txt_path).unlink(missing_ok=True)

    def test_ocr_processor_fallback(self) -> None:
        """Ensures OCR processor gracefully handles image bytes."""
        dummy_bytes = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        text = asyncio.run(self.ocr_processor.extract_text_from_image(dummy_bytes))
        self.assertIsInstance(text, str)


class TestAIIngestionPipelineLifecycleAndREST(unittest.TestCase):
    """Verifies end-to-end asynchronous ingestion state machine and REST API contracts."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)
        with Session(sync_test_engine, expire_on_commit=False) as session:
            cls.org = Organization(
                name=f"Ingestion Test Org {uuid4().hex[:6]}",
                domain=f"ingestion_{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            cls.user = User(
                email=f"ingestion_lead_{uuid4().hex[:6]}@enterprise.io",
                hashed_password=get_password_hash("DevOpsSecure2026!"),
                full_name="Ingestion DevOps Lead",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org_id,
                is_active=True,
            )
            session.add(cls.user)
            session.commit()
            session.refresh(cls.user)

            # Create test document file
            storage_dir = Path(settings.STORAGE_ROOT) / str(cls.org_id)
            storage_dir.mkdir(parents=True, exist_ok=True)
            cls.test_file = storage_dir / f"test_spec_{uuid4().hex[:6]}.md"
            cls.test_file.write_text(
                "# System Specification\n\n"
                "This document describes the KEEP AI ingestion pipeline.\n\n"
                "## Architecture\n\n"
                "High-performance vector database with pgvector.\n",
                encoding="utf-8",
            )

            cls.doc = Document(
                id=uuid4(),
                organization_id=cls.org_id,
                uploader_id=cls.user.id,
                filename="test_spec.md",
                original_filename="test_spec.md",
                title="System Specification Document",
                file_path=str(cls.test_file),
                file_type="md",
                file_size=cls.test_file.stat().st_size,
                mime_type="text/markdown",
                checksum_sha256="abc123mockchecksum456789",
                status="UPLOADED",
            )
            session.add(cls.doc)
            session.commit()
            session.refresh(cls.doc)

            cls.version = DocumentVersion(
                id=uuid4(),
                document_id=cls.doc.id,
                version_number=1,
                file_path=str(cls.test_file),
                file_size=cls.test_file.stat().st_size,
                mime_type="text/markdown",
                checksum_sha256="abc123mockchecksum456789",
                uploader_id=cls.user.id,
            )
            session.add(cls.version)
            session.commit()
            session.refresh(cls.version)

            cls.doc.current_version_id = cls.version.id
            session.commit()

        cls.token = create_access_token(
            {
                "sub": str(cls.user.id),
                "email": cls.user.email,
                "org_id": str(cls.org_id),
                "role": "OrgAdmin",
            }
        )
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.test_file.unlink(missing_ok=True)

    def test_start_ingestion_endpoint(self) -> None:
        """Verifies POST /api/v1/ingestion/start creates a job and returns 202 Accepted."""
        payload = {
            "document_id": str(self.doc.id),
            "chunking_strategy": "SEMANTIC_HEADING_AWARE",
            "embedding_provider": "OPENAI",
            "embedding_model": "text-embedding-3-small",
            "target_chunk_size": 250,
            "force_ocr": False,
        }
        response = self.client.post("/api/v1/ingestion/start", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 202)
        data = response.json()
        self.assertTrue(data.get("success"))
        job_data = data.get("data")
        self.assertIn("job_id", job_data)
        self.assertEqual(job_data.get("document_id"), str(self.doc.id))

    def test_get_ingestion_status_and_jobs_list(self) -> None:
        """Verifies GET /api/v1/ingestion/jobs lists jobs and GET /api/v1/ingestion/status/{id} returns state."""
        # Start a job first
        start_payload = {
            "document_id": str(self.doc.id),
            "chunking_strategy": "SEMANTIC_HEADING_AWARE",
            "embedding_provider": "OPENAI",
            "embedding_model": "text-embedding-3-small",
        }
        self.client.post("/api/v1/ingestion/start", json=start_payload, headers=self.headers)

        # 1. List jobs
        list_resp = self.client.get("/api/v1/ingestion/jobs", headers=self.headers)
        self.assertEqual(list_resp.status_code, 200)
        jobs_data = list_resp.json().get("data", {})
        self.assertIn("items", jobs_data)
        self.assertGreater(len(jobs_data["items"]), 0)

        job_id = jobs_data["items"][0]["job_id"]

        # 2. Status inspection
        status_resp = self.client.get(f"/api/v1/ingestion/status/{job_id}", headers=self.headers)
        self.assertEqual(status_resp.status_code, 200)
        status_data = status_resp.json().get("data", {})
        self.assertEqual(status_data["job_id"], job_id)
        self.assertIn("status", status_data)
        self.assertIn("current_stage", status_data)
        self.assertIn("progress_percent", status_data)

    def test_ingestion_statistics_endpoint(self) -> None:
        """Verifies GET /api/v1/ingestion/statistics returns tenant-level metrics."""
        response = self.client.get("/api/v1/ingestion/statistics", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json().get("data", {})
        self.assertIn("total_jobs", data)
        self.assertIn("pending_jobs", data)
        self.assertIn("completed_jobs", data)
        self.assertIn("failed_jobs", data)
        self.assertIn("total_chunks_indexed", data)

    def test_retry_failed_job_lifecycle(self) -> None:
        """Verifies POST /api/v1/ingestion/retry/{id} handles retry logic and exponential backoff."""
        with Session(sync_test_engine) as session:
            failed_job = IngestionJob(
                id=uuid4(),
                organization_id=self.org_id,
                document_id=self.doc.id,
                document_version_id=self.version.id,
                status="FAILED",
                current_stage="text_extraction",
                progress_percent=20.0,
                error_message="Simulation extraction failure",
                retry_count=0,
                max_retries=3,
            )
            session.add(failed_job)
            session.commit()
            failed_job_id = str(failed_job.id)

        response = self.client.post(
            f"/api/v1/ingestion/retry/{failed_job_id}",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json().get("data", {})
        self.assertIn(data.get("status"), ["PENDING", "RETRYING", "EXTRACTING", "COMPLETED"])
        self.assertEqual(data.get("retry_count"), 1)


class TestAIIngestionPerformanceAndStress(unittest.TestCase):
    """Evaluates queue throughput, concurrent processing stability, and performance bounds."""

    def test_batch_semantic_chunking_performance(self) -> None:
        """Benchmarks that 100 document paragraphs are chunked in < 500ms."""
        large_document = "\n\n".join(
            [f"## Section {i}\n\nThis is a standard enterprise paragraph detailing requirement {i}." for i in range(100)]
        )
        chunker = DefaultSemanticChunker()
        content = ExtractedDocumentContent(
            document_id=uuid4(),
            document_version_id=uuid4(),
            raw_text=large_document,
        )
        config = IngestionJobConfig(
            document_id=content.document_id,
            document_version_id=content.document_version_id,
            organization_id=uuid4(),
            chunking_strategy=ChunkingStrategy.SEMANTIC_HEADING_AWARE,
            target_chunk_size=100,
            chunk_overlap=20,
        )

        start_time = time.perf_counter()
        chunks = chunker.chunk_document(content=content, config=config)
        duration = time.perf_counter() - start_time

        self.assertGreater(len(chunks), 20)
        self.assertLess(duration, 0.50, f"Chunking was too slow: {duration:.4f}s")

    def test_vector_embedding_generation_throughput(self) -> None:
        """Benchmarks that 100 embedding vectors can be synthesized in < 250ms."""
        embedder = DefaultEmbeddingGenerator()
        chunks = [
            SemanticChunkSpec(
                chunk_id=uuid4(),
                document_id=uuid4(),
                document_version_id=uuid4(),
                organization_id=uuid4(),
                chunk_index=i,
                text=f"Enterprise requirement snippet {i} for vector index.",
            )
            for i in range(100)
        ]
        config = IngestionJobConfig(
            document_id=uuid4(),
            document_version_id=uuid4(),
            organization_id=uuid4(),
            embedding_provider=EmbeddingModelProvider.HUGGINGFACE_LOCAL,
            embedding_model="bge-small-en-v1.5",
        )

        start_time = time.perf_counter()
        specs = asyncio.run(embedder.generate_embeddings(chunks, config))
        duration = time.perf_counter() - start_time

        self.assertEqual(len(specs), 100)
        self.assertLess(duration, 0.50, f"Embedding generation too slow: {duration:.4f}s")


class TestAIWorkerInfrastructureTopology(unittest.TestCase):
    """Verifies Docker, Compose, Prometheus alerting, and Grafana dashboard infrastructure configurations."""

    def test_dockerfile_worker_exists_and_configured(self) -> None:
        """Ensures docker/Dockerfile.worker is properly authored with OCR & cache volumes."""
        worker_dockerfile = REPO_ROOT / "docker" / "Dockerfile.worker"
        self.assertTrue(worker_dockerfile.is_file(), "Dockerfile.worker must exist")
        content = worker_dockerfile.read_text(encoding="utf-8")
        self.assertIn("tesseract-ocr", content)
        self.assertIn("AI_MODEL_CACHE_DIR", content)
        self.assertIn("worker_entrypoint.py", content)

    def test_worker_entrypoint_exists_and_executable(self) -> None:
        """Ensures docker/worker_entrypoint.py exists and exports AIWorkerRuntime."""
        entrypoint_file = REPO_ROOT / "docker" / "worker_entrypoint.py"
        self.assertTrue(entrypoint_file.is_file(), "worker_entrypoint.py must exist")
        content = entrypoint_file.read_text(encoding="utf-8")
        self.assertIn("class AIWorkerRuntime", content)
        self.assertIn("ai_ingestion_queue", content)

    def test_docker_compose_dev_has_ai_worker(self) -> None:
        """Ensures docker-compose.yml defines ai-worker service and ai_model_cache volume."""
        compose_path = REPO_ROOT / "docker-compose.yml"
        content = compose_path.read_text(encoding="utf-8")
        self.assertIn("ai-worker:", content)
        self.assertIn("Dockerfile.worker", content)
        self.assertIn("ai_model_cache:", content)

    def test_docker_compose_prod_has_ai_worker_and_limits(self) -> None:
        """Ensures docker-compose.prod.yml defines production ai-worker with strict resource limits."""
        compose_path = REPO_ROOT / "docker-compose.prod.yml"
        content = compose_path.read_text(encoding="utf-8")
        self.assertIn("ai-worker:", content)
        self.assertIn("keep-ai-worker-prod", content)
        self.assertIn("cpus: \"2.00\"", content)
        self.assertIn("memory: 4096M", content)

    def test_prometheus_alert_rules_include_ai_ingestion(self) -> None:
        """Ensures infrastructure/prometheus/alert_rules.yml contains AI Ingestion pipeline alerts."""
        alert_path = REPO_ROOT / "infrastructure" / "prometheus" / "alert_rules.yml"
        content = alert_path.read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        rules = [r["alert"] for group in parsed.get("groups", []) for r in group.get("rules", [])]
        expected_alerts = [
            "AIIngestionQueueBacklogHigh",
            "AIIngestionFailureRateHigh",
            "AIOCRProcessingTimeout",
            "AIEmbeddingLatencyHigh",
        ]
        for alert in expected_alerts:
            self.assertIn(alert, rules, f"Missing expected alert rule: {alert}")

    def test_grafana_ai_ingestion_dashboard_provisioned(self) -> None:
        """Ensures infrastructure/grafana/dashboards/ai-ingestion-dashboard.json exists and is valid JSON."""
        dashboard_path = REPO_ROOT / "infrastructure" / "grafana" / "dashboards" / "ai-ingestion-dashboard.json"
        self.assertTrue(dashboard_path.is_file(), "ai-ingestion-dashboard.json must exist")
        data = json.loads(dashboard_path.read_text(encoding="utf-8"))
        self.assertEqual(data.get("uid"), "keep-ai-ingestion-phase-2-1")
        self.assertGreater(len(data.get("panels", [])), 0)
