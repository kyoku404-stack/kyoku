"""Integration Tests for Ingestion REST API Endpoints (Phase 2.1).

Verifies all 5 Ingestion endpoints defined in docs/api/api-contract.md Section 8:
1. POST /api/v1/ingestion/start        (Enqueues async ingestion job, returns 202 Accepted)
2. GET  /api/v1/ingestion/status/{id}   (Queries real-time job progress and stage metrics)
3. GET  /api/v1/ingestion/jobs          (Paginated listing with filters)
4. POST /api/v1/ingestion/retry/{id}    (Re-enqueues failed jobs with backoff)
5. GET  /api/v1/ingestion/statistics   (Tenant-level operational aggregate metrics)

Specification: devdocs/p2/p2.1.txt Chapters 15 & 16 & docs/api/api-contract.md Section 8
Owner: Member 2 (Backend Lead)
"""

import unittest
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.document import Document
from backend.app.models.document_version import DocumentVersion
from backend.app.models.ingestion_job import IngestionJob
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestIngestionEndpointsIntegration(unittest.TestCase):
    """Integration test suite for Phase 2.1 Ingestion REST APIs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            # 1. Tenant organization
            cls.org = Organization(
                name="Ingestion Test Org",
                domain=f"ingest-{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            # 2. Org Admin user
            cls.admin_user = User(
                email=f"admin-{uuid4().hex[:6]}@ingest.com",
                hashed_password=get_password_hash("AdminPass123!"),
                full_name="Ingestion Admin",
                organization_id=cls.org_id,
                role="OrgAdmin",
            )
            # 3. Regular Member user
            cls.member_user = User(
                email=f"member-{uuid4().hex[:6]}@ingest.com",
                hashed_password=get_password_hash("MemberPass123!"),
                full_name="Ingestion Member",
                organization_id=cls.org_id,
                role="Member",
            )
            # 4. Viewer user
            cls.viewer_user = User(
                email=f"viewer-{uuid4().hex[:6]}@ingest.com",
                hashed_password=get_password_hash("ViewerPass123!"),
                full_name="Ingestion Viewer",
                organization_id=cls.org_id,
                role="Viewer",
            )
            session.add_all([cls.admin_user, cls.member_user, cls.viewer_user])
            session.commit()
            session.refresh(cls.admin_user)
            session.refresh(cls.member_user)
            session.refresh(cls.viewer_user)

            cls.admin_id = cls.admin_user.id
            cls.admin_email = cls.admin_user.email
            cls.member_id = cls.member_user.id
            cls.member_email = cls.member_user.email
            cls.viewer_id = cls.viewer_user.id
            cls.viewer_email = cls.viewer_user.email

            # Create sample document file on disk
            storage_dir = Path(settings.STORAGE_ROOT) / str(cls.org_id)
            storage_dir.mkdir(parents=True, exist_ok=True)
            sample_file = storage_dir / "sample_report.md"
            sample_file.write_text(
                "# Annual Security Report\n\nAll cryptographic keys have been rotated successfully.\n\n"
                "## Incident Metrics\nZero uncontained breaches recorded in FY2026.\n",
                encoding="utf-8",
            )

            # Create document in DB
            cls.test_doc = Document(
                id=uuid4(),
                organization_id=cls.org_id,
                uploader_id=cls.member_id,
                filename="sample_report.md",
                original_filename="sample_report.md",
                title="Annual Security Report",
                file_path=str(sample_file),
                file_type="md",
                mime_type="text/markdown",
                file_size=len(sample_file.read_bytes()),
                status="AWAITING_PROCESSING",
            )
            session.add(cls.test_doc)
            session.commit()
            session.refresh(cls.test_doc)
            cls.doc_id = cls.test_doc.id

            # Create version in DB
            cls.test_version = DocumentVersion(
                id=uuid4(),
                document_id=cls.doc_id,
                version_number=1,
                file_path=str(sample_file),
                file_size=len(sample_file.read_bytes()),
                checksum_sha256="fake-checksum-123",
                mime_type="text/markdown",
                uploader_id=cls.member_id,
            )
            session.add(cls.test_version)
            session.commit()
            session.refresh(cls.test_version)
            cls.version_id = cls.test_version.id

            cls.test_doc.current_version_id = cls.version_id
            session.commit()

        # Generate JWT tokens
        cls.admin_token = create_access_token(
            {
                "sub": str(cls.admin_id),
                "email": cls.admin_email,
                "org_id": str(cls.org_id),
                "role": "OrgAdmin",
            }
        )
        cls.member_token = create_access_token(
            {
                "sub": str(cls.member_id),
                "email": cls.member_email,
                "org_id": str(cls.org_id),
                "role": "Member",
            }
        )
        cls.viewer_token = create_access_token(
            {
                "sub": str(cls.viewer_id),
                "email": cls.viewer_email,
                "org_id": str(cls.org_id),
                "role": "Viewer",
            }
        )

        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}
        cls.member_headers = {"Authorization": f"Bearer {cls.member_token}"}
        cls.viewer_headers = {"Authorization": f"Bearer {cls.viewer_token}"}

    def test_start_ingestion_success(self) -> None:
        """POST /api/v1/ingestion/start creates a job and returns 202 Accepted."""
        payload = {
            "document_id": str(self.test_doc.id),
            "document_version_id": str(self.test_version.id),
            "force_ocr": False,
            "chunking_strategy": "SEMANTIC_HEADING_AWARE",
            "target_chunk_size": 512,
            "chunk_overlap": 50,
            "embedding_provider": "OPENAI",
            "embedding_model": "text-embedding-3-small",
        }
        res = self.client.post(
            "/api/v1/ingestion/start",
            json=payload,
            headers=self.member_headers,
        )
        self.assertEqual(res.status_code, 202)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["message"], "Document ingestion job enqueued successfully.")
        self.assertIn("job_id", body["data"])
        self.assertEqual(body["data"]["document_id"], str(self.test_doc.id))
        self.assertEqual(body["data"]["status"], "PENDING")
        self.assertEqual(body["data"]["queue_name"], "ai_ingestion_queue")

    def test_start_ingestion_document_not_found(self) -> None:
        """POST /api/v1/ingestion/start returns 404 for unknown document ID."""
        payload = {
            "document_id": str(uuid4()),
            "chunking_strategy": "SEMANTIC_HEADING_AWARE",
        }
        res = self.client.post(
            "/api/v1/ingestion/start",
            json=payload,
            headers=self.admin_headers,
        )
        self.assertEqual(res.status_code, 404)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], "NOT_FOUND")

    def test_get_ingestion_status(self) -> None:
        """GET /api/v1/ingestion/status/{id} retrieves real-time pipeline status."""
        # 1. Start job
        payload = {"document_id": str(self.test_doc.id)}
        start_res = self.client.post(
            "/api/v1/ingestion/start",
            json=payload,
            headers=self.admin_headers,
        )
        job_id = start_res.json()["data"]["job_id"]

        # 2. Query status
        status_res = self.client.get(
            f"/api/v1/ingestion/status/{job_id}",
            headers=self.member_headers,
        )
        self.assertEqual(status_res.status_code, 200)
        body = status_res.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["job_id"], job_id)
        self.assertEqual(body["data"]["document_id"], str(self.test_doc.id))
        self.assertIn("status", body["data"])
        self.assertIn("progress_percent", body["data"])
        self.assertIn("current_stage", body["data"])

    def test_get_ingestion_status_not_found(self) -> None:
        """GET /api/v1/ingestion/status/{id} returns 404 for unknown ID."""
        res = self.client.get(
            f"/api/v1/ingestion/status/{uuid4()}",
            headers=self.member_headers,
        )
        self.assertEqual(res.status_code, 404)

    def test_list_ingestion_jobs_paginated(self) -> None:
        """GET /api/v1/ingestion/jobs returns paginated job items."""
        res = self.client.get(
            "/api/v1/ingestion/jobs?page=1&page_size=10",
            headers=self.member_headers,
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertIn("items", body["data"])
        self.assertIn("total", body["data"])
        self.assertIn("page", body["data"])
        self.assertIn("page_size", body["data"])
        self.assertIn("total_pages", body["data"])

    def test_retry_failed_job_success(self) -> None:
        """POST /api/v1/ingestion/retry/{id} re-enqueues a failed job."""
        # Insert a failed job into database
        failed_job_id = uuid4()
        with Session(sync_test_engine) as session:
            failed_job = IngestionJob(
                id=failed_job_id,
                organization_id=self.org_id,
                document_id=self.test_doc.id,
                document_version_id=self.test_version.id,
                status="FAILED",
                current_stage="failed",
                error_message="Simulated parser failure for retry test",
                retry_count=0,
            )
            session.add(failed_job)
            session.commit()

        # Retry endpoint
        retry_res = self.client.post(
            f"/api/v1/ingestion/retry/{failed_job_id}",
            headers=self.admin_headers,
        )
        self.assertEqual(retry_res.status_code, 200)
        body = retry_res.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["job_id"], str(failed_job_id))
        self.assertEqual(body["data"]["status"], "RETRYING")
        self.assertEqual(body["data"]["retry_count"], 1)

    def test_retry_non_failed_job_returns_error(self) -> None:
        """POST /api/v1/ingestion/retry/{id} rejects retrying a COMPLETED job."""
        completed_job_id = uuid4()
        with Session(sync_test_engine) as session:
            completed_job = IngestionJob(
                id=completed_job_id,
                organization_id=self.org_id,
                document_id=self.test_doc.id,
                document_version_id=self.test_version.id,
                status="COMPLETED",
                current_stage="completed",
                progress_percent=100.0,
            )
            session.add(completed_job)
            session.commit()

        retry_res = self.client.post(
            f"/api/v1/ingestion/retry/{completed_job_id}",
            headers=self.admin_headers,
        )
        self.assertIn(retry_res.status_code, (400, 422))
        body = retry_res.json()
        self.assertFalse(body["success"])

    def test_get_ingestion_statistics(self) -> None:
        """GET /api/v1/ingestion/statistics aggregates tenant operational metrics."""
        res = self.client.get(
            "/api/v1/ingestion/statistics",
            headers=self.admin_headers,
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        stats = body["data"]
        self.assertEqual(stats["organization_id"], str(self.org_id))
        self.assertIn("total_jobs", stats)
        self.assertIn("completed_jobs", stats)
        self.assertIn("failed_jobs", stats)
        self.assertIn("pending_jobs", stats)
        self.assertIn("total_chunks_indexed", stats)
        self.assertIn("average_duration_seconds", stats)
        self.assertIn("ocr_utilization_percent", stats)
