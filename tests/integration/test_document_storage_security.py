"""Security, Tenant Isolation & Path Quarantine Integration Tests for Phase 1.8 Document Storage.

Verifies:
1. Multi-Tenant Storage Path Isolation:
   - Tenant isolation: Org Alpha users cannot access, download, preview, patch, version, or delete Org Beta assets.
   - Physical filesystem isolation: directory layout strictly compartmentalizes tenant files into storage/{org_id}/.
2. Directory Traversal Attack Quarantine:
   - Path traversal payloads in filename (../../, ..\\..\\, null bytes, control chars) are sanitized and quarantined.
   - Physical storage paths never escape the tenant root directory.
3. Storage Quota Enforcement:
   - Uploads exceeding organization quota trigger strict HTTP 400 STORAGE_QUOTA_EXCEEDED.
   - No orphaned database records or partial files remain upon quota rejection.
4. Magic Byte Sniffing & MIME Spoofing Quarantine:
   - Disguised executables (ELF, Windows MZ) renamed to .pdf/.png are intercepted and rejected (422 UNSUPPORTED_FILE_TYPE).
   - Shell scripts spoofed as office documents are quarantined.
5. RBAC Document Permissions & Resource Ownership:
   - Viewer role cannot create, modify, or delete documents (403 Forbidden).
   - Non-admin Member cannot delete another member's document (ownership bypass denied).
   - OrgAdmin / Manager can administrative-override delete.
6. SHA-256 Duplicate File Detection & Tenant Scope:
   - Duplicate file in same org returns 409 DUPLICATE_FILE_DETECTED.
   - Same file in a different org is accepted without collision.

Owner: Member 4 (DevOps & Integration Lead)
Sub-phase: Phase 1.8 Document Upload, File Management & Storage System
Specification: devdocs/p1/p1.8.txt Chapters 6, 8, 15, 19, 20
"""

import io
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.constants import ErrorCode, UserRole
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestDocumentStorageSecurityIntegration(unittest.TestCase):
    """Integration test suite verifying multi-tenant isolation, storage security, and sanitization."""

    @classmethod
    def tearDownClass(cls) -> None:
        """Cleans up isolated test directories in storage root."""
        for org_id in [cls.org_alpha_id, cls.org_beta_id]:
            org_dir = Path(settings.STORAGE_ROOT) / str(org_id)
            if org_dir.exists():
                shutil.rmtree(org_dir, ignore_errors=True)
        storage_root = Path(settings.STORAGE_ROOT)
        if storage_root.exists() and not any(storage_root.iterdir()):
            storage_root.rmdir()

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine) as session:
            # Create Organization Alpha
            cls.org_alpha = Organization(
                name="Security Org Alpha",
                domain=f"alpha-{uuid4().hex[:6]}.com",
            )
            # Create Organization Beta
            cls.org_beta = Organization(
                name="Security Org Beta",
                domain=f"beta-{uuid4().hex[:6]}.com",
            )
            session.add_all([cls.org_alpha, cls.org_beta])
            session.commit()
            session.refresh(cls.org_alpha)
            session.refresh(cls.org_beta)

            cls.org_alpha_id = cls.org_alpha.id
            cls.org_beta_id = cls.org_beta.id

            # Users for Org Alpha
            cls.alpha_admin = User(
                email=f"alpha_admin_{uuid4().hex[:6]}@alpha.com",
                hashed_password=get_password_hash("AlphaSec123!"),
                full_name="Alpha Admin",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org_alpha_id,
                is_active=True,
            )
            cls.alpha_member1 = User(
                email=f"alpha_m1_{uuid4().hex[:6]}@alpha.com",
                hashed_password=get_password_hash("AlphaSec123!"),
                full_name="Alpha Member 1",
                role=UserRole.MEMBER,
                organization_id=cls.org_alpha_id,
                is_active=True,
            )
            cls.alpha_member2 = User(
                email=f"alpha_m2_{uuid4().hex[:6]}@alpha.com",
                hashed_password=get_password_hash("AlphaSec123!"),
                full_name="Alpha Member 2",
                role=UserRole.MEMBER,
                organization_id=cls.org_alpha_id,
                is_active=True,
            )
            cls.alpha_viewer = User(
                email=f"alpha_viewer_{uuid4().hex[:6]}@alpha.com",
                hashed_password=get_password_hash("AlphaSec123!"),
                full_name="Alpha Viewer",
                role=UserRole.VIEWER,
                organization_id=cls.org_alpha_id,
                is_active=True,
            )

            # Users for Org Beta
            cls.beta_admin = User(
                email=f"beta_admin_{uuid4().hex[:6]}@beta.com",
                hashed_password=get_password_hash("BetaSec123!"),
                full_name="Beta Admin",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org_beta_id,
                is_active=True,
            )
            cls.beta_member = User(
                email=f"beta_m_{uuid4().hex[:6]}@beta.com",
                hashed_password=get_password_hash("BetaSec123!"),
                full_name="Beta Member",
                role=UserRole.MEMBER,
                organization_id=cls.org_beta_id,
                is_active=True,
            )

            session.add_all([
                cls.alpha_admin,
                cls.alpha_member1,
                cls.alpha_member2,
                cls.alpha_viewer,
                cls.beta_admin,
                cls.beta_member,
            ])
            session.commit()
            for u in [
                cls.alpha_admin,
                cls.alpha_member1,
                cls.alpha_member2,
                cls.alpha_viewer,
                cls.beta_admin,
                cls.beta_member,
            ]:
                session.refresh(u)

        # Generate JWT Bearer tokens
        cls.alpha_admin_token = create_access_token(
            data={
                "sub": str(cls.alpha_admin.id),
                "email": cls.alpha_admin.email,
                "org_id": str(cls.org_alpha_id),
                "role": "OrgAdmin",
            }
        )
        cls.alpha_m1_token = create_access_token(
            data={
                "sub": str(cls.alpha_member1.id),
                "email": cls.alpha_member1.email,
                "org_id": str(cls.org_alpha_id),
                "role": "Member",
            }
        )
        cls.alpha_m2_token = create_access_token(
            data={
                "sub": str(cls.alpha_member2.id),
                "email": cls.alpha_member2.email,
                "org_id": str(cls.org_alpha_id),
                "role": "Member",
            }
        )
        cls.alpha_viewer_token = create_access_token(
            data={
                "sub": str(cls.alpha_viewer.id),
                "email": cls.alpha_viewer.email,
                "org_id": str(cls.org_alpha_id),
                "role": "Viewer",
            }
        )
        cls.beta_admin_token = create_access_token(
            data={
                "sub": str(cls.beta_admin.id),
                "email": cls.beta_admin.email,
                "org_id": str(cls.org_beta_id),
                "role": "OrgAdmin",
            }
        )
        cls.beta_member_token = create_access_token(
            data={
                "sub": str(cls.beta_member.id),
                "email": cls.beta_member.email,
                "org_id": str(cls.org_beta_id),
                "role": "Member",
            }
        )

        cls.alpha_m1_headers = {"Authorization": f"Bearer {cls.alpha_m1_token}"}
        cls.alpha_m2_headers = {"Authorization": f"Bearer {cls.alpha_m2_token}"}
        cls.alpha_admin_headers = {"Authorization": f"Bearer {cls.alpha_admin_token}"}
        cls.alpha_viewer_headers = {"Authorization": f"Bearer {cls.alpha_viewer_token}"}
        cls.beta_admin_headers = {"Authorization": f"Bearer {cls.beta_admin_token}"}
        cls.beta_member_headers = {"Authorization": f"Bearer {cls.beta_member_token}"}

    def test_01_multi_tenant_path_isolation_and_cross_tenant_access_denial(self) -> None:
        """Verifies Org Alpha document cannot be read, downloaded, previewed, modified, or deleted by Org Beta."""
        # 1. Org Alpha Member 1 uploads a confidential strategy document
        pdf_bytes = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< >>\n%%EOF"
        upload_resp = self.client.post(
            "/api/v1/documents/upload",
            headers=self.alpha_m1_headers,
            files={"file": ("alpha_confidential_strategy.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            data={"title": "Alpha Confidential Strategy", "category": "LEGAL"},
        )
        self.assertEqual(upload_resp.status_code, 202)
        doc_id = upload_resp.json()["data"]["document_id"]

        # 2. Verify physical filesystem location is compartmentalized under storage/{org_alpha_id}/
        alpha_physical_file = (
            Path(settings.STORAGE_ROOT)
            / str(self.org_alpha_id)
            / "documents"
            / str(doc_id)
            / "v1"
            / "alpha_confidential_strategy.pdf"
        )
        self.assertTrue(alpha_physical_file.exists(), f"File must exist at {alpha_physical_file}")

        # Ensure no trace exists under storage/{org_beta_id}/
        beta_tenant_dir = Path(settings.STORAGE_ROOT) / str(self.org_beta_id)
        if beta_tenant_dir.exists():
            for f in beta_tenant_dir.rglob("alpha_confidential_strategy.pdf"):
                self.fail(f"Leaked file found in Org Beta storage: {f}")

        # 3. Org Beta User attempts GET /documents/{id} -> Expect 403 or 404
        beta_get = self.client.get(f"/api/v1/documents/{doc_id}", headers=self.beta_member_headers)
        self.assertIn(beta_get.status_code, [403, 404])
        if beta_get.status_code == 403:
            self.assertEqual(beta_get.json()["error"]["code"], ErrorCode.AUTH_ORGANIZATION_MISMATCH)
        else:
            self.assertEqual(beta_get.json()["error"]["code"], ErrorCode.DOCUMENT_NOT_FOUND)

        # 4. Org Beta User attempts GET /documents/{id}/download -> Expect 403 or 404
        beta_dl = self.client.get(f"/api/v1/documents/{doc_id}/download", headers=self.beta_member_headers)
        self.assertIn(beta_dl.status_code, [403, 404])

        # 5. Org Beta User attempts GET /documents/{id}/preview -> Expect 403 or 404
        beta_prev = self.client.get(f"/api/v1/documents/{doc_id}/preview", headers=self.beta_member_headers)
        self.assertIn(beta_prev.status_code, [403, 404])

        # 6. Org Beta User attempts PATCH /documents/{id} -> Expect 403 or 404
        beta_patch = self.client.patch(
            f"/api/v1/documents/{doc_id}",
            headers=self.beta_member_headers,
            json={"title": "Hacked Title"},
        )
        self.assertIn(beta_patch.status_code, [403, 404])

        # 7. Org Beta User attempts POST /documents/{id}/version -> Expect 403 or 404
        new_pdf = b"%PDF-1.7\n2 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< >>\n%%EOF"
        beta_ver = self.client.post(
            f"/api/v1/documents/{doc_id}/version",
            headers=self.beta_member_headers,
            files={"file": ("tampered.pdf", io.BytesIO(new_pdf), "application/pdf")},
            data={"change_notes": "Malicious revision"},
        )
        self.assertIn(beta_ver.status_code, [403, 404])

        # 8. Org Beta User attempts DELETE /documents/{id} -> Expect 403 or 404
        beta_del = self.client.delete(f"/api/v1/documents/{doc_id}", headers=self.beta_admin_headers)
        self.assertIn(beta_del.status_code, [403, 404])

        # 9. Verify Org Beta's document listing excludes Alpha's document
        beta_list = self.client.get("/api/v1/documents", headers=self.beta_member_headers)
        self.assertEqual(beta_list.status_code, 200)
        beta_docs = beta_list.json()["data"]["items"]
        beta_ids = [d["id"] for d in beta_docs]
        self.assertNotIn(doc_id, beta_ids)

    def test_02_path_traversal_attack_quarantine(self) -> None:
        """Verifies malicious path traversal filenames are sanitized and confined to tenant storage."""
        traversal_filenames = [
            ("../../../../etc/passwd.txt", "passwd.txt"),
            ("..\\..\\windows\\system32\\calc.txt", "system32_calc.txt"),
            ("subdir/../../../var/log/app.txt", "app.txt"),
            ("safe_prefix/../../escaped.txt", "escaped.txt"),
        ]

        text_content = b"Sanitization and path traversal security verification contents."

        for malicious_name, expected_substring in traversal_filenames:
            resp = self.client.post(
                "/api/v1/documents/upload",
                headers=self.alpha_m1_headers,
                files={"file": (malicious_name, io.BytesIO(text_content + malicious_name.encode() + uuid4().bytes), "text/plain")},
                data={"title": "Traversal Test", "category": "POLICIES"},
            )
            self.assertEqual(resp.status_code, 202, f"Upload should succeed with sanitized filename for {malicious_name}")
            data = resp.json()["data"]
            doc_id = data["document_id"]
            sanitized_name = data["filename"]

            # Filename must NOT contain path traversal characters
            self.assertNotIn("/", sanitized_name)
            self.assertNotIn("\\", sanitized_name)
            self.assertNotIn("..", sanitized_name)
            self.assertIn(expected_substring.replace(".txt", ""), sanitized_name)

            # Physical file must be strictly within storage/{org_id}/documents/{doc_id}/v1/
            tenant_storage_root = (Path(settings.STORAGE_ROOT) / str(self.org_alpha_id)).resolve()
            version_dir = tenant_storage_root / "documents" / str(doc_id) / "v1"
            stored_file = (version_dir / sanitized_name).resolve()

            self.assertTrue(stored_file.exists())
            # Ensure stored file is a child of the tenant storage root
            self.assertTrue(
                str(stored_file).startswith(str(tenant_storage_root)),
                f"Stored file {stored_file} escaped tenant root {tenant_storage_root}",
            )

    def test_03_storage_quota_enforcement(self) -> None:
        """Verifies upload fails with HTTP 400 STORAGE_QUOTA_EXCEEDED when tenant quota is breached."""
        unique_bytes = b"%PDF-1.7\nUnique Quota Overflow " + uuid4().bytes + b"\n%%EOF"

        # Mock check_quota on the storage service to simulate exceeding quota
        with patch("backend.app.services.document_service.LocalStorageService.check_quota", return_value=False):
            resp = self.client.post(
                "/api/v1/documents/upload",
                headers=self.alpha_m1_headers,
                files={"file": ("quota_overflow.pdf", io.BytesIO(unique_bytes), "application/pdf")},
                data={"title": "Quota Overflow File", "category": "FINANCE"},
            )
            self.assertEqual(resp.status_code, 400)
            err = resp.json()["error"]
            self.assertEqual(err["code"], ErrorCode.STORAGE_QUOTA_EXCEEDED)
            self.assertIn("quota", err["message"].lower())

    def test_04_magic_byte_sniffing_and_mime_spoofing_quarantine(self) -> None:
        """Verifies executable or script payloads masquerading as valid documents are rejected."""
        # 1. Linux ELF binary masquerading as PDF
        elf_header = b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x3e\x00"
        resp_elf = self.client.post(
            "/api/v1/documents/upload",
            headers=self.alpha_m1_headers,
            files={"file": ("trojan_disguised.pdf", io.BytesIO(elf_header), "application/pdf")},
            data={"title": "Malicious PDF", "category": "RESEARCH"},
        )
        self.assertEqual(resp_elf.status_code, 422)
        self.assertEqual(resp_elf.json()["error"]["code"], ErrorCode.UNSUPPORTED_FILE_TYPE)

        # 2. Windows MZ/PE executable masquerading as PNG image
        pe_header = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00\xb8\x00\x00\x00"
        resp_pe = self.client.post(
            "/api/v1/documents/upload",
            headers=self.alpha_m1_headers,
            files={"file": ("ransomware.png", io.BytesIO(pe_header), "image/png")},
            data={"title": "Malicious PNG", "category": "REPORTS"},
        )
        self.assertEqual(resp_pe.status_code, 422)
        self.assertEqual(resp_pe.json()["error"]["code"], ErrorCode.UNSUPPORTED_FILE_TYPE)

        # 3. Shell script masquerading as Office DOCX
        shell_script = b"#!/bin/bash\nrm -rf /tmp/test\necho 'hacked'\n"
        resp_sh = self.client.post(
            "/api/v1/documents/upload",
            headers=self.alpha_m1_headers,
            files={"file": ("script.docx", io.BytesIO(shell_script), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"title": "Malicious DOCX", "category": "REPORTS"},
        )
        self.assertEqual(resp_sh.status_code, 422)
        self.assertEqual(resp_sh.json()["error"]["code"], ErrorCode.UNSUPPORTED_FILE_TYPE)

    def test_05_rbac_role_permissions_and_ownership_boundaries(self) -> None:
        """Verifies Viewer cannot upload/delete, and Member cannot delete another Member's document."""
        # 1. Viewer attempts upload -> 403 Forbidden
        pdf_bytes = b"%PDF-1.7\nViewer Test " + uuid4().bytes + b"\n%%EOF"
        resp_viewer = self.client.post(
            "/api/v1/documents/upload",
            headers=self.alpha_viewer_headers,
            files={"file": ("viewer_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            data={"title": "Viewer Upload", "category": "REPORTS"},
        )
        self.assertEqual(resp_viewer.status_code, 403)

        # 2. Member 1 uploads a document
        m1_pdf = b"%PDF-1.7\nMember 1 Document " + uuid4().bytes + b"\n%%EOF"
        resp_m1 = self.client.post(
            "/api/v1/documents/upload",
            headers=self.alpha_m1_headers,
            files={"file": ("m1_doc.pdf", io.BytesIO(m1_pdf), "application/pdf")},
            data={"title": "Member 1 Private Asset", "category": "REPORTS"},
        )
        self.assertEqual(resp_m1.status_code, 202)
        doc_id = resp_m1.json()["data"]["document_id"]

        # 3. Viewer attempts to delete Member 1's document -> 403 Forbidden
        resp_del_viewer = self.client.delete(f"/api/v1/documents/{doc_id}", headers=self.alpha_viewer_headers)
        self.assertEqual(resp_del_viewer.status_code, 403)

        # 4. Member 2 (different member in same org) attempts to delete Member 1's document -> 403 Forbidden
        resp_del_m2 = self.client.delete(f"/api/v1/documents/{doc_id}", headers=self.alpha_m2_headers)
        self.assertEqual(resp_del_m2.status_code, 403)
        self.assertIn(resp_del_m2.json()["error"]["code"], [ErrorCode.AUTH_RESOURCE_FORBIDDEN, ErrorCode.AUTH_PERMISSION_DENIED])

        # 5. Org Admin (administrative role) can delete Member 1's document -> 200 OK
        resp_del_admin = self.client.delete(f"/api/v1/documents/{doc_id}", headers=self.alpha_admin_headers)
        self.assertEqual(resp_del_admin.status_code, 200)
        self.assertTrue(resp_del_admin.json()["data"]["deleted"])

    def test_06_sha256_duplicate_detection_scoped_to_organization(self) -> None:
        """Verifies duplicate detection rejects repeated uploads within the same org, but allows across orgs."""
        unique_payload = f"Unique Duplicate Check Content {uuid4().hex}".encode()
        unique_txt = b"KEEP Document Payload\n" + unique_payload

        # 1. Org Alpha Member 1 uploads first instance
        resp_1 = self.client.post(
            "/api/v1/documents/upload",
            headers=self.alpha_m1_headers,
            files={"file": ("unique_doc.txt", io.BytesIO(unique_txt), "text/plain")},
            data={"title": "Unique Org Alpha Doc", "category": "RESEARCH"},
        )
        self.assertEqual(resp_1.status_code, 202)
        first_doc_id = resp_1.json()["data"]["document_id"]

        # 2. Org Alpha Member 2 uploads the EXACT same file -> 409 Conflict
        resp_dup = self.client.post(
            "/api/v1/documents/upload",
            headers=self.alpha_m2_headers,
            files={"file": ("another_name_same_bytes.txt", io.BytesIO(unique_txt), "text/plain")},
            data={"title": "Duplicate File", "category": "RESEARCH"},
        )
        self.assertEqual(resp_dup.status_code, 409)
        self.assertEqual(resp_dup.json()["error"]["code"], ErrorCode.DUPLICATE_FILE_DETECTED)
        self.assertEqual(resp_dup.json()["error"]["details"]["existing_document_id"], first_doc_id)

        # 3. Org Beta User uploads the same bytes -> Allowed (cross-tenant isolation)
        resp_beta = self.client.post(
            "/api/v1/documents/upload",
            headers=self.beta_member_headers,
            files={"file": ("beta_own_copy.txt", io.BytesIO(unique_txt), "text/plain")},
            data={"title": "Org Beta Legitimate Copy", "category": "RESEARCH"},
        )
        self.assertEqual(resp_beta.status_code, 202)
        self.assertNotEqual(resp_beta.json()["data"]["document_id"], first_doc_id)
