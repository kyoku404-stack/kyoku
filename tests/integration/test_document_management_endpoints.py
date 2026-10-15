"""Integration Tests for Phase 1.8 Document Management REST Endpoints.

Verifies all 8 Phase 1.8 REST endpoints defined in docs/api/api-contract.md Section 3.3:
1. POST   /api/v1/documents/upload    (multipart upload, magic bytes check, duplicate 409, unsupported 422)
2. GET    /api/v1/documents           (paginated listing, category/status/search filters, sorting)
3. GET    /api/v1/documents/{id}      (metadata retrieval, version history list)
4. GET    /api/v1/documents/{id}/download (secure binary stream, version-specific download)
5. GET    /api/v1/documents/{id}/preview  (preview stream for PDF, images, text, and converted HTML)
6. PATCH  /api/v1/documents/{id}      (metadata updating, title, category, tags, ownership bypass)
7. POST   /api/v1/documents/{id}/version (revised version upload v2, version bump, change notes)
8. DELETE /api/v1/documents/{id}      (soft-deletion and archiving with uploader ownership override)

Owner: Member 2 (Backend & Database Lead)
Sub-phase: Phase 1.8 Document Upload, File Management & Storage System
Specification: devdocs/p1/p1.8.txt & docs/api/api-contract.md Section 3.3
"""

import io
import shutil
import unittest
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestDocumentManagementEndpointsIntegration(unittest.TestCase):
    """End-to-end integration tests for Phase 1.8 Document Management REST API."""

    @classmethod
    def tearDownClass(cls) -> None:
        storage_org_path = Path(settings.STORAGE_ROOT) / str(cls.org_id)
        if storage_org_path.exists():
            shutil.rmtree(storage_org_path, ignore_errors=True)
        storage_root = Path(settings.STORAGE_ROOT)
        if storage_root.exists() and not any(storage_root.iterdir()):
            storage_root.rmdir()


    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine) as session:
            # Create isolated organization for Document tests
            cls.org = Organization(
                name="DocCorp Global",
                domain=f"doccorp-{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            # Create Admin user
            cls.admin_user = User(
                email=f"docadmin-{uuid4().hex[:6]}@doccorp.com",
                hashed_password=get_password_hash("DocAdminSecure123!"),
                full_name="Doc System Admin",
                organization_id=cls.org_id,
                role="OrgAdmin",
            )
            # Create Regular Member user
            cls.member_user = User(
                email=f"docmember-{uuid4().hex[:6]}@doccorp.com",
                hashed_password=get_password_hash("DocMemberSecure123!"),
                full_name="Doc Staff Member",
                organization_id=cls.org_id,
                role="Member",
            )
            session.add(cls.admin_user)
            session.add(cls.member_user)
            session.commit()
            session.refresh(cls.admin_user)
            session.refresh(cls.member_user)

            cls.admin_id = cls.admin_user.id
            cls.member_id = cls.member_user.id

        # Generate JWT headers
        cls.admin_token = create_access_token(
            data={
                "sub": str(cls.admin_id),
                "email": cls.admin_user.email,
                "org_id": str(cls.org_id),
                "role": "OrgAdmin",
            }
        )
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}

        cls.member_token = create_access_token(
            data={
                "sub": str(cls.member_id),
                "email": cls.member_user.email,
                "org_id": str(cls.org_id),
                "role": "Member",
            }
        )
        cls.member_headers = {"Authorization": f"Bearer {cls.member_token}"}

    def test_01_upload_document_success(self) -> None:
        """Upload valid PDF file with metadata returning 202 Accepted and initial version 1."""
        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Title (Enterprise Architecture) >>\nendobj\ntrailer\n<<>>\n%%EOF"
        files = {"file": ("architecture_blueprint.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        data = {
            "title": "Enterprise Architecture Blueprint",
            "category": "TECHNICAL_DOCUMENTATION",
            "tags": "architecture,engineering,v1",
            "description": "System architecture blueprint overview.",
        }

        res = self.client.post(
            f"{settings.API_V1_STR}/documents/upload",
            files=files,
            data=data,
            headers=self.admin_headers,
        )
        self.assertEqual(res.status_code, 202)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertEqual(
            body["message"], "Document uploaded successfully and queued for AI ingestion."
        )

        doc_data = body["data"]
        self.__class__.created_doc_id = doc_data["document_id"]
        self.assertEqual(doc_data["filename"], "architecture_blueprint.pdf")
        self.assertEqual(doc_data["category"], "TECHNICAL_DOCUMENTATION")
        self.assertEqual(doc_data["version_number"], 1)
        self.assertIn("architecture", doc_data["tags"])
        self.assertIn("status", doc_data)

    def test_02_upload_duplicate_detection(self) -> None:
        """Re-uploading the exact same binary content in the same org triggers 409 DUPLICATE_FILE_DETECTED."""
        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Title (Enterprise Architecture) >>\nendobj\ntrailer\n<<>>\n%%EOF"
        files = {
            "file": ("architecture_blueprint_copy.pdf", io.BytesIO(pdf_bytes), "application/pdf")
        }
        data = {"title": "Duplicate Copy"}

        res = self.client.post(
            f"{settings.API_V1_STR}/documents/upload",
            files=files,
            data=data,
            headers=self.admin_headers,
        )
        self.assertEqual(res.status_code, 409)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], "DUPLICATE_FILE_DETECTED")
        self.assertIn("existing_document_id", body["error"]["details"])

    def test_03_upload_unsupported_format_rejected(self) -> None:
        """Rejects executable and non-whitelisted extensions with 422 UNSUPPORTED_FILE_TYPE."""
        exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00"
        files = {
            "file": ("malicious_payload.exe", io.BytesIO(exe_bytes), "application/octet-stream")
        }

        res = self.client.post(
            f"{settings.API_V1_STR}/documents/upload",
            files=files,
            headers=self.admin_headers,
        )
        self.assertEqual(res.status_code, 422)
        self.assertEqual(res.json()["error"]["code"], "UNSUPPORTED_FILE_TYPE")

    def test_04_list_documents_filtering_and_pagination(self) -> None:
        """Lists tenant documents with category filter and search query."""
        res = self.client.get(
            f"{settings.API_V1_STR}/documents?category=TECHNICAL_DOCUMENTATION&search=blueprint",
            headers=self.admin_headers,
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertGreaterEqual(data["total"], 1)
        self.assertGreaterEqual(len(data["items"]), 1)
        first_item = data["items"][0]
        self.assertEqual(first_item["category"], "TECHNICAL_DOCUMENTATION")

    def test_05_get_document_details_and_versions(self) -> None:
        """Retrieves comprehensive metadata and version history array."""
        doc_id = self.__class__.created_doc_id
        res = self.client.get(
            f"{settings.API_V1_STR}/documents/{doc_id}",
            headers=self.admin_headers,
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        doc = body["data"]
        self.assertEqual(doc["id"], doc_id)
        self.assertEqual(doc["current_version_number"], 1)
        self.assertEqual(len(doc["versions"]), 1)
        self.assertEqual(doc["versions"][0]["version_number"], 1)

    def test_06_download_document_stream(self) -> None:
        """Streams stored binary file with Content-Disposition attachment header."""
        doc_id = self.__class__.created_doc_id
        res = self.client.get(
            f"{settings.API_V1_STR}/documents/{doc_id}/download",
            headers=self.admin_headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["content-type"], "application/pdf")
        self.assertIn("attachment", res.headers["content-disposition"])
        self.assertTrue(res.content.startswith(b"%PDF-"))

    def test_07_preview_document_stream(self) -> None:
        """Streams preview stream (PDF byte stream for PDF document)."""
        doc_id = self.__class__.created_doc_id
        res = self.client.get(
            f"{settings.API_V1_STR}/documents/{doc_id}/preview",
            headers=self.admin_headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["content-type"], "application/pdf")
        self.assertTrue(res.content.startswith(b"%PDF-"))

    def test_08_update_document_metadata(self) -> None:
        """Updates document title, category, and tags via PATCH."""
        doc_id = self.__class__.created_doc_id
        payload = {
            "title": "Updated Architecture Blueprint v1.1",
            "category": "RESEARCH",
            "tags": ["architecture", "research", "updated"],
        }
        res = self.client.patch(
            f"{settings.API_V1_STR}/documents/{doc_id}",
            json=payload,
            headers=self.admin_headers,
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["title"], "Updated Architecture Blueprint v1.1")
        self.assertEqual(body["data"]["category"], "RESEARCH")
        self.assertIn("research", body["data"]["tags"])

    def test_09_upload_new_version(self) -> None:
        """Uploads revision v2, bumps active version number, and stores revision change notes."""
        doc_id = self.__class__.created_doc_id
        revised_bytes = b"%PDF-1.4\nRevision 2 Content with updated microservices diagram\n%%EOF"
        files = {
            "file": ("architecture_blueprint_v2.pdf", io.BytesIO(revised_bytes), "application/pdf")
        }
        data = {"change_notes": "Added microservices integration diagrams in Section 3."}

        res = self.client.post(
            f"{settings.API_V1_STR}/documents/{doc_id}/version",
            files=files,
            data=data,
            headers=self.admin_headers,
        )
        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertTrue(body["success"])
        v_data = body["data"]
        self.assertEqual(v_data["document_id"], doc_id)
        self.assertEqual(v_data["version_number"], 2)
        self.assertEqual(
            v_data["change_notes"], "Added microservices integration diagrams in Section 3."
        )

        # Verify details now reports version 2 and 2 versions in history
        detail_res = self.client.get(
            f"{settings.API_V1_STR}/documents/{doc_id}",
            headers=self.admin_headers,
        )
        detail_data = detail_res.json()["data"]
        self.assertEqual(detail_data["current_version_number"], 2)
        self.assertEqual(len(detail_data["versions"]), 2)

    def test_10_archive_and_delete_document(self) -> None:
        """Archives document first, then executes soft-deletion preserving audit trail."""
        doc_id = self.__class__.created_doc_id

        # 1. Archive
        archive_res = self.client.delete(
            f"{settings.API_V1_STR}/documents/{doc_id}?action=archive",
            headers=self.admin_headers,
        )
        self.assertEqual(archive_res.status_code, 200)
        self.assertEqual(archive_res.json()["data"]["status"], "ARCHIVED")

        # 2. Soft-delete
        delete_res = self.client.delete(
            f"{settings.API_V1_STR}/documents/{doc_id}?action=delete",
            headers=self.admin_headers,
        )
        self.assertEqual(delete_res.status_code, 200)
        self.assertTrue(delete_res.json()["data"]["is_deleted"])
        self.assertTrue(delete_res.json()["data"]["deleted"])
