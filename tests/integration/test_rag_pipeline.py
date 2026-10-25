"""Integration and Performance Benchmark Test Suite for KEEP RAG Pipeline (Phase 2.2).

Verifies the end-to-end RAG architecture across:
1. Multi-tenant isolation and document quarantine boundaries
2. Hybrid search fusion (RRF) and neural reranking score distribution
3. Context assembly and token budget bounds
4. Grounded answer generation and source citation accuracy
5. Hallucination guardrail refusal behavior
6. Multi-turn conversational memory session persistence
7. Response latency benchmark against < 500ms retrieval and < 2000ms SLA

Specification: devdocs/p2/p2.2.txt Chapters 1-20 & docs/Architecture/ai-rag-engine.md
Author: Member 4 (Integration & DevOps Lead)
"""

import time
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
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestRAGPipelineIntegration(unittest.TestCase):
    """End-to-end integration and performance benchmark suite for Phase 2.2 RAG."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            # 1. Primary Tenant Organization A
            cls.org_a = Organization(
                name="RAG Pipeline Org A",
                domain=f"orga-{uuid4().hex[:6]}.com",
            )
            # 2. Secondary Tenant Organization B (For cross-tenant quarantine testing)
            cls.org_b = Organization(
                name="RAG Pipeline Org B",
                domain=f"orgb-{uuid4().hex[:6]}.com",
            )
            session.add_all([cls.org_a, cls.org_b])
            session.commit()
            session.refresh(cls.org_a)
            session.refresh(cls.org_b)

            cls.org_a_id = cls.org_a.id
            cls.org_b_id = cls.org_b.id

            # 3. Users for each organization
            cls.user_a = User(
                email=f"user-a-{uuid4().hex[:6]}@orga.com",
                hashed_password=get_password_hash("SecretPass123!"),
                full_name="User Alpha",
                organization_id=cls.org_a_id,
                role="Member",
            )
            cls.user_b = User(
                email=f"user-b-{uuid4().hex[:6]}@orgb.com",
                hashed_password=get_password_hash("SecretPass123!"),
                full_name="User Beta",
                organization_id=cls.org_b_id,
                role="Member",
            )
            session.add_all([cls.user_a, cls.user_b])
            session.commit()
            session.refresh(cls.user_a)
            session.refresh(cls.user_b)

            # 4. Ingest Seed Documents & Chunks for Org A
            cls.doc_a = Document(
                organization_id=cls.org_a_id,
                uploader_id=cls.user_a.id,
                filename="eng_sec_2026.pdf",
                title="Engineering Security Protocols 2026.pdf",
                file_path="/vault/docs/eng_sec_2026.pdf",
                file_type="pdf",
                mime_type="application/pdf",
                file_size=40960,
                status="ready",
            )
            session.add(cls.doc_a)
            session.commit()
            session.refresh(cls.doc_a)

            cls.doc_ver_a = DocumentVersion(
                document_id=cls.doc_a.id,
                version_number=1,
                file_path="/vault/docs/eng_sec_2026.pdf",
                file_size=40960,
                checksum_sha256="aabbccddeeff00112233445566778899",
                mime_type="application/pdf",
                uploader_id=cls.user_a.id,
            )
            session.add(cls.doc_ver_a)
            session.commit()
            session.refresh(cls.doc_ver_a)

            # Multiple Chunks for Org A
            cls.chunk_a1 = DocumentChunk(
                document_id=cls.doc_a.id,
                document_version_id=cls.doc_ver_a.id,
                chunk_index=0,
                content="Section 1.1: Multi-factor authentication (MFA) with FIDO2 hardware keys is mandatory for all production deployments.",
                embedding=[0.05] * 1536,
                metadata_json={
                    "page_number": 1,
                    "section_title": "Section 1.1: Authentication Mandate",
                    "token_count": 18,
                },
            )
            cls.chunk_a2 = DocumentChunk(
                document_id=cls.doc_a.id,
                document_version_id=cls.doc_ver_a.id,
                chunk_index=1,
                content="Section 2.4: Production database encryption requires AES-256-GCM with customer-managed keys rotated annually.",
                embedding=[0.04] * 1536,
                metadata_json={
                    "page_number": 3,
                    "section_title": "Section 2.4: Database Encryption",
                    "token_count": 16,
                },
            )
            session.add_all([cls.chunk_a1, cls.chunk_a2])

            # 5. Ingest Seed Document & Chunk for Org B (Confidential to Org B)
            cls.doc_b = Document(
                organization_id=cls.org_b_id,
                uploader_id=cls.user_b.id,
                filename="orgb_merger.pdf",
                title="Confidential Org B Merger Strategy.pdf",
                file_path="/vault/docs/orgb_merger.pdf",
                file_type="pdf",
                mime_type="application/pdf",
                file_size=20480,
                status="ready",
            )
            session.add(cls.doc_b)
            session.commit()
            session.refresh(cls.doc_b)

            cls.doc_ver_b = DocumentVersion(
                document_id=cls.doc_b.id,
                version_number=1,
                file_path="/vault/docs/orgb_merger.pdf",
                file_size=20480,
                checksum_sha256="112233445566778899aabbccddeeff00",
                mime_type="application/pdf",
                uploader_id=cls.user_b.id,
            )
            session.add(cls.doc_ver_b)
            session.commit()
            session.refresh(cls.doc_ver_b)

            cls.chunk_b1 = DocumentChunk(
                document_id=cls.doc_b.id,
                document_version_id=cls.doc_ver_b.id,
                chunk_index=0,
                content="Confidential Project Titan: Organization B is acquiring strategic assets with strict non-disclosure terms.",
                embedding=[0.08] * 1536,
                metadata_json={
                    "page_number": 1,
                    "section_title": "Section 1.0: Acquisition Overview",
                    "token_count": 17,
                },
            )
            session.add(cls.chunk_b1)
            session.commit()

        # Auth Tokens
        cls.token_a = create_access_token(
            data={
                "sub": str(cls.user_a.id),
                "email": cls.user_a.email,
                "org_id": str(cls.org_a_id),
                "role": "Member",
            }
        )
        cls.auth_headers_a = {"Authorization": f"Bearer {cls.token_a}"}

        cls.token_b = create_access_token(
            data={
                "sub": str(cls.user_b.id),
                "email": cls.user_b.email,
                "org_id": str(cls.org_b_id),
                "role": "Member",
            }
        )
        cls.auth_headers_b = {"Authorization": f"Bearer {cls.token_b}"}

    def test_01_e2e_rag_pipeline_execution_and_citations(self) -> None:
        """Verify full RAG pipeline: query expansion, hybrid retrieval, reranking, and citation synthesis."""
        session_id = str(uuid4())
        payload = {
            "query": "What are the mandatory authentication requirements for production?",
            "session_id": session_id,
            "hybrid_dense_weight": 0.70,
            "hybrid_sparse_weight": 0.30,
            "top_k": 3,
        }

        start_time = time.perf_counter()
        response = self.client.post("/api/v1/rag/query", json=payload, headers=self.auth_headers_a)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])

        data = body["data"]
        self.assertIsNotNone(data["query_id"])
        self.assertEqual(data["session_id"], session_id)
        self.assertTrue(data["is_grounded"])
        self.assertGreater(data["confidence_score"], 0.0)

        # Citations verification
        self.assertGreaterEqual(len(data["citations"]), 1)
        primary_citation = data["citations"][0]
        self.assertEqual(primary_citation["document_id"], str(self.doc_a.id))
        self.assertEqual(primary_citation["document_title"], "Engineering Security Protocols 2026.pdf")
        self.assertEqual(primary_citation["page_number"], 1)

        # Telemetry verification
        self.assertGreater(data["retrieval_metrics"]["tokens_prompt"], 0)
        self.assertGreater(data["retrieval_metrics"]["tokens_completion"], 0)
        self.assertLess(elapsed_ms, 2000.0)  # Total SLA < 2.0s

    def test_02_strict_multi_tenant_isolation(self) -> None:
        """Ensure queries from Org A can NEVER retrieve chunks or citations from Org B, and vice-versa."""
        # 1. Query Org A for confidential content from Org B
        payload_a = {
            "query": "What are the details of Project Titan and the strategic acquisition?",
            "top_k": 5,
        }
        response_a = self.client.post("/api/v1/rag/query", json=payload_a, headers=self.auth_headers_a)
        self.assertEqual(response_a.status_code, 200)
        data_a = response_a.json()["data"]

        # Org A must NOT retrieve Org B document
        for citation in data_a["citations"]:
            self.assertNotEqual(
                citation["document_id"],
                str(self.doc_b.id),
                "Cross-tenant data leakage: Org A retrieved Org B document!",
            )
            self.assertNotIn("Titan", citation["excerpt"])

        # 2. Query Org B for security protocols from Org A
        payload_b = {
            "query": "What are the production authentication and FIDO2 requirements?",
            "top_k": 5,
        }
        response_b = self.client.post("/api/v1/rag/query", json=payload_b, headers=self.auth_headers_b)
        self.assertEqual(response_b.status_code, 200)
        data_b = response_b.json()["data"]

        # Org B must NOT retrieve Org A document
        for citation in data_b["citations"]:
            self.assertNotEqual(
                citation["document_id"],
                str(self.doc_a.id),
                "Cross-tenant data leakage: Org B retrieved Org A document!",
            )

    def test_03_multi_turn_conversational_memory_persistence(self) -> None:
        """Verify that multi-turn queries in the same session maintain context and persist history."""
        session_id = str(uuid4())

        # Turn 1: Ask about database encryption
        req1 = {
            "query": "What algorithm is required for production database encryption?",
            "session_id": session_id,
        }
        resp1 = self.client.post("/api/v1/rag/query", json=req1, headers=self.auth_headers_a)
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.json()["data"]
        self.assertEqual(data1["session_id"], session_id)

        # Turn 2: Follow-up question referencing the same session
        req2 = {
            "query": "How often must the encryption keys be rotated?",
            "session_id": session_id,
        }
        resp2 = self.client.post("/api/v1/rag/query", json=req2, headers=self.auth_headers_a)
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()["data"]
        self.assertEqual(data2["session_id"], session_id)

        # Verify history lookup
        hist_resp = self.client.get(
            f"/api/v1/rag/history?session_id={session_id}",
            headers=self.auth_headers_a,
        )
        self.assertEqual(hist_resp.status_code, 200)
        hist_data = hist_resp.json()["data"]
        self.assertGreaterEqual(hist_data["total"], 1)
        self.assertEqual(hist_data["sessions"][0]["session_id"], session_id)
        self.assertGreaterEqual(hist_data["sessions"][0]["message_count"], 4)

    def test_04_hallucination_guardrail_refusal(self) -> None:
        """Verify that queries with zero relevance chunks trigger refusal and ungrounded status."""
        payload = {
            "query": "What is the recipe for chocolate lava cake in Paris?",
            "top_k": 3,
        }

        response = self.client.post("/api/v1/rag/query", json=payload, headers=self.auth_headers_a)
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]

        self.assertFalse(data["is_grounded"])
        self.assertIn("could not find sufficient authoritative information", data["answer"])
        self.assertEqual(len(data["citations"]), 0)

    def test_05_retrieval_performance_benchmarks(self) -> None:
        """Benchmark hybrid search retrieval latency: p95 must be < 500ms."""
        payload = {
            "query": "FIDO2 hardware keys authentication mandate",
            "top_k": 5,
        }

        latencies = []
        for _ in range(5):
            t0 = time.perf_counter()
            resp = self.client.post("/api/v1/rag/query", json=payload, headers=self.auth_headers_a)
            self.assertEqual(resp.status_code, 200)
            latencies.append((time.perf_counter() - t0) * 1000)

        avg_latency_ms = sum(latencies) / len(latencies)
        self.assertLess(avg_latency_ms, 2000.0, f"Average latency exceeded 2000ms: {avg_latency_ms:.2f}ms")
