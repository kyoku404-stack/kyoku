"""Integration Tests for RAG & Semantic Search REST API Endpoints (Phase 2.2).

Verifies all 5 RAG endpoints defined in docs/api/api-contract.md Section 9:
1. POST /api/v1/rag/query            (Grounded Q&A with hybrid search & citations)
2. GET  /api/v1/rag/history          (Multi-turn conversational history)
3. GET  /api/v1/rag/citations/{id}   (Deep citation provenance lookup)
4. POST /api/v1/rag/feedback         (User satisfaction evaluation recording)
5. GET  /api/v1/rag/statistics       (Tenant-level operational RAG analytics)

Specification: devdocs/p2/p2.2.txt Chapters 1-20 & docs/api/api-contract.md Section 9
Owner: Member 2 (Backend Lead)
"""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.document import Document
from backend.app.models.document_version import DocumentVersion
from backend.app.models.knowledge import DocumentChunk
from backend.app.models.organization import Organization
from backend.app.models.rag import RAGQuery
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestRAGEndpointsIntegration(unittest.TestCase):
    """Integration test suite for Phase 2.2 RAG REST APIs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            # 1. Tenant organization
            cls.org = Organization(
                name="RAG Test Org",
                domain=f"rag-{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            # 2. Test user
            cls.user = User(
                email=f"rag-user-{uuid4().hex[:6]}@ragtest.com",
                hashed_password=get_password_hash("RAGPass123!"),
                full_name="RAG Test User",
                organization_id=cls.org_id,
                role="Member",
            )
            session.add(cls.user)
            session.commit()
            session.refresh(cls.user)
            cls.user_id = cls.user.id
            cls.user_email = cls.user.email

            # 3. Document
            cls.doc = Document(
                id=uuid4(),
                organization_id=cls.org_id,
                uploader_id=cls.user_id,
                filename="leave_policy.pdf",
                original_filename="leave_policy.pdf",
                title="Employee Leave Policy Handbook",
                file_path="/tmp/leave_policy.pdf",
                file_type="pdf",
                mime_type="application/pdf",
                file_size=1024,
                status="READY_FOR_AI",
            )
            session.add(cls.doc)
            session.commit()
            session.refresh(cls.doc)

            # 4. Document Version
            cls.doc_version = DocumentVersion(
                id=uuid4(),
                document_id=cls.doc.id,
                version_number=1,
                file_path="/tmp/leave_policy.pdf",
                file_size=1024,
                checksum_sha256="rag-checksum-hash-1",
                mime_type="application/pdf",
                uploader_id=cls.user_id,
            )
            session.add(cls.doc_version)
            session.commit()
            session.refresh(cls.doc_version)

            cls.doc.current_version_id = cls.doc_version.id

            # 5. Document Chunk with content & embedding
            cls.chunk = DocumentChunk(
                id=uuid4(),
                document_id=cls.doc.id,
                document_version_id=cls.doc_version.id,
                chunk_index=0,
                content="All full-time employees are entitled to 20 days of paid annual leave per calendar year.",
                embedding=[0.05] * 1536,
                metadata_json={
                    "page_number": 4,
                    "section_title": "Section 4.1: Annual Leave",
                    "checksum_sha256": "chunk-sha-123",
                },
            )
            session.add(cls.chunk)
            session.commit()
            session.refresh(cls.chunk)
            cls.chunk_id = cls.chunk.id

        # Generate JWT Token
        cls.token = create_access_token(
            {
                "sub": str(cls.user_id),
                "email": cls.user_email,
                "org_id": str(cls.org_id),
                "role": "Member",
            }
        )
        cls.auth_headers = {"Authorization": f"Bearer {cls.token}"}

    def test_01_rag_query_grounded_success(self):
        """Tests that natural language queries retrieve relevant chunks and return grounded answers."""
        payload = {
            "query": "What is our annual leave entitlement?",
            "top_k": 3,
            "hybrid_dense_weight": 0.65,
            "hybrid_sparse_weight": 0.35,
        }
        response = self.client.post("/api/v1/rag/query", json=payload, headers=self.auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        data = body["data"]
        assert data["query"] == payload["query"]
        assert data["is_grounded"] is True
        assert data["confidence_score"] > 0.0
        assert len(data["citations"]) > 0
        assert data["citations"][0]["document_title"] == "Employee Leave Policy Handbook"
        assert data["citations"][0]["page_number"] == 4

    def test_02_rag_query_circuit_breaker_ungrounded(self):
        """Tests that out-of-domain queries trigger the zero-hallucination circuit breaker."""
        payload = {
            "query": "How do I bake an authentic Neapolitan pizza?",
            "top_k": 3,
        }
        response = self.client.post("/api/v1/rag/query", json=payload, headers=self.auth_headers)
        assert response.status_code == 200
        body = response.json()
        data = body["data"]
        assert data["is_grounded"] is False
        assert "could not find sufficient authoritative information" in data["answer"]
        assert len(data["citations"]) == 0

    def test_03_rag_query_multi_turn_session_tracking(self):
        """Tests that conversational multi-turn sessions are recorded in ChatSession and ChatMessage."""
        session_id = str(uuid4())
        payload = {
            "query": "Who approves my leave request?",
            "session_id": session_id,
        }
        response = self.client.post("/api/v1/rag/query", json=payload, headers=self.auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["session_id"] == session_id

        # Verify history endpoint retrieves the session
        hist_resp = self.client.get(
            f"/api/v1/rag/history?session_id={session_id}",
            headers=self.auth_headers,
        )
        assert hist_resp.status_code == 200
        hist_data = hist_resp.json()["data"]
        assert hist_data["total"] >= 1
        assert len(hist_data["sessions"]) >= 1
        sess = hist_data["sessions"][0]
        assert sess["session_id"] == session_id
        assert sess["message_count"] == 2  # user + assistant

    def test_04_rag_citation_detail_lookup(self):
        """Tests inspecting source metadata and full chunk content by chunk ID."""
        response = self.client.get(
            f"/api/v1/rag/citations/{self.chunk_id}",
            headers=self.auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        data = body["data"]
        assert data["chunk_id"] == str(self.chunk_id)
        assert data["document_title"] == "Employee Leave Policy Handbook"
        assert data["page_number"] == 4
        assert "20 days of paid annual leave" in data["full_content"]

    def test_05_rag_citation_detail_not_found(self):
        """Tests 404 response for nonexistent citation ID."""
        fake_id = str(uuid4())
        response = self.client.get(
            f"/api/v1/rag/citations/{fake_id}",
            headers=self.auth_headers,
        )
        assert response.status_code == 404
        assert response.json()["success"] is False

    def test_06_rag_feedback_submission(self):
        """Tests submitting user evaluation and rating on a query."""
        # First create a query in DB to reference
        with Session(sync_test_engine, expire_on_commit=False) as session:
            q = RAGQuery(
                id=uuid4(),
                organization_id=self.org_id,
                user_id=self.user_id,
                query_text="What is leave?",
                response_text="20 days leave [Source 1]",
                confidence_score=0.9,
                is_grounded=True,
            )
            session.add(q)
            session.commit()
            session.refresh(q)
            query_id = q.id

        payload = {
            "query_id": str(query_id),
            "rating": 5,
            "is_helpful": True,
            "comment": "Accurate and fast response!",
        }
        response = self.client.post("/api/v1/rag/feedback", json=payload, headers=self.auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "feedback_id" in body["data"]

    def test_07_rag_statistics_reporting(self):
        """Tests retrieving aggregate organizational RAG metrics."""
        response = self.client.get("/api/v1/rag/statistics", headers=self.auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        data = body["data"]
        assert data["organization_id"] == str(self.org_id)
        assert data["total_queries"] >= 1
        assert "average_latency_ms" in data
        assert "positive_feedback_percentage" in data
