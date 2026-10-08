"""Unit tests for AI and RAG Persistence & Data Layer Contracts (Phase 1.3).

Verifies vector store records, filters, chunk repositories, knowledge graph triples,
chat history sessions, messages, and AI audit log models.
"""

import unittest
from uuid import uuid4

from backend.app.services.rag.interfaces import (
    AIQueryLogRecord,
    BaseAIQueryLogRepository,
    BaseChatHistoryRepository,
    BaseChunkRepository,
    BaseKnowledgeGraphStore,
    BaseVectorStore,
    ChatMessageRecord,
    ChatSessionRecord,
    CitationMetadata,
    DocumentChunkRecord,
    KGEntityRecord,
    KGRelationshipRecord,
    RetrievalResult,
    VectorFilter,
    VectorRecord,
)


class MockVectorStore(BaseVectorStore):
    """Mock implementation of BaseVectorStore for contract verification."""

    def __init__(self):
        self.store: dict[str, VectorRecord] = {}

    async def upsert_vectors(self, vectors: list[VectorRecord]) -> int:
        for v in vectors:
            self.store[str(v.id)] = v
        return len(vectors)

    async def similarity_search(
        self,
        query_vector: list[float],
        top_k: int,
        filter_criteria: VectorFilter,
    ) -> list[RetrievalResult]:
        results = []
        for v in self.store.values():
            if v.organization_id == filter_criteria.organization_id:
                results.append(
                    RetrievalResult(
                        chunk_id=v.id,
                        document_id=v.document_id or uuid4(),
                        content=v.payload.get("content", ""),
                        score=0.95,
                    )
                )
        return results[:top_k]

    async def delete_vectors(self, vector_ids: list, organization_id) -> int:
        deleted = 0
        for vid in vector_ids:
            key = str(vid)
            if key in self.store and self.store[key].organization_id == organization_id:
                del self.store[key]
                deleted += 1
        return deleted

    async def delete_vectors_by_document(self, document_id, organization_id) -> int:
        keys_to_delete = [
            k
            for k, v in self.store.items()
            if v.document_id == document_id and v.organization_id == organization_id
        ]
        for k in keys_to_delete:
            del self.store[k]
        return len(keys_to_delete)


class MockChunkRepository(BaseChunkRepository):
    """Mock implementation of BaseChunkRepository for contract verification."""

    def __init__(self):
        self.chunks: dict[str, DocumentChunkRecord] = {}

    async def create_chunks(
        self,
        chunks: list[DocumentChunkRecord],
    ) -> list[DocumentChunkRecord]:
        for c in chunks:
            self.chunks[str(c.id)] = c
        return chunks

    async def get_chunks_by_document(
        self,
        document_id,
        organization_id,
    ) -> list[DocumentChunkRecord]:
        return [
            c
            for c in self.chunks.values()
            if c.document_id == document_id and c.organization_id == organization_id
        ]

    async def get_chunk_by_id(
        self,
        chunk_id,
        organization_id,
    ) -> DocumentChunkRecord | None:
        chunk = self.chunks.get(str(chunk_id))
        if chunk and chunk.organization_id == organization_id:
            return chunk
        return None

    async def delete_chunks_by_document(
        self,
        document_id,
        organization_id,
    ) -> int:
        keys = [
            k
            for k, v in self.chunks.items()
            if v.document_id == document_id and v.organization_id == organization_id
        ]
        for k in keys:
            del self.chunks[k]
        return len(keys)


class MockKGStore(BaseKnowledgeGraphStore):
    """Mock implementation of BaseKnowledgeGraphStore for contract verification."""

    def __init__(self):
        self.entities: dict[str, KGEntityRecord] = {}
        self.relationships: dict[str, KGRelationshipRecord] = {}

    async def upsert_entity(self, entity: KGEntityRecord) -> KGEntityRecord:
        self.entities[str(entity.id)] = entity
        return entity

    async def upsert_relationship(
        self,
        relationship: KGRelationshipRecord,
    ) -> KGRelationshipRecord:
        self.relationships[str(relationship.id)] = relationship
        return relationship

    async def get_entity_neighbors(
        self,
        entity_id,
        organization_id,
        max_depth: int = 1,
    ) -> dict:
        outgoing = [
            r
            for r in self.relationships.values()
            if r.source_entity_id == entity_id and r.organization_id == organization_id
        ]
        return {"entity_id": entity_id, "depth": max_depth, "edges": outgoing}

    async def find_entity_by_name(
        self,
        name: str,
        entity_type: str,
        organization_id,
    ) -> KGEntityRecord | None:
        for e in self.entities.values():
            if (
                e.name == name
                and e.entity_type == entity_type
                and e.organization_id == organization_id
            ):
                return e
        return None


class MockChatHistoryRepository(BaseChatHistoryRepository):
    """Mock implementation of BaseChatHistoryRepository for contract verification."""

    def __init__(self):
        self.sessions: dict[str, ChatSessionRecord] = {}
        self.messages: dict[str, list[ChatMessageRecord]] = {}

    async def create_session(self, session: ChatSessionRecord) -> ChatSessionRecord:
        self.sessions[str(session.id)] = session
        self.messages[str(session.id)] = []
        return session

    async def get_session(self, session_id, organization_id) -> ChatSessionRecord | None:
        sess = self.sessions.get(str(session_id))
        if sess and sess.organization_id == organization_id:
            return sess
        return None

    async def list_user_sessions(
        self, user_id, organization_id, limit: int = 50
    ) -> list[ChatSessionRecord]:
        return [
            s
            for s in self.sessions.values()
            if s.user_id == user_id and s.organization_id == organization_id
        ][:limit]

    async def add_message(self, message: ChatMessageRecord) -> ChatMessageRecord:
        sess_key = str(message.session_id)
        if sess_key in self.messages:
            self.messages[sess_key].append(message)
        return message

    async def get_session_messages(
        self, session_id, limit: int = 100
    ) -> list[ChatMessageRecord]:
        return self.messages.get(str(session_id), [])[:limit]

    async def delete_session(self, session_id, organization_id) -> bool:
        sess = await self.get_session(session_id, organization_id)
        if sess:
            sess.is_archived = True
            return True
        return False


class MockAIQueryLogRepository(BaseAIQueryLogRepository):
    """Mock implementation of BaseAIQueryLogRepository for contract verification."""

    def __init__(self):
        self.logs: list[AIQueryLogRecord] = []

    async def log_query(self, log_entry: AIQueryLogRecord) -> None:
        self.logs.append(log_entry)

    async def get_organization_usage(self, organization_id) -> dict:
        org_logs = [entry for entry in self.logs if entry.organization_id == organization_id]
        total_tokens = sum(entry.tokens_used for entry in org_logs)
        return {
            "organization_id": organization_id,
            "query_count": len(org_logs),
            "total_tokens": total_tokens,
        }


class TestAIPersistenceContracts(unittest.IsolatedAsyncioTestCase):
    """Test suite asserting all AI persistence contracts and abstract repos."""

    async def test_vector_record_and_store_contract(self):
        org_id = uuid4()
        doc_id = uuid4()
        vec_id = uuid4()

        vec = VectorRecord(
            id=vec_id,
            vector=[0.1, 0.2, 0.3, 0.4],
            payload={"content": "sample content"},
            organization_id=org_id,
            document_id=doc_id,
        )
        self.assertEqual(vec.id, vec_id)
        self.assertEqual(vec.organization_id, org_id)
        self.assertEqual(len(vec.vector), 4)

        store = MockVectorStore()
        upsert_count = await store.upsert_vectors([vec])
        self.assertEqual(upsert_count, 1)

        filt = VectorFilter(organization_id=org_id, document_id=doc_id)
        search_res = await store.similarity_search([0.1, 0.2, 0.3, 0.4], top_k=5, filter_criteria=filt)
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0].chunk_id, vec_id)

        del_count = await store.delete_vectors_by_document(doc_id, org_id)
        self.assertEqual(del_count, 1)

    async def test_chunk_repository_contract(self):
        org_id = uuid4()
        doc_id = uuid4()
        chunk_id = uuid4()

        chunk = DocumentChunkRecord(
            id=chunk_id,
            organization_id=org_id,
            document_id=doc_id,
            chunk_index=0,
            content="Enterprise compliance guidelines.",
            token_count=12,
            page_number=1,
            section_title="Overview",
            embedding=[0.5, 0.6],
            metadata={"source": "manual"},
        )
        repo = MockChunkRepository()
        await repo.create_chunks([chunk])

        retrieved = await repo.get_chunk_by_id(chunk_id, org_id)
        assert retrieved is not None
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.chunk_index, 0)
        self.assertEqual(retrieved.section_title, "Overview")

        all_doc_chunks = await repo.get_chunks_by_document(doc_id, org_id)
        self.assertEqual(len(all_doc_chunks), 1)

    async def test_knowledge_graph_store_contract(self):
        org_id = uuid4()
        entity_a = KGEntityRecord(
            id=uuid4(),
            organization_id=org_id,
            name="Alpha Project",
            entity_type="Project",
            description="Core enterprise initiative",
            properties={"priority": "High"},
        )
        entity_b = KGEntityRecord(
            id=uuid4(),
            organization_id=org_id,
            name="Jane Doe",
            entity_type="Person",
            properties={"department": "Engineering"},
        )
        rel = KGRelationshipRecord(
            id=uuid4(),
            organization_id=org_id,
            source_entity_id=entity_b.id,
            target_entity_id=entity_a.id,
            relation_type="ASSIGNED_TO",
            weight=1.0,
            confidence_score=0.98,
        )

        kg_store = MockKGStore()
        await kg_store.upsert_entity(entity_a)
        await kg_store.upsert_entity(entity_b)
        await kg_store.upsert_relationship(rel)

        found = await kg_store.find_entity_by_name("Alpha Project", "Project", org_id)
        assert found is not None
        self.assertIsNotNone(found)
        self.assertEqual(found.id, entity_a.id)

        neighbors = await kg_store.get_entity_neighbors(entity_b.id, org_id)
        self.assertEqual(len(neighbors["edges"]), 1)
        self.assertEqual(neighbors["edges"][0].relation_type, "ASSIGNED_TO")

    async def test_chat_history_repository_contract(self):
        org_id = uuid4()
        user_id = uuid4()
        session_id = uuid4()

        session = ChatSessionRecord(
            id=session_id,
            organization_id=org_id,
            user_id=user_id,
            title="Q3 Strategy Discussion",
        )
        repo = MockChatHistoryRepository()
        await repo.create_session(session)

        user_sessions = await repo.list_user_sessions(user_id, org_id)
        self.assertEqual(len(user_sessions), 1)
        self.assertEqual(user_sessions[0].title, "Q3 Strategy Discussion")

        msg = ChatMessageRecord(
            id=uuid4(),
            session_id=session_id,
            role="assistant",
            content="Strategic goals are outlined in Document 1.",
            citations=[
                CitationMetadata(
                    document_id=uuid4(),
                    filename="Strategy.pdf",
                    page_number=2,
                    relevance_score=0.95,
                )
            ],
            latency_ms=210.0,
        )
        await repo.add_message(msg)

        messages = await repo.get_session_messages(session_id)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].role, "assistant")
        self.assertEqual(len(messages[0].citations), 1)

    async def test_ai_query_log_repository_contract(self):
        org_id = uuid4()
        user_id = uuid4()

        entry = AIQueryLogRecord(
            id=uuid4(),
            organization_id=org_id,
            user_id=user_id,
            query="Summarize project timeline",
            response="Milestone 1 completed...",
            tokens_used=150,
            latency_ms=320.0,
            model_name="gpt-4o",
            citations_count=2,
        )

        repo = MockAIQueryLogRepository()
        await repo.log_query(entry)

        usage = await repo.get_organization_usage(org_id)
        self.assertEqual(usage["query_count"], 1)
        self.assertEqual(usage["total_tokens"], 150)


if __name__ == "__main__":
    unittest.main()
