# KEEP — AI Persistence & Database Architecture Specification (docs/Architecture/ai-persistence-architecture.md)

> **Master Persistence, Vector Store & Knowledge Graph Architecture Specification for KEEP**  
> *Approved by: Member 1 (Project Lead & AI Architect)*  
> *Target Implementer: Member 2 (Backend Lead) | Integration: Member 4 (DevOps Lead)*  
> *Specification Reference: devdocs/p1/p1.3.txt (Chapters 1–22)*

---

## 1. Executive Summary & Objective

In accordance with **Phase 1.3 (Database Implementation & Persistence Layer)** of `devdocs/p1/p1.3.txt`, this document establishes the formal persistence architecture, schema validation, vector storage strategy, relational knowledge graph representation, and conversational memory design for the KEEP platform.

The persistence layer serves as the permanent memory of KEEP. It must reliably support:
1. **Multi-Tenant Enterprise Organizations**: Strict tenant isolation across all relational tables, files, vector embeddings, and graph entities.
2. **AI Knowledge Ingestion & Hybrid RAG Engine**: High-throughput storage of documents, chunk hierarchies, embedding vectors (1536-dim / 384-dim), citation provenance, and lexical BM25 search indices.
3. **Enterprise Knowledge Graph**: Semantic entity linking, relationship mapping, multi-hop traversals, and property graphs.
4. **Conversational AI & Decision Support**: Structured chat sessions, message histories, tool calling records, token usage accounting, and human-in-the-loop feedback.
5. **Zero-Trust Auditability & Compliance**: Immutable activity logs, soft deletes, and role-based data boundaries.

---

## 2. Persistence Architecture & Layering Model

KEEP enforces a strict **4-Tier Layered Persistence Architecture** to decouple database mechanics from business logic:

```
+-------------------------------------------------------------------------+
|                         FastAPI Router Layer                            |
|             (HTTP validation, JWT claims, Pydantic DTOs)                |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                         Service / Business Layer                        |
|        (Domain logic, RAG orchestration, AI contexts, Workflows)        |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                        Repository Layer (Abstract)                      |
|       (CRUD, Tenant filters, Pagination, Vector search, KG traversals)  |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                    SQLAlchemy 2.0 ORM & Async Engine                    |
|             (Asyncpg, Connection pooling, Unit of Work, Alembic)        |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                       PostgreSQL 16 + pgvector                          |
|         (Relational tables, HNSW vector indices, GIN JSONB, tsvector)   |
+-------------------------------------------------------------------------+
```

### 2.1 Separation of Concerns Principles
- **No Raw SQL in Routers or Services**: All persistence queries must reside within typed Repository classes (`UserRepository`, `DocumentRepository`, `VectorStore`, `KnowledgeGraphStore`, `ChatRepository`).
- **One Session Per Request**: Database sessions are scoped to individual async request lifespans with automatic rollback on exception and automatic closure upon response completion.
- **Mandatory Tenant Predicates**: Every query executed by a repository must include `WHERE organization_id = :org_id` or join through a tenant-scoped parent entity.

---

## 3. Entity Design Review & Validation for AI Modules

### 3.1 Relational Entity Matrix (Phase 1.3 Core)

The core relational data model consists of the following primary tables:

| Entity Table | Primary Key | Tenant FK | Core Purpose | Future AI Integration Touchpoint |
| :--- | :--- | :--- | :--- | :--- |
| `organizations` | UUID | Self (`id`) | Enterprise multi-tenant root | AI quota limits, default LLM model configs, tenant isolation boundary |
| `users` | UUID | `organization_id` | Authentication, RBAC, profiles | AI query execution context, personal history, user preferences |
| `teams` | UUID | `organization_id` | Departmental / functional teams | Team-scoped knowledge access control and collaborative workspaces |
| `team_members` | Composite | N/A (via Team) | User-to-team memberships | Fine-grained knowledge partition filtering |
| `projects` | UUID | `organization_id` | Enterprise project containers | Project-scoped RAG retrieval, automated project summarization |
| `documents` | UUID | `organization_id` | Uploaded raw file metadata & state | Root container for document chunks, OCR text, and citation targets |
| `meetings` | UUID | `organization_id` | Calendar events & sync recordings | Meeting transcription, action item extraction, automated summaries |
| `tasks` | UUID | `organization_id` | Assigned work items & milestones | AI-suggested task generation from meetings and documents |
| `activity_logs` | UUID | `organization_id` | Security & audit event logging | AI inference audit trail, compliance verification, anomaly detection |

---

## 4. AI & Vector Persistence Specifications (Phase 2 Preparation)

### 4.1 Document Chunks & Vector Embeddings (`document_chunks`)

To support dense semantic retrieval and citation provenance, document text is broken into overlapping semantic chunks and persisted with high-dimensional vector embeddings.

#### Schema Definition:
```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    token_count INT NOT NULL DEFAULT 0,
    page_number INT,
    section_title VARCHAR(255),
    embedding vector(1536), -- Standard OpenAI / text-embedding-3-small (configurable to 384)
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_document_chunk_idx UNIQUE (document_id, chunk_index)
);
```

#### Indexing Strategy:
1. **Hierarchical Navigable Small World (HNSW) Vector Index**:
   ```sql
   CREATE INDEX idx_chunks_embedding_hnsw ON document_chunks 
   USING hnsw (embedding vector_cosine_ops) 
   WITH (m = 16, ef_construction = 64);
   ```
2. **Tenant Filter B-Tree Index**:
   ```sql
   CREATE INDEX idx_chunks_org_doc ON document_chunks (organization_id, document_id);
   ```
3. **Full-Text Lexical Search (tsvector)**:
   ```sql
   ALTER TABLE document_chunks ADD COLUMN tsv_content tsvector 
   GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;
   CREATE INDEX idx_chunks_tsv ON document_chunks USING gin (tsv_content);
   ```

---

## 5. Relational Knowledge Graph Persistence (Phase 2.4 Preparation)

In accordance with ADR-001 and Assumption 001, the MVP Knowledge Graph is persisted directly in PostgreSQL using normalized relational tables with JSONB property bags.

### 5.1 Knowledge Graph Entities (`kg_entities`)
Represents semantic nodes (e.g., Person, Organization, Project, Document, Technology, Policy).

```sql
CREATE TABLE kg_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL, -- 'Person', 'Project', 'Technology', 'Document', 'Department'
    description TEXT,
    source_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    properties JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_kg_entity_org_name_type UNIQUE (organization_id, name, entity_type)
);
```

### 5.2 Knowledge Graph Relationships (`kg_relationships`)
Represents directed semantic edges linking entities (e.g., `AUTHOR_OF`, `ASSIGNED_TO`, `DEPENDS_ON`, `BELONGS_TO`).

```sql
CREATE TABLE kg_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    source_entity_id UUID NOT NULL REFERENCES kg_entities(id) ON DELETE CASCADE,
    target_entity_id UUID NOT NULL REFERENCES kg_entities(id) ON DELETE CASCADE,
    relation_type VARCHAR(100) NOT NULL, -- 'AUTHOR_OF', 'WORKS_ON', 'MENTIONS', 'SUPERVISES'
    weight FLOAT NOT NULL DEFAULT 1.0,
    confidence_score FLOAT NOT NULL DEFAULT 1.0,
    source_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    properties JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

#### Graph Indexing & Traversal Strategy:
- Composite index on `(organization_id, source_entity_id, relation_type)`.
- Composite index on `(organization_id, target_entity_id, relation_type)`.
- Fast multi-hop graph queries executed via PostgreSQL Recursive Common Table Expressions (CTEs).

---

## 6. Conversational Memory & AI Audit Persistence

### 6.1 Chat Sessions & Message History (`chat_sessions` & `chat_messages`)

```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL DEFAULT 'New Conversation',
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- 'user', 'assistant', 'system', 'tool'
    content TEXT NOT NULL,
    model_name VARCHAR(100),
    tokens_prompt INT DEFAULT 0,
    tokens_completion INT DEFAULT 0,
    latency_ms FLOAT DEFAULT 0.0,
    citations_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    tool_calls_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### 6.2 AI Feedback & Quality Metrics (`ai_feedback`)

```sql
CREATE TABLE ai_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    rating INT NOT NULL, -- +1 for thumbs up, -1 for thumbs down
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

---

## 7. Soft Delete & Data Lifecycle Policy

In enterprise environments, accidental deletions must be recoverable, and regulatory retention policies must be upheld.

### 7.1 Soft Delete Implementation (`SoftDeleteMixin`)
All primary business entities (`organizations`, `users`, `projects`, `documents`, `meetings`, `tasks`, `chat_sessions`) inherit a standardized soft-delete pattern:
- `is_deleted`: `BOOLEAN NOT NULL DEFAULT FALSE`
- `deleted_at`: `TIMESTAMP WITH TIME ZONE NULL`

### 7.2 Repository Query Filtering
Repositories automatically include `WHERE is_deleted = FALSE` in standard lookup queries. Dedicated administrative endpoints provide hard-delete and restore capabilities.

---

## 8. Database Indexing Matrix Summary

| Table | Index Name | Type | Columns / Expression | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `idx_users_org_email` | B-tree (Unique) | `organization_id, email` | Fast multi-tenant user authentication |
| `documents` | `idx_documents_org_status` | B-tree | `organization_id, status, created_at` | Ingestion queue & document listing |
| `document_chunks` | `idx_chunks_embedding_hnsw`| HNSW | `embedding (vector_cosine_ops)` | High-performance approximate nearest neighbor search |
| `document_chunks` | `idx_chunks_tsv` | GIN | `tsv_content` | BM25 sparse keyword full-text search |
| `kg_relationships`| `idx_kg_rel_src` | B-tree | `organization_id, source_entity_id` | Forward graph neighbor traversal |
| `kg_relationships`| `idx_kg_rel_tgt` | B-tree | `organization_id, target_entity_id` | Reverse graph neighbor traversal |
| `chat_messages` | `idx_chat_messages_session`| B-tree | `session_id, created_at` | Rapid chronological message rendering |
| `activity_logs` | `idx_activity_org_created` | B-tree | `organization_id, created_at DESC` | Security audit trail queries |

---

## 9. Alignment & Instructions for Team Members

- **Member 2 (Backend Lead)**: Implement SQLAlchemy 2.0 ORM models in `backend/app/models/` mirroring this specification, create repository classes in `backend/app/repositories/`, and generate initial Alembic migration scripts in `backend/migrations/versions/`.
- **Member 3 (Frontend Lead)**: Ensure frontend TypeScript models and DTO interfaces align with the relational entities (Organizations, Users, Projects, Documents, Chunks, Chat Sessions, Citations).
- **Member 4 (DevOps Lead)**: Verify PostgreSQL 16 container includes the `pgvector` extension and validate migration upgrade/downgrade commands in CI/CD pipeline.
