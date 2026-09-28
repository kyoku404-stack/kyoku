# KEEP — Detailed System Architecture (docs/Architecture/system-architecture.md)

> **Subsystem Engineering Specification & Component Interaction Topology**  
> *Owner: Member 1 (Project Lead & AI Architect)*

---

## 1. System Topology Overview

The KEEP platform is architectured as a modern, containerized monorepo with clean separation of concerns across presentation, API gateway, domain services, asynchronous worker execution, and polyglot persistence.

```
+-----------------------------------------------------------------------------------+
|                                 CLIENT LAYER                                      |
|  Next.js / React 18+ (TypeScript) + Tailwind CSS + Zustand State Store            |
+-----------------------------------------------------------------------------------+
                                         │  HTTPS / WSS
                                         ▼
+-----------------------------------------------------------------------------------+
|                             GATEWAY & API LAYER                                   |
|  FastAPI Engine (Python 3.12)                                                     |
|  - CORS, Rate Limiting, Request ID Middleware                                     |
|  - JWT Authentication & RBAC Authorization Dependency Injection                   |
|  - API Router v1 (/auth, /users, /orgs, /documents, /search, /chat, /analytics)   |
+-----------------------------------------------------------------------------------+
            │                                 │                              │
            ▼                                 ▼                              ▼
+-----------------------+         +-----------------------+      +------------------+
|   DOCUMENT SERVICE    |         |   RAG & SEARCH ENGINE |      | KNOWLEDGE GRAPH  |
| - Multipart Uploads   |         | - Hybrid Retrieval    |      | - Entity Triple  |
| - Validation & Storage|         | - BM25 + pgvector     |      |   Extraction     |
| - Task Dispatcher     |         | - Re-ranking & LLMs   |      | - Graph Queries  |
+-----------------------+         +-----------------------+      +------------------+
            │                                 │                              │
            ▼                                 │                              │
+-----------------------+                     │                              │
|  REDIS TASK QUEUE     |                     │                              │
+-----------------------+                     │                              │
            │                                 │                              │
            ▼                                 │                              │
+-----------------------+                     │                              │
| CELERY WORKER PIPELINE|                     │                              │
| - Text / OCR Extract  |                     │                              │
| - Semantic Chunking   |                     │                              │
| - Vector Embeddings   |                     │                              │
+-----------------------+                     │                              │
            │                                 │                              │
            ▼                                 ▼                              ▼
+-----------------------------------------------------------------------------------+
|                               PERSISTENCE LAYER                                   |
| - PostgreSQL 16 (Relational: Users, Organizations, Documents, Audit Logs)         |
| - pgvector Extension (Vector Index: Document Chunks, Embeddings, HNSW Index)      |
| - PostgreSQL Graph CTEs / Neo4j (Entity-Relationship Graph Store)                  |
| - Local / Object Storage S3 (Encrypted Document File Storage)                     |
+-----------------------------------------------------------------------------------+
```

---

## 2. Layered Backend Design Pattern

Backend modules adhere strictly to a 4-tier layered architecture:

```
[ FastAPI Router Layer ]  -->  Handles HTTP request parsing, Pydantic validation, status codes
         │
         ▼
[ Service Business Layer ] -->  Encapsulates core business rules, multi-tenant validation, orchestrates tasks
         │
         ▼
[ Repository Data Layer ]  -->  Abstracts database queries, vector similarity searches, graph lookups
         │
         ▼
[ SQLAlchemy ORM Layer ]   -->  Represents physical database schema, tables, and relationships
```

### Benefits:
- **Testability**: Services and repositories can be unit tested with mock adapters without a running database.
- **Decoupling**: Business logic remains independent of the database driver or API framework.
- **Maintainability**: Clear separation prevents code duplication across endpoints.

---

## 3. Asynchronous Ingestion & Task Processing Pipeline

1. **Upload Initiation**:
   - The user sends a document via `POST /api/v1/documents/upload`.
   - The API verifies MIME type (PDF, DOCX, TXT, PNG, JPG), enforces tenant quotas, and writes raw bytes to secure storage.
   - A `PENDING` database record is inserted into the `documents` table.
2. **Task Enqueuing**:
   - An asynchronous task `process_document_task(document_id, organization_id)` is published to Redis.
   - The API immediately responds with `202 Accepted` and the document ID.
3. **Worker Processing**:
   - Celery worker receives the task:
     - **Extraction**: Reads document via PyMuPDF (PDF), python-docx (Word), or Tesseract (images/scanned PDFs).
     - **Sanitization & Normalization**: Strips invalid Unicode, normalizes whitespace.
     - **Chunking**: Splits into 512-token chunks with 64-token overlap.
     - **Embedding**: Generates vectors using SentenceTransformers / OpenAI Embeddings.
     - **Vector Storage**: Writes chunks to `document_chunks` table in PostgreSQL with pgvector embeddings.
     - **Knowledge Graph Extraction**: Identifies key enterprise entities and relationships.
     - **Finalization**: Updates `documents.status = 'PROCESSED'`.

---

## 4. Multi-Tenant Isolation Strategy

KEEP implements **Row-Level Shared-Database Multi-Tenancy**:
- All tenant-owned records have a foreign key `organization_id: UUID`.
- Tenant context is extracted from the verified JWT token upon every request.
- Repositories inject `filter(Model.organization_id == current_tenant_id)` on all reads, updates, and deletes.
- Vector searches filter vector indexes by tenant ID in the metadata payload to prevent cross-tenant data leakage.

---

## 5. Security & Observability

- **Zero-Trust Token Management**: Short-lived JWT access tokens (15–60 min) with rolling refresh tokens stored securely in HTTP-only cookies.
- **Audit Logging**: All write, delete, and AI query operations log structured JSON audit records containing `user_id`, `organization_id`, `action`, `resource_id`, and `ip_address`.
- **Structured Error Handling**: Global exception handlers intercept all unhandled exceptions, returning standard RFC-7807 compliant problem details and preventing stack trace leakage.
