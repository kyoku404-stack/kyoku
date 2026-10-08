# Architecture Decision Log & Assumptions (docs/decisions/decisions.md)

> **Official Architecture Decision Records (ADRs) and Technical Assumptions for KEEP**  
> *Maintained by Member 1 (Project Lead & AI Architect)*

---

## Architecture Decision Records (ADRs)

### ADR-001 — Monorepo Architecture Selection

#### Date
2026-08-17

#### Context
KEEP requires seamless co-development of frontend UI, backend FastAPI services, ingestion workers, database schemas, and DevOps configuration across four autonomous development agents.

#### Decision
Establish a single monorepo structure containing `/frontend`, `/backend`, `/docker`, `/infrastructure`, `/docs`, `/tests`, and `/devdocs`.

#### Alternatives Considered
- Separate repositories for frontend and backend: Rejected due to cross-repository branch coordination complexity for autonomous agents.

#### Reason
A monorepo provides atomic Git commits across frontend and backend contract updates, simplifies CI/CD execution, and maintains a unified source of truth.

#### Impact
Agents operate on isolated feature branches within the single repository.

#### Status
ACCEPTED

---

### ADR-002 — Backend Framework & Persistence Alignment

#### Date
2026-08-17

#### Context
`devdocs/` specifies high-concurrency API performance, asynchronous background ingestion, and Python AI/ML library integration (LangChain, PyMuPDF, SentenceTransformers).

#### Decision
Adopt **FastAPI** (Python 3.12+) as the core backend API engine, combined with **SQLAlchemy 2.0 ORM**, **Alembic** migrations, and **PostgreSQL 16**.

#### Alternatives Considered
- Django REST Framework: Rejected due to synchronous ORM overhead for async AI streaming.
- Node.js Express: Rejected due to python-native AI/ML ecosystem requirements.

#### Reason
FastAPI provides native `asyncio` performance, automatic Pydantic OpenAPI schema generation, and seamless integration with Python AI packages.

#### Status
ACCEPTED

---

### ADR-003 — Multi-Tenant Isolation Pattern

#### Date
2026-08-17

#### Context
KEEP is an enterprise platform serving multiple organizations. Strict tenant data segregation is required across relational data, documents, and vector embeddings.

#### Decision
Enforce tenant isolation via an explicit `organization_id` foreign key column on all database entities, file storage prefixes, and vector payload metadata.

#### Alternatives Considered
- Separate PostgreSQL schema per tenant: Rejected due to high migration and connection pool overhead for many tenants.
- Separate database per tenant: Rejected due to excessive operational complexity.

#### Reason
Row-level tenant filtering backed by mandatory middleware checks ensures security while maintaining operational simplicity and high scalability.

#### Status
ACCEPTED

---

### ADR-004 — Vector Storage & Hybrid Search Engine

#### Date
2026-09-28

#### Context
Enterprise knowledge queries require both semantic understanding (understanding concepts) and exact keyword precision (names, part numbers, exact acronyms). Pure vector search suffers from vocabulary mismatch, while keyword search lacks semantic context.

#### Decision
Implement **Hybrid Search** combining:
1. **Dense Semantic Search**: Vector embeddings stored in PostgreSQL via the `pgvector` extension (with abstract provider interface supporting Qdrant/Chroma for high-scale environments).
2. **Sparse Keyword Search**: PostgreSQL full-text search (`tsvector` with BM25 ranking algorithm).
3. **Rank Fusion**: Reciprocal Rank Fusion (RRF) followed by Cross-Encoder reranking for top candidates.

#### Alternatives Considered
- Vector-only search: Inadequate for exact product codes, acronyms, and legal clause numbers.
- ElasticSearch / OpenSearch standalone: Adds additional container infrastructure overhead for MVP phase.

#### Reason
PostgreSQL 16 + `pgvector` allows transactional consistency between document metadata, relational entities, and vector embeddings within a single unified database engine.

#### Status
ACCEPTED

---

### ADR-005 — AI & LLM Provider Abstraction Layer

#### Date
2026-09-28

#### Context
Enterprise deployments may use cloud LLM APIs (OpenAI, Anthropic) or on-premise open-source LLMs (Ollama, vLLM, HuggingFace) depending on security compliance and air-gapped environments.

#### Decision
Implement abstract interfaces (`BaseLLMService`, `BaseEmbeddingService`, `BaseRetriever`, `BaseReranker`) in `/backend/app/services/ai/` and `/backend/app/services/rag/`. Concrete implementations are instantiated via dependency injection configured through environment settings (`AI_PROVIDER=openai|local|mock`).

#### Alternatives Considered
- Hardcoded OpenAI SDK calls: Creates vendor lock-in and impedes offline development/testing.

#### Reason
Enables zero-cost mock testing in CI pipelines, local execution without API keys, and enterprise compliance flexibility.

#### Status
ACCEPTED

---

### ADR-006 — Backend Layering, Standardized Envelope & Error Handling Protocol

#### Date
2026-09-30

#### Context
`devdocs/p1/p1.2.txt` Chapters 10, 14, and 15 mandate a strict 4-tier layered architecture (Router -> Service -> Repository -> Database) and a standardized JSON response format across all endpoints to guarantee predictable frontend consumption and decoupled backend evolution.

#### Decision
1. Standardize all API responses to follow a uniform envelope:
   - Success: `{"success": true, "message": str, "data": Any}`
   - Error: `{"success": false, "error": {"code": str, "message": str, "details": dict}}`
2. Implement global exception handling middleware that catches domain exceptions (`AppException`, `NotFoundException`, `AuthException`, `ValidationException`, `AIServiceException`) and transforms them into standard error envelopes without exposing internal stack traces.
3. Enforce strict layered boundaries: Routers only parse HTTP and invoke Services; Services only contain business logic and call Repositories; Repositories only execute database queries with explicit tenant filters.

#### Alternatives Considered
- Direct raw JSON returns per endpoint: Leads to inconsistent frontend error handling and breaking changes.
- Placing business logic inside FastAPI route handlers: Causes tight coupling and impedes unit testing.

#### Reason
Ensures robust contract stability for Member 3 (Frontend), eliminates boilerplate exception handling across endpoints, and enables comprehensive unit testing.

#### Status
ACCEPTED

---

### ADR-007 — AI Service Integration Points, Streaming Protocol & Context Hooks

#### Date
2026-09-30

#### Context
`devdocs/p1/p1.2.txt` Chapter 19 requires Member 1 (Project Lead & AI Architect) to define AI service interfaces and integration points for the backend. AI features (RAG Q&A, Document Summarization, Semantic Search) require real-time streaming, token usage tracking, and multi-tenant isolation.

#### Decision
1. Define abstract contracts in `/backend/app/services/rag/` and `/backend/app/services/ai/` for:
   - `BaseHybridSearchService`, `BaseContextBuilder`, `BaseCitationFormatter`, `BaseRAGEngine`
   - `BaseLLMService`, `BaseEmbeddingService`, `BasePromptService`, `BaseSemanticCacheService`, `BaseTokenTrackerService`, `BaseAssistantService`
2. Expose streaming AI completions using Server-Sent Events (SSE) `/api/v1/chat/stream` yielding typed event packets: `{"event": "token"|"citation"|"error"|"done", "data": ...}`.
3. Embed `AIExecutionContext` (capturing tenant_id, user_id, session_id, latency_ms, token_usage) across all AI calls to guarantee tenant isolation and audit logging.

#### Alternatives Considered
- Direct synchronous blocking LLM responses: Unacceptable latency (>5s) for user-facing chat interactions.
- Coupling AI provider SDKs directly into database models: Violates separation of concerns.

#### Reason
Abstract interfaces insulate the application from LLM provider pricing/API changes, provide native SSE streaming for instant UI feedback, and maintain strict tenant boundaries.

#### Status
ACCEPTED

---

### ADR-008 — Multi-Tenant Schema Strategy, pgvector Vector Storage & Chunk Indexing

#### Date
2026-10-02

#### Context
`devdocs/p1/p1.3.txt` Chapters 6, 7, 14, and 19 require designing and validating the complete database persistence layer for KEEP, including multi-tenancy, soft deletion, document chunk storage, vector embeddings, and indexing.

#### Decision
1. Adopt **PostgreSQL 16 + pgvector** as the unified storage engine for both relational entities and vector embeddings (`document_chunks.embedding vector(1536)`).
2. Use **Hierarchical Navigable Small World (HNSW)** indexing with cosine distance (`vector_cosine_ops`, `m=16`, `ef_construction=64`) for sub-millisecond approximate nearest neighbor (ANN) retrieval.
3. Add a stored generated `tsvector` column (`tsv_content`) indexed via GIN on `document_chunks` for integrated BM25 full-text keyword retrieval.
4. Enforce soft deletion via `SoftDeleteMixin` (`is_deleted`, `deleted_at`) across all primary business entities.

#### Alternatives Considered
- Storing vectors in an external Qdrant container for MVP: Adds operational complexity and requires 2-phase commits between Postgres and Qdrant.
- IVFFlat vector indexing: Requires pre-training and re-indexing as data grows; HNSW provides higher recall without rebuild overhead.

#### Reason
Keeps operational architecture lean, ensures transactional consistency between documents and chunks, and provides blazing fast hybrid search capabilities.

#### Status
ACCEPTED

---

### ADR-009 — Relational Knowledge Graph Store (Nodes, Edges, Triples) & Hybrid Search Persistence

#### Date
2026-10-02

#### Context
Phase 1.3 and Phase 2.4 require relational schema preparation for enterprise Knowledge Graph entity linking and relationship discovery without requiring an immediate dedicated graph database.

#### Decision
1. Implement MVP Knowledge Graph storage in PostgreSQL using two normalized relational tables:
   - `kg_entities`: Represents semantic nodes (UUID, `organization_id`, `name`, `entity_type`, `properties` JSONB).
   - `kg_relationships`: Represents directed semantic edges (UUID, `organization_id`, `source_entity_id`, `target_entity_id`, `relation_type`, `weight`, `confidence_score`, `properties` JSONB).
2. Index forward and reverse graph lookups using composite B-tree indices on `(organization_id, source_entity_id)` and `(organization_id, target_entity_id)`.
3. Support multi-hop traversals via PostgreSQL Recursive Common Table Expressions (CTEs).

#### Alternatives Considered
- Neo4j / Amazon Neptune from Day 1: Adds substantial container footprint and cross-database sync overhead during Phase 1 & 2 development.

#### Reason
PostgreSQL relational tables with JSONB and recursive CTEs easily satisfy 2-hop to 3-hop enterprise entity traversals while maintaining full ACID guarantees and multi-tenant isolation.

#### Status
ACCEPTED

---

### ADR-010 — Conversational State, Message History, Citation Provenance & AI Audit Logging Persistence

#### Date
2026-10-02

#### Context
AI chat workflows require persistent conversational memory across browser sessions, token quota tracking, verified citation provenance linking back to source documents, and human feedback collection.

#### Decision
1. Model conversational persistence with:
   - `chat_sessions`: Tenant-scoped session container (`id`, `organization_id`, `user_id`, `title`, `is_archived`).
   - `chat_messages`: Chronological message records (`id`, `session_id`, `role`, `content`, `model_name`, `tokens_prompt`, `tokens_completion`, `latency_ms`, `citations_json`, `tool_calls_json`).
2. Persist user feedback via `ai_feedback` (`message_id`, `rating`, `comment`) for model fine-tuning and retrieval quality evaluation.
3. Record all AI generation invocations and access requests into an immutable `activity_logs` table for enterprise audit compliance.

#### Alternatives Considered
- Storing chat history purely in Redis: Lost upon container restarts, lacks relational joins with documents/projects.
- Embedding raw citations as unstructured strings in message text: Precludes clickable UI provenance navigation.

#### Reason
Relational chat and feedback persistence enables seamless historical analysis, token quota monitoring, and verifiable citation traceability.

#### Status
ACCEPTED

---

### ADR-011 — Enterprise RBAC Matrix, Hierarchical Inheritance & Role Resolution Strategy

#### Date
2026-10-09

#### Context
`devdocs/p1/p1.4.txt` (Chapter 10) defines a 4-role hierarchy: Organization Admin > Project Manager > Employee (Member) > Viewer. The platform requires a formal permission resolution model that ensures deterministic authorization checks across all API endpoints, prevents privilege leakage, and supports role inheritance cleanly without hardcoded if/else ladders.

#### Decision
1. Establish a canonical role hierarchy:
   - `Organization Admin` inherits all permissions of `Project Manager`.
   - `Project Manager` inherits all permissions of `Employee`.
   - `Employee` inherits all permissions of `Viewer`.
2. Formalize granular permission strings (e.g., `doc:read`, `doc:create`, `doc:delete`, `chat:query`, `users:manage`, `kg:write`) mapped to roles in a centralized permission registry.
3. Enforce authorization via FastAPI dependencies (`require_permission` / `require_role`) and domain security context checks.

#### Alternatives Considered
- Flat roles with manual permission lists stored per user in the database: Overcomplicates MVP administration and migration overhead.
- Attribute-Based Access Control (ABAC) engine (e.g., Open Policy Agent): Excessive architectural overhead for Phase 1 MVP requirements.

#### Reason
Hierarchical RBAC maps directly to enterprise departmental structures while allowing rapid deterministic evaluations in under 1ms.

#### Status
ACCEPTED

---

### ADR-012 — Tenant-Scoped Identity Context & Access-Controlled AI Retrieval (RAG & KG)

#### Date
2026-10-09

#### Context
KEEP is an AI-first knowledge platform. Unlike standard CRUD APIs where database queries are trivially filtered, AI workflows (Hybrid RAG, Knowledge Graph traversal, semantic vector similarity, autonomous tool calling) can inadvertently leak sensitive enterprise intelligence across tenant boundaries or unauthorized user roles if security is not natively bound to the AI execution context.

#### Decision
1. Immutably inject `AISecurityContext` and `RAGSecurityContext` into all AI operations (`BaseLLMService`, `BaseRetriever`, `BaseVectorStore`, `BaseKnowledgeGraphStore`, `BaseAssistantService`).
2. Enforce two-layer retrieval gating:
   - Layer 1 (Tenant Hard Boundary): All vector queries, BM25 searches, and KG CTE queries strictly filter by `organization_id`.
   - Layer 2 (Permission & Visibility Gating): Restrict candidate retrieval chunks and graph entity traversals based on user role and permitted document IDs before assembling prompt contexts.
3. Tool Execution Gating: When the AI agent dispatches tool calls, tools are filtered and verified against `BaseAIAccessController.can_access_tool(tool_name, security_context)`.

#### Alternatives Considered
- Filtering retrieved context post-generation via LLM prompt instructions ("Please do not reveal info if user is not authorized"): Unreliable, highly vulnerable to prompt injection and jailbreak attacks.
- Universal unrestricted organizational search for all users: Violates enterprise document confidentiality where certain documents are restricted to management or specific teams.

#### Reason
Binding security context directly into retrieval and tool execution guarantees zero-leakage enterprise AI safety.

#### Status
ACCEPTED

---

### ADR-013 — Stateless JWT Double-Token Lifecycle, Session Revocation & Security Policy

#### Date
2026-10-09

#### Context
`devdocs/p1/p1.4.txt` (Chapters 6–9, 14–17) mandates secure user authentication, token-based session management, immediate session invalidation upon logout or password reset, and password complexity defense.

#### Decision
1. Adopt a stateless JWT double-token protocol:
   - Short-lived Access Token (15–30 min) containing signed claims (`sub`, `org_id`, `role`, `email`, `type="access"`).
   - Long-lived Refresh Token (14–30 days) with unique UUID (`jti`) and `type="refresh"`.
2. Implement Refresh Token Rotation: Each token refresh issues a new access/refresh token pair and invalidates the previous refresh token.
3. Store active sessions in the database (`activity_logs` / session registry) capturing `user_id`, `organization_id`, `ip_address`, and `user_agent`.
4. Enforce immediate invalidation upon `POST /api/v1/auth/logout` and password reset by revoking active refresh tokens.
5. Standardize password complexity: Minimum 8 characters, uppercase, lowercase, digit, and special character, hashed via salted bcrypt (work factor 12) or Argon2id.

#### Alternatives Considered
- Server-side session store with opaque tokens for all API calls: Requires database/Redis lookups on every single micro-request, degrading API throughput under load.
- Single long-lived JWT access token: Impossible to revoke securely before expiration.

#### Reason
The double-token strategy combines maximum API performance with robust session revocation and rotation security.

#### Status
ACCEPTED

---

## Documented Assumptions

### Assumption 001 — Knowledge Graph Storage Engine (PostgreSQL MVP -> Neo4j)

#### Reason
Phase 2.4 specifies Knowledge Graph construction. Section 2.4 notes: "Future implementations may use Neo4j or Amazon Neptune, while the MVP may initially model relationships using PostgreSQL before migrating to a dedicated graph database."

#### Temporary Decision
Initial Phase 2.4 Knowledge Graph development will model entities (`kg_entities`) and relationships (`kg_relationships`) within PostgreSQL using relational tables and CTE graph queries before introducing a dedicated Neo4j service in Phase 3.6.

#### Impact
Simplifies Phase 2 infrastructure overhead while preserving full graph semantics and entity traversal capabilities.

#### Requires Confirmation
YES (From Human Maintainer prior to Phase 2.4)

---

### Assumption 002 — Vector Store Selection for Local Development

#### Reason
`devdocs/` Phase 2.1 & 2.2 specify vector embedding storage and retrieval without forcing a single vector vendor for local dev vs production.

#### Temporary Decision
Use PostgreSQL with `pgvector` extension for standard local Docker Compose development to minimize container count, with an abstract vector repository layer allowing seamless pluggability for Qdrant in production.

#### Impact
Reduces system resource usage during local four-agent test execution.

#### Requires Confirmation
NO (Implementation detail abstracted via vector service layer)
