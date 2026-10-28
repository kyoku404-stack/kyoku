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

### ADR-014 — Multi-Tier Organizational Hierarchy & Context-Aware Knowledge Retrieval

#### Date
2026-10-10

#### Context
`devdocs/p1/p1.5.txt` (Chapters 1–8, 13, 20) defines the enterprise management layer of KEEP, requiring organizations to manage workspaces, departments, teams, projects, user memberships, and hierarchy. This hierarchy forms the foundation for enterprise search, organizational memory, and AI knowledge retrieval.

#### Decision
1. Model the enterprise structure as a 4-tier hierarchy:
   - Organization (Root tenant boundary)
   - Departments (Functional divisions: Engineering, Sales, HR, etc.)
   - Teams (Collaborative units within departments)
   - Projects (Workspaces containing documents, meetings, tasks, and discussions)
2. Support dynamic multi-tier context scoping for AI operations:
   - Local Project Scope: High-precision retrieval for project-specific tasks and queries.
   - Team & Department Scope: Fallback for operational workflows, team standards, and divisional policies.
   - Organization-Wide Scope: Fallback for enterprise handbooks, compliance manuals, and general corporate knowledge.
3. Every knowledge resource (document, vector chunk, meeting transcript, KG entity) tracks its hierarchical ownership (`organization_id`, `department_id`, `team_id`, `project_id`).

#### Alternatives Considered
- Flat workspace model (all projects belong directly to an organization without departments or teams): Simpler, but insufficient for large enterprise tenants with hundreds of users and distinct divisional boundaries.
- Ad-hoc tag-based organization: Lacks strict governance, deterministic access control, and structured search relevance.

#### Reason
Hierarchical modeling matches real-world corporate structure and allows the AI retrieval engine to balance precision and recall intelligently without polluting project contexts with irrelevant departmental data.

#### Status
ACCEPTED

---

### ADR-015 — Multi-Tenant Workspace Isolation Barrier & AI Context Quarantine

#### Date
2026-10-10

#### Context
`devdocs/p1/p1.5.txt` (Chapter 16) mandates absolute multi-tenant data isolation across documents, projects, teams, meetings, AI chats, analytics, and search results. Data leakage across tenants represents a catastrophic enterprise security violation.

#### Decision
1. Enforce a cryptographic and relational zero-trust isolation barrier:
   - Tenant Identity: Verified server-side via the signed JWT `org_id` claim on every incoming request.
   - Database Scope: Every database query executed via repositories and ORM must explicitly filter by `organization_id`.
   - Vector Store Scope: All vector similarity and hybrid search queries (`pgvector` / Qdrant) must enforce hard metadata filtering on `organization_id`.
   - Knowledge Graph Scope: Recursive CTE graph traversals must strictly constrain candidate nodes and edges to `organization_id`.
2. AI Prompt & Context Quarantine:
   - Retrieval candidates must be pre-filtered by `organization_id` before entering prompt assembly pipelines.
   - Semantic cache entries are strictly keyed by `(organization_id, query_hash)`.

#### Alternatives Considered
- Database-per-tenant architecture: Maximum isolation, but excessive operational overhead, high connection pool starvation, and migration complexity for hundreds of tenants.
- Schema-per-tenant architecture: High maintenance overhead with Alembic migrations across dynamic schemas.

#### Reason
Row-level multi-tenancy with strict composite indexes, foreign key constraints, and application-layer gatekeeping provides enterprise security with optimal hardware utilization and simplified operational maintenance.

#### Status
ACCEPTED

---

### ADR-016 — Department & Team Scoped AI Permissions & Retrieval Inheritance

#### Date
2026-10-10

#### Context
`devdocs/p1/p1.5.txt` (Chapters 14 & 20) requires extending the permission model established in Phase 1.4 to govern departments, teams, projects, invitations, and membership management, while ensuring AI operations respect departmental boundaries.

#### Decision
1. Expand `AIPermission` enum with granular workspace management permissions:
   - `org:create`, `org:read`, `org:update`, `org:delete`, `org:settings`
   - `dept:create`, `dept:read`, `dept:update`, `dept:delete`
   - `team:create`, `team:read`, `team:update`, `team:delete`
   - `project:create`, `project:read`, `project:update`, `project:delete`, `project:membership`
   - `invitation:create`, `invitation:read`, `invitation:revoke`
   - `member:read`, `member:update`, `member:remove`
2. Integrate department, team, and project scoping into `AISecurityContext` and `RAGSecurityContext`:
   - `AISecurityContext`: Tracks caller's `department_id`, set of active `team_ids`, and set of accessible `project_ids`.
   - `RAGSecurityContext`: Implements `can_access_project()`, `can_access_department()`, and `can_access_document()`.
3. Provide abstract interfaces for context resolution (`BaseWorkspaceContextResolver`) and tenant validation (`BaseTenantIsolationValidator`).

#### Alternatives Considered
- Static role-based checks without resource scoping: Fails to enforce that a Project Manager can only manage projects they actually own or belong to.
- Complex attribute-based access control (ABAC) engine with runtime policy DSL: Overengineered for the current phase, adds unnecessary latency to AI inference pipelines.

#### Reason
Extending the typed security context with hierarchical scope identifiers provides deterministic, high-performance authorization for both REST endpoints and AI retrieval pipelines.

#### Status
ACCEPTED

---

### ADR-017 — Action-Based Permission Model & Hierarchical Role Mapping

#### Date
2026-10-12

#### Context
`devdocs/p1/p1.6.txt` (Chapters 4, 5, 6) mandates an action-based permission model (`document.create`, `document.delete`, `project.manage`, `meeting.create`, `ai.chat`, `organization.manage`, etc.) rather than monolithic role-name checks. Roles must receive curated sets of permissions with hierarchical inheritance from lower to higher tiers.

#### Decision
1. Define granular, action-based permissions in `AIPermission` enum:
   - `document.create`, `document.read`, `document.update`, `document.delete`
   - `project.manage`, `project.membership`
   - `meeting.create`, `meeting.read`, `meeting.manage`
   - `ai.chat`, `ai.search`, `ai.admin`, `ai.config`
   - `organization.manage`, `organization.settings`
   - `user.invite`, `user.manage`, `user.view`
   - `analytics.view`, `analytics.export`
   - `audit.read`
2. Map canonical permissions hierarchically across the 5 system roles:
   - `Viewer`: Read-only access to documents, meetings, AI search/chat, dashboards.
   - `Member` / `Employee`: Inherits Viewer + document creation/updates.
   - `ProjectManager`: Inherits Member + document deletion, project management, meeting creation/management, member invitations.
   - `OrgAdmin`: Inherits ProjectManager + tenant settings, user management, AI administration, analytics export, audit logs.
   - `SuperAdmin`: Inherits OrgAdmin + system organization creation.

#### Alternatives Considered
- Direct role-string comparisons in route handlers (`if user.role != "Admin"`): Fragile, prevents fine-grained delegation, incompatible with future custom role configurations.
- Coarse read/write/admin permissions: Insufficient granularity for enterprise compliance (e.g., distinguishing document upload from document deletion).

#### Reason
Action-based keys decouple permission checks from role assignments, enabling future custom roles without refactoring endpoint guards.

#### Status
ACCEPTED

---

### ADR-018 — Resource-Level Authorization & Ownership Bypass Policy

#### Date
2026-10-12

#### Context
`devdocs/p1/p1.6.txt` (Chapters 7, 9, 10, 11) specifies that access decisions must evaluate both caller identity and target resource metadata (organization tenant boundary, project membership, and resource ownership). Certain resources grant elevated permissions to creators regardless of base role (e.g., an Employee who uploaded a document may update or delete their own upload).

#### Decision
1. Model resource evaluation via a typed `ResourceAuthorizationContext` capturing `caller_id`, `caller_role`, `caller_org_id`, `caller_project_ids`, `resource_id`, `resource_type`, `resource_org_id`, `resource_owner_id`, `resource_project_id`, and `required_permission`.
2. Establish a deterministic 7-step authorization evaluation pipeline:
   - Step 1: Hard tenant boundary check (`caller_org_id == resource_org_id`) -> immediate `AUTH_ORGANIZATION_MISMATCH` (403) on mismatch.
   - Step 2: Role permission evaluation (`required_permission in caller.permissions`).
   - Step 3: Ownership override check (`BaseResourceOwnershipChecker.is_owner()`) for permitted actions (`document.update`, `document.delete`, `meeting.manage`, `chat_session.delete`).
   - Step 4: Project workspace containment check (`resource_project_id in caller_project_ids`) for non-admin users.
3. Define abstract contracts `BaseAuthorizationPolicyEngine` and `BaseResourceOwnershipChecker` in `backend/app/services/ai/interfaces.py`.

#### Alternatives Considered
- Decentralized checks inside each service handler: Results in inconsistent error codes, missing audit logs, and potential horizontal access bypasses.
- SQL-only row level security (RLS): Difficult to mock in unit test environments and does not integrate cleanly with FastAPI dependency injection and AI retrieval.

#### Reason
Centralized policy evaluation ensures uniform least-privilege enforcement, structured error reporting, and reliable audit trail generation.

#### Status
ACCEPTED

---

### ADR-019 — AI Retrieval Authorization Filtering & KG Traversal Scoping

#### Date
2026-10-12

#### Context
`devdocs/p1/p1.6.txt` (Chapter 14) requires that AI modules (RAG search, conversational context assembly, and Knowledge Graph entity traversal) inherit the exact same authorization boundaries as REST endpoints. No confidential document or entity from an unauthorized project or tenant may ever enter prompt context.

#### Decision
1. Introduce `BaseAIAuthorizationFilter` abstract interface in `backend/app/services/rag/interfaces.py`:
   - `filter_knowledge_candidates(candidates, security_context)`: Prunes candidate document chunks by tenant boundary, document-level read permission, and project membership.
   - `authorize_kg_traversal(entities, security_context)`: Filters Knowledge Graph nodes to only those originating from caller-accessible source documents.
2. Extend `RetrievalResult` dataclass with `organization_id` to enforce hard tenant validation during candidate pruning.
3. Enforce AI action permissions: `ai.chat` for RAG conversation, `ai.search` for semantic queries, `ai.admin` for quotas/monitoring, and `ai.config` for model tuning.

#### Alternatives Considered
- Filtering prompt outputs post-generation via LLM self-critique: Unreliable, incurs high token latency, and risks sensitive data leakage.
- Disregarding resource-level project scoping for AI prompts: Violates enterprise data isolation between internal project teams.

#### Reason
Pre-retrieval and in-pipeline candidate pruning prevents unauthorized context injection before prompts reach the LLM, ensuring zero data leakage.

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

---

### ADR-020 — Dashboard Widget-Level API Independence

#### Date
2026-10-13

#### Context
Phase 1.7 requires a dashboard that loads quickly and remains resilient when individual backend services are slow or temporarily unavailable. A single monolithic `GET /api/v1/dashboard` endpoint would create a hard dependency where one slow data source (e.g., analytics) delays the entire page render.

#### Decision
Each dashboard widget sources data from its own dedicated endpoint. Six separate endpoints are defined: `/api/v1/dashboard` (summary + KPIs), `/api/v1/activity`, `/api/v1/projects/recent`, `/api/v1/documents/recent`, `/api/v1/notifications`, `/api/v1/analytics/summary`. All six are dispatched in parallel immediately after the dashboard route mounts.

#### Alternatives Considered
- Single composite endpoint: Rejected — one slow data source delays full page render and prevents partial progressive hydration.
- GraphQL batching: Rejected — introduces GraphQL dependency not established in the Phase 1.2 tech stack decision (ADR-002).

#### Reason
Widget-level independence enables: (a) skeleton-first progressive render, (b) independent error boundaries per widget, (c) granular TTL-based caching in Redis, and (d) independent refresh polling intervals (e.g., notifications at 30s vs. analytics at 300s).

#### Impact
Member 2 implements six dedicated FastAPI endpoints. Member 3 implements six independent widget hooks with individual loading/error/empty states. Member 4 load tests each endpoint independently.

#### Status
ACCEPTED

---

### ADR-021 — CSS Custom Properties Token Layer for Theme Management

#### Date
2026-10-13

#### Context
Phase 1.7 requires Light, Dark, and System theme support. Future versions will require organization-specific branding. A naive approach of per-component color literals or duplicated CSS classes creates exponential maintenance burden.

#### Decision
All color, shadow, and spacing values are defined exclusively as CSS custom properties (variables) on `:root[data-theme="light"]` and `:root[data-theme="dark"]` in a dedicated `tokens.css` file. No component CSS file references hardcoded color values. Theme switching is achieved by toggling the `data-theme` attribute on the `<html>` element. The KEEP brand accent is Indigo (#6366F1 light / #818CF8 dark) with Violet (#8B5CF6 / #A78BFA) as secondary.

#### Alternatives Considered
- CSS-in-JS theme objects: Rejected — adds runtime overhead and a new dependency not in the established stack.
- Tailwind dark mode: Rejected — Tailwind is not in the established tech stack (ADR-002).
- Duplicate CSS files per theme: Rejected — leads to maintenance divergence across components.

#### Reason
A single token layer means organization branding in future phases requires only overriding the `:root[data-theme]` block with organization-specific values — zero component changes needed. Enforces design system consistency.

#### Impact
Member 3 creates `frontend/src/styles/tokens.css` and a `ThemeSwitcher` component. `DashboardContext` exposes `theme` / `setTheme`. Theme preference persisted in `localStorage` under key `keep_theme`.

#### Status
ACCEPTED

---

### ADR-022 — AI Assistant Widget as Integration Shell (Phase 1.7 Stub Strategy)

#### Date
2026-10-13

#### Context
The AI Assistant widget (Chapter 12 of Phase 1.7 spec) must appear fully functional in the dashboard UI today, but the underlying RAG engine (Phase 2.2), knowledge ingestion pipeline (Phase 2.1), and meeting intelligence (Phase 2.3) are not yet implemented.

#### Decision
The AI Assistant widget in Phase 1.7 is implemented as a **functional UI shell** with a stub backend endpoint (`POST /api/v1/ai/query`). The stub endpoint:
- Accepts the identical `AIQueryRequest` payload shape that Phase 2.2 will use.
- Returns a canned SSE stream: one `token` event with a placeholder response, then a `done` event with an empty `sources` array.
- Returns HTTP 200 with the correct SSE `Content-Type: text/event-stream` header so the frontend streaming client is exercised end-to-end.

The widget UI is fully implemented: query input, suggested prompts (role-filtered), streaming token display, source citation placeholders, session history panel. When Phase 2.2 activates, the backend stub is replaced with the real RAG pipeline — zero frontend changes required.

#### Alternatives Considered
- Placeholder UI only (no backend stub): Rejected — frontend SSE streaming client would not be exercised or tested in Phase 1.7; Phase 2 integration would require frontend changes.
- Mock API at the frontend layer: Rejected — hides real HTTP/SSE contract from integration tests.

#### Reason
The stub strategy ensures that the exact API contract, SSE streaming protocol, and frontend rendering pipeline are validated in Phase 1.7. The "seam" between Phase 1.7 (UI) and Phase 2.2 (RAG) is tested and provably clean.

#### Impact
Member 2 implements `POST /api/v1/ai/query` stub with SSE response. Member 3 implements full AI widget UI with EventSource client. Member 4 authors E2E tests that validate the stub SSE stream is received and rendered.

#### Status
ACCEPTED

---

### ADR-023 — Document Storage Layout, Tenant Isolation & Storage Abstraction (Local Disk MVP with S3 Compatibility)

#### Date
2026-10-15

#### Context
`devdocs/p1/p1.8.txt` (Chapters 7 & 8) mandates enterprise-grade document storage with strict organization-level isolation. Binary assets must be physically and logically segregated to guarantee that zero-trust tenant boundaries are upheld at both the relational persistence layer and the storage filesystem layer. While production deployments will leverage cloud object storage (Amazon S3 / Azure Blob Storage / MinIO), local development and test environments require a Docker-mounted volume without external cloud dependencies.

#### Decision
1. Abstract all physical storage operations behind an abstract interface `BaseFileStorageService` in `backend/app/services/rag/interfaces.py`, defining async methods:
   - `save_file(organization_id, document_id, version, filename, content_stream)`
   - `get_file_path(organization_id, document_id, version, filename)`
   - `delete_file(organization_id, document_id, version)`
   - `get_storage_usage(organization_id)`
   - `check_quota(organization_id, additional_bytes)`
2. Enforce a canonical hierarchical storage path structure:
   `storage/{organization_id}/documents/{document_id}/v{version_number}/{sanitized_filename}`
   `storage/{organization_id}/previews/{document_id}/v{version_number}/{preview_file}`
   `storage/{organization_id}/thumbnails/{document_id}/thumb_300x300.webp`
3. Prohibit direct web exposure of the `storage/` directory. All file downloads, streaming, and preview requests must route through authenticated FastAPI endpoints verifying caller permissions and tenant boundaries.
4. Implement `LocalStorageService` as the default provider for Phase 1.8 local containerized development.

#### Alternatives Considered
- Storing binary file data directly in PostgreSQL as `BYTEA` / BLOB columns: Rejected — causes extreme database bloat, degrades backup/restore performance, and exhausts database connection memory during multi-megabyte transfers.
- Single flat storage directory with hashed filenames: Rejected — loses tenant-level physical isolation, complicates organization data deletion / GDPR compliance, and risks catastrophic multi-tenant data exposure on configuration error.

#### Reason
Physical directory-level tenant isolation provides defense-in-depth security. The abstract storage service interface guarantees zero code refactoring when deploying to AWS S3 in production.

#### Impact
Member 2 implements `LocalStorageService` and integrates path generation into document service workflows. Member 4 configures Docker volume mounts for `/app/storage`.

#### Status
ACCEPTED

---

### ADR-024 — Document Metadata Schema, SHA-256 Checksum Deduplication & Ingestion State Machine

#### Date
2026-10-15

#### Context
`devdocs/p1/p1.8.txt` (Chapters 5, 6, 9, 14, 16) specifies that every uploaded file must capture rich technical, structural, and domain metadata, enforce validation checks (file types, size limits, filename sanitization), compute cryptographic checksums for duplicate detection, and progress through an explicit multi-step state machine leading to AI ingestion.

#### Decision
1. Define a standardized document metadata schema combining relational typed columns (`id`, `organization_id`, `project_id`, `uploader_id`, `filename`, `original_filename`, `file_type`, `mime_type`, `file_size`, `checksum_sha256`, `category`, `current_version_number`, `status`) with a rich `metadata_json` JSONB payload for dynamic extraction attributes (page count, author, word count, OCR applied, orientation, language).
2. Calculate SHA-256 checksums on the fly during upload streaming to enable instant duplicate detection against existing active documents within the tenant.
3. Establish an explicit 9-state processing state machine:
   `PENDING` -> `VALIDATED` -> `AWAITING_PROCESSING` -> `QUEUED` -> `EXTRACTING` -> `CHUNKING` -> `EMBEDDING` -> `READY_FOR_AI` (with terminal / operational branches `FAILED`, `ARCHIVED`, `DELETED`).
4. Validate incoming files against registered magic byte headers and size limits per format (PDF: 100MB, DOCX: 50MB, PPTX: 100MB, Images/Text/CSV: 20MB).

#### Alternatives Considered
- Synchronous text parsing and OCR during upload request: Rejected — parsing large PDFs or images exceeds HTTP timeout limits (e.g. 30–60s) and degrades API gateway responsiveness.
- Coarse status flags (`is_processed: bool`): Rejected — lacks observability into where background workers fail (e.g. OCR failure vs embedding model API timeout).

#### Reason
A 9-state pipeline provides clear visibility across long-running asynchronous worker operations and establishes idempotent recovery seams for Celery task retries.

#### Impact
Member 1 provides typed dataclasses and state machine contracts in `backend/app/services/rag/interfaces.py`. Member 2 implements upload validation, metadata persistence, and state transitions.

#### Status
ACCEPTED

---

### ADR-025 — Document Versioning Lineage, Vector Invalidation & RAG Ingestion Pipeline Seam

#### Date
2026-10-15

#### Context
`devdocs/p1/p1.8.txt` (Chapter 11) requires document revision and version tracking. When a user uploads a revised version of an existing document, the system must maintain complete historical lineage, allow previous versions to be inspected and downloaded, while ensuring the upcoming Phase 2 RAG vector indexing pipeline remains consistent and free of stale or duplicate semantic chunks.

#### Decision
1. Implement a two-tier relational model:
   - `documents` table represents the persistent knowledge entity (logical document).
   - `document_versions` table represents immutable physical revisions (`version_number: int`, `file_path`, `file_size`, `checksum_sha256`, `uploader_id`, `change_notes`, `metadata_json`, `created_at`).
2. Version numbers increment sequentially ($1, 2, 3, \dots$). `documents.current_version_id` points to the latest active version.
3. In Phase 2, `document_chunks` store both `document_id` and `document_version_id`.
4. When a new version is uploaded:
   - The new version snapshot is recorded and status set to `QUEUED`.
   - Previous version chunks remain active in RAG search until the new version successfully achieves `READY_FOR_AI`.
   - Upon successful completion, previous version chunks are deactivated (`is_active = FALSE`), preventing duplicate or conflicting citations while preserving historical citation provenance.

#### Alternatives Considered
- Destructive in-place overwrite of files: Rejected — destroys document auditability, violates enterprise compliance policies, and breaks provenance of citations in existing chat sessions.
- Non-linear branching version tree (DAG): Rejected — unnecessary complexity for enterprise knowledge management where documents evolve in linear revisions.

#### Reason
Linear immutable snapshots provide clean, audit-compliant document history and eliminate vector index corruption during concurrent asynchronous re-ingestion.

#### Impact
Member 1 specifies `document_versions` schema in `docs/database/database-schema.md` and typed interfaces. Member 2 creates SQLAlchemy model and Alembic migration. Member 3 develops version history timeline UI.

#### Status
ACCEPTED

---

### ADR-026 — Centralized JSON Structured Logging & W3C TraceContext Propagation

#### Date
2026-10-21

#### Context
`devdocs/p1/p1.9.txt` (Chapters 4, 5, 6, 11) mandates centralized logging across all application components (API, Auth, Database, Storage, Workers, AI) with structured attributes (timestamp, level, module, action, status, user_id, organization_id, request_id, execution_time_ms). Plain text unstructured logs (`print()` or default string logging) prevent machine parsing, query filtering in Grafana Loki, automated threshold alerting, and cross-service trace reconstruction during incident triage.

#### Decision
1. Standardize all log output to newline-delimited JSON (`ndjson`) emitted to `stdout`.
2. Adopt the canonical log schema defined in `docs/Architecture/observability-architecture.md`:
   `timestamp`, `level`, `module`, `action`, `status`, `user_id`, `organization_id`, `request_id`, `trace_id`, `execution_time_ms`, `ip_address`, `message`, `metadata`.
3. Implement request context middleware in FastAPI that:
   - Extracts incoming `X-Request-ID` or generates a UUIDv4 if missing.
   - Parses or initializes W3C `traceparent` headers (`trace_id`).
   - Binds `request_id`, `user_id`, and `organization_id` to Python `contextvars` for automatic injection into every log emission across synchronous and asynchronous call trees.
   - Echoes `X-Request-ID` in HTTP response headers.

#### Alternatives Considered
- Writing plain text log files locally to disk: Rejected — causes Docker volume contention, requires manual log rotation scripts, and prevents centralized aggregation in Loki/ELK.
- Requiring developers to pass `request_id` manually to every logging call: Rejected — error-prone and leads to missing correlation IDs deep inside repository and service layers.

#### Reason
Standardized JSON with contextvars-driven correlation propagation enables zero-overhead distributed log tracing and automated ingestion into Loki and Grafana.

#### Impact
Member 2 implements logging middleware and structured formatters. Member 4 configures Promtail/Loki log aggregation.

#### Status
ACCEPTED

---

### ADR-027 — Prometheus & OpenTelemetry Metrics Topology with Multi-Tier Health Check Probing

#### Date
2026-10-21

#### Context
`devdocs/p1/p1.9.txt` (Chapters 7, 8, 15) requires continuous performance metrics collection (API latency, throughput, error rates, database connections, storage utilization) and a multi-tier health probe architecture. Without granular probes, orchestrators like Docker Compose and Kubernetes cannot differentiate between a transient slow query and a hard crash, risking unnecessary container restarts or routing traffic to dead dependencies.

#### Decision
1. Expose Prometheus metrics at standard endpoint `GET /metrics` utilizing `prometheus_client` exposition format.
2. Provide a lightweight JSON aggregation endpoint `GET /api/v1/metrics/summary` for the frontend dashboard to display live operational telemetry without direct TSDB query dependencies.
3. Decouple health checks into five granular probe endpoints:
   - `GET /health`: Composite system health returning HTTP 200 (healthy/degraded) or 503 (unhealthy) with detailed sub-system dependency statuses.
   - `GET /health/database`: Verifies PostgreSQL connectivity (`SELECT 1`), active pool connections, and `pgvector` extension presence.
   - `GET /health/storage`: Validates storage directory write/read permissions and quota headroom.
   - `GET /health/api`: Reports process uptime, memory RSS, and active request count.
   - `GET /health/auth`: Verifies JWT secret key health and token signing readiness.

#### Alternatives Considered
- Single monolithic `/health` endpoint that performs heavy write/read checks on every ping: Rejected — causes database and disk I/O overhead under aggressive container liveness polling (e.g. every 5 seconds).
- Proprietary metrics JSON endpoint only: Rejected — prevents integration with standard industry observability stacks (Prometheus, Grafana, Datadog).

#### Reason
Multi-tier health checks allow load balancers to perform ultra-fast liveness checks (< 2ms) while enabling administrators to diagnose exact subsystem degradation. Prometheus standards ensure turnkey container infrastructure monitoring.

#### Impact
Member 2 implements health routes and Prometheus metric counters/histograms. Member 3 develops system status UI pages. Member 4 provisions Prometheus and Grafana services in Docker.

#### Status
ACCEPTED

---

### ADR-028 — AI Model, Embedding, and RAG Pipeline Observability Framework (Phase 2 Preparation)

#### Date
2026-10-21

#### Context
Phase 1.9 introduces system-wide observability while Phase 2 introduces production AI workloads (document chunking, embedding generation, dense/sparse RAG vector queries, and LLM answer generation). AI operations present unique failure modes: silent hallucinations, retrieval quality degradation, context window overflow, API rate limits (429), and uncontrolled token costs. Without purpose-built telemetry contracts established now, Phase 2 AI services will lack visibility.

#### Decision
1. Establish a dedicated AI Observability domain contract package in `backend/app/services/ai/observability.py`.
2. Define typed telemetry models:
   - `AIOperationType`: Categorizes AI operations (`EMBEDDING_GENERATION`, `VECTOR_SEARCH`, `LLM_COMPLETION`, `LLM_STREAM`, `RAG_QUERY`, `GRAPH_EXTRACTION`, `AGENT_TOOL_CALL`).
   - `AIExecutionMetrics`: Measures prompt tokens, completion tokens, total tokens, latency (TTFT and total), estimated cost in USD, and provider/model identifier.
   - `RAGRetrievalMetrics`: Measures query text, candidate chunk counts, rerank counts, top similarity scores, retrieval latency, and context token footprint.
   - `AIObservabilityEvent`: Unified audit and telemetry record capturing `trace_id`, `request_id`, `organization_id`, `user_id`, `project_id`, execution metrics, retrieval metrics, error details, and status.
3. Define abstract interfaces `BaseAIObservabilityCollector`, `BaseAICostCalculator`, and `BaseAITraceContext`.
4. Provide a thread-safe `InMemoryAIObservabilityCollector` for local testing and lightweight in-process metric aggregation, ensuring zero external vendor lock-in.

#### Alternatives Considered
- Direct coupling to proprietary LLM observability SaaS (e.g., LangSmith, Arize Phoenix, Weights & Biases): Rejected — introduces external network dependencies, privacy risks for sensitive enterprise tenant data, and cloud vendor lock-in.
- Postponing AI metrics to Phase 2.5: Rejected — without foundational contracts established in Phase 1.9, Phase 2.1 and Phase 2.2 would require ad-hoc logging that diverges across team members.

#### Reason
Clean interface abstraction in `services/ai/` guarantees that Phase 2 ingestion and RAG engines emit structured, auditable, and cost-attributed telemetry from Day 1.

#### Impact
Member 1 implements typed contracts and unit test verification. Member 2 integrates AI metrics into application metrics registry. Member 3 builds AI usage widget charts. Member 4 configures AI alert thresholds.

#### Status
ACCEPTED

---

### ADR-029 — Production Reverse Proxy, TLS Termination & Container Network Topology

#### Date
2026-10-23

#### Context
`devdocs/p1/p1.10.txt` (Chapters 3, 4, 5, 8, 11) mandates containerizing the application, configuring a production reverse proxy with HTTPS, and hardening system security. Direct exposure of application ports (FastAPI on 8000, Next.js on 3000, PostgreSQL on 5432, Redis on 6379) to public internet interfaces creates severe security vulnerabilities, lacks unified SSL/TLS lifecycle termination, and prevents standardized HTTP security header injection.

#### Decision
1. Standardize on **Nginx** (`nginx:1.27-alpine`) as the single public-facing reverse proxy and ingress gateway.
2. Route incoming traffic based on path rules:
   - `/*` routed to Frontend production container (Next.js/React).
   - `/api/v1/*` routed to Backend FastAPI container.
   - `/health` and `/health/*` routed to Backend health check probes.
   - `/metrics` restricted strictly to internal Docker network / Prometheus scraping.
3. Enforce strict TLS 1.3 / 1.2 termination with HTTP-to-HTTPS automatic 301 redirection.
4. Enforce enterprise security headers across all responses (`HSTS`, `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`).
5. Isolate all internal services (`backend`, `postgres`, `redis`, `loki`, `promtail`) on an internal Docker bridge network (`keep-network`) with zero direct host port publishing for database or cache services in production.

#### Alternatives Considered
- Direct host binding without reverse proxy: Rejected — exposes backend directly, complicates SSL certificate management, and lacks unified static caching and gzip compression.
- Envoy / Traefik: Rejected for MVP baseline — Nginx provides proven enterprise stability, minimal resource footprint (< 256MB), and direct support across all standard enterprise environments.

#### Reason
Nginx provides high throughput, battle-tested SSL/TLS termination, and flexible path routing while strictly isolating sensitive backend services inside Docker's virtual network.

#### Impact
Member 4 configures Nginx configuration and Docker Compose networking. Member 3 configures frontend production assets and API routing. Member 2 validates backend behind reverse proxy headers.

#### Status
ACCEPTED

---

### ADR-030 — Future AI Workload Infrastructure Isolation & Resource Scaling Architecture (Phase 2 Readiness)

#### Date
2026-10-23

#### Context
`devdocs/p1/p1.10.txt` (Chapters 5, 10, 15, 18) mandates that Phase 1.10 infrastructure configuration must prepare the platform for the heavy AI implementation phases beginning in Phase 2. AI operations (PDF OCR, multimodal extraction, SentenceTransformer embedding generation, dense vector similarity search in `pgvector`, and LLM answer synthesis) require significantly more memory, CPU, and worker concurrency than typical CRUD transactions. Executing AI tasks synchronously inside the FastAPI request-response event loop would cause thread starvation, slow API response times, and system-wide timeouts.

#### Decision
1. Establish dedicated asynchronous worker queues in Redis/Celery (`ai_ingestion_queue`, `ai_embedding_queue`, `ai_graph_queue`, `ai_batch_queue`) separate from primary web API workers.
2. Define standard hardware and sizing tiers (`MINIMUM_DEV`, `RECOMMENDED_PROD_CPU`, `HIGH_PERF_GPU`, `ENTERPRISE_DISTRIBUTED`) with typed validation contracts in `backend/app/services/ai/deployment.py`.
3. Provision a dedicated persistent volume `ai_model_cache` (`/app/models/cache`) to store local embedding weights and reranker models, preventing repetitive downloads and reducing container startup latency.
4. Optimize `pgvector` indexing parameters for production: HNSW index with `m = 16`, `ef_construction = 64`, and runtime query `ef_search = 40`, backed by `maintenance_work_mem = 512MB`.
5. Adopt a `HYBRID` execution model as the enterprise production baseline: local CPU/GPU for embedding and reranking, coupled with managed cloud API connectors for frontier LLM reasoning.

#### Alternatives Considered
- Synchronous in-process AI execution: Rejected — blocks HTTP event loops and causes request timeouts on multi-page PDF processing.
- Standalone external Vector DB SaaS only (Pinecone): Rejected — introduces external cloud vendor lock-in and cross-network latency; `pgvector` co-locates relational metadata and vectors inside the existing PostgreSQL 16 ACID boundary.

#### Reason
Queue-based workload isolation guarantees predictable API latency (< 300ms) for end users while enabling asynchronous AI workers to scale independently based on document ingestion volume.

#### Impact
Member 1 establishes typed contracts in `services/ai/` and `services/rag/`. Member 4 provisions Docker volumes and worker services. Member 2 integrates queue dispatching seams.

#### Status
ACCEPTED

---

### ADR-031 — Automated Continuous Deployment Pipeline, Health Gating & Disaster Recovery Strategy

#### Date
2026-10-23

#### Context
`devdocs/p1/p1.10.txt` (Chapters 7, 12, 13, 14) mandates automated CI/CD pipelines, daily backup policies, disaster recovery planning, and production deployment validation. Manual deployments risk configuration drift, missing database migrations, and unhandled production outages.

#### Decision
1. Implement a 6-stage GitHub Actions CI/CD deployment pipeline:
   - Stage 1: Static analysis (Ruff, ESLint, TypeScript `tsc --noEmit`).
   - Stage 2: Automated test execution (Pytest unit & integration suites, Vitest frontend suite).
   - Stage 3: Multi-stage Docker container build and image linting.
   - Stage 4: Staging deployment with container health probing.
   - Stage 5: Production deployment promotion with zero-downtime rolling update.
   - Stage 6: Health-gated rollback triggering if `GET /health` fails to report healthy status within 60 seconds.
2. Codify automated daily backups for:
   - PostgreSQL database (compressed `pg_dump` with 30-day retention).
   - Document storage volume (compressed tarball with SHA-256 integrity manifest).
3. Establish recovery objectives: RPO < 1 hour, RTO < 15 minutes.

#### Alternatives Considered
- Manual SSH deployment: Rejected — error-prone, non-auditable, and violates four-agent governance.
- Continuous deployment without health-check gating: Rejected — risks deploying broken configurations directly to live users without automated rollback safety.

#### Reason
Automated health-gated pipelines ensure that every production release is empirically verified before receiving production traffic, guaranteeing 99.9% platform availability.

#### Impact
Member 4 implements CI/CD workflow steps and backup/recovery shell scripts. Member 2 verifies database migration idempotency. Member 3 ensures zero-warning build artifacts.

#### Status
ACCEPTED

---

### ADR-032 — Hierarchical & Heading-Aware Semantic Chunking Strategy with Dynamic Sliding Overlap

#### Date
2026-10-25

#### Context
`devdocs/p2/p2.1.txt` (Chapter 9 & 10) mandates dividing uploaded documents into semantically meaningful chunks rather than arbitrary character boundaries or fixed page splits. Standard fixed-size chunking frequently splits sentences in half, severs paragraphs from their section titles, and breaks the logical context required by downstream LLMs during Retrieval-Augmented Generation (RAG).

#### Decision
1. Implement a **Heading-Aware Hierarchical Chunking Engine**:
   - Parse and respect markdown headings (`#`, `##`, `###`), document section headers, and slide titles.
   - Group text under the nearest parent heading, injecting the section title into chunk metadata.
2. Parameter Standards:
   - Primary target chunk size: 512 tokens ($\approx 2,000$ characters).
   - Minimum chunk threshold: 100 tokens (suppresses fragmented noise).
   - Maximum chunk threshold: 1,024 tokens (hard safety ceiling).
3. Sliding Window Overlap:
   - Enforce a 10% to 15% token overlap (50 to 75 tokens) across consecutive chunks within the same section.
   - Clear overlap across major chapter breaks to prevent contextual contamination.
4. Boundary Hierarchy:
   - Priority 1: Markdown Headings
   - Priority 2: Paragraph Breaks (`\n\n`)
   - Priority 3: Sentence Delimiters (`. `, `! `, `? `)
   - Priority 4: Word Boundaries

#### Alternatives Considered
- Fixed 1000-character chunking: Rejected — splits coherent ideas across boundaries and produces poor retrieval precision.
- Whole-document embedding: Rejected — exceeds LLM context windows and dilutes specific answer retrieval.

#### Reason
Semantic chunking preserves complete organizational concepts, significantly boosting BM25 keyword matching and dense vector similarity scores during hybrid search.

#### Impact
Member 1 authors typed interfaces (`BaseSemanticChunker`, `SemanticChunkSpec`). Member 2 implements the production chunking service.

#### Status
ACCEPTED

---

### ADR-033 — Dual-Tier Embedding Model Architecture (OpenAI & Local BGE) with Normalized L2 Cosine Distance

#### Date
2026-10-25

#### Context
`devdocs/p2/p2.1.txt` (Chapter 11 & 12) requires transforming semantic chunks into numerical vector embeddings stored in a vector database (`pgvector`). Enterprise deployments require flexibility between high-performance cloud embeddings and zero-cost, privacy-preserving, air-gapped local execution.

#### Decision
1. Establish a **Dual-Tier Embedding Model Strategy**:
   - **Tier 1 (Cloud Production Default)**: OpenAI `text-embedding-3-small` (1,536 dimensions, 8,191 max context, ~$0.02 per 1M tokens).
   - **Tier 2 (Local / Air-Gapped / Zero-Cost)**: BAAI `bge-small-en-v1.5` (384 dimensions, 512 max context, local CPU/GPU execution via HuggingFace SentenceTransformers).
2. Normalization:
   - All embedding vectors must be $L_2$-normalized ($||\mathbf{v}||_2 = 1.0$) upon generation.
3. Indexing & Metric:
   - Use `vector_cosine_ops` (Cosine Distance) with HNSW indexes in `pgvector` (`m=16`, `ef_construction=64`).
4. Tenant Isolation:
   - All vector queries must include multi-tenant filter constraints (`organization_id = :org_id`).

#### Alternatives Considered
- Cloud-only (OpenAI exclusively): Rejected — prevents on-premises enterprise deployments with strict data residency mandates.
- High-dimensional large models (3,072 dims): Rejected as default due to increased RAM footprint in PostgreSQL and slower vector query latency.

#### Reason
The dual-tier approach guarantees enterprise privacy compliance while maintaining state-of-the-art semantic retrieval quality.

#### Impact
Member 1 provides typed contracts (`BaseEmbeddingGenerator`, `EmbeddingVectorSpec`). Member 4 configures local model artifact caching. Member 2 integrates the generation pipeline.

#### Status
ACCEPTED

---

### ADR-034 — Asynchronous Ingestion Task Pipeline, State Machine, and Exponential Backoff Retry Policy

#### Date
2026-10-25

#### Context
`devdocs/p2/p2.1.txt` (Chapters 13 & 14) mandates asynchronous processing of uploaded documents to avoid blocking the user-facing web interface. Heavy PDF parsing, OCR image processing, and embedding generation can take anywhere from 2 seconds to several minutes depending on document volume. Transient failures (OCR timeout, LLM rate limit) must be handled gracefully without human intervention.

#### Decision
1. Adopt a **10-State Asynchronous Ingestion State Machine**:
   - `PENDING` -> `EXTRACTING` -> (`OCR_PROCESSING` optional) -> `NORMALIZING` -> `CHUNKING` -> `EMBEDDING` -> `INDEXING` -> `COMPLETED`.
   - On error: Transition to `FAILED`.
   - Automatic retry: Transition to `RETRYING` if `retry_count < 3`.
2. Asynchronous Queue Architecture:
   - Dedicated Redis queues: `ai_ingestion_queue` (extraction/OCR) and `ai_embedding_queue` (vector calculation).
3. Exponential Backoff Retry Formula:
   $$\text{Delay} = 2^{\text{attempt}} \times 5\text{ seconds} \quad (\text{Attempt 1: } 10\text{s}, \text{Attempt 2: } 20\text{s}, \text{Attempt 3: } 40\text{s})$$
4. Dead-Letter Quarantine:
   - Jobs exceeding 3 failed attempts remain in terminal `FAILED` state with complete stack traces, enabling manual admin review and retry via `POST /api/v1/ingestion/retry/{id}`.

#### Alternatives Considered
- In-process BackgroundTasks: Rejected — crashes if the web server restarts and lacks queue visibility/retries.
- Immediate retries without backoff: Rejected — exacerbates rate limits on external LLM APIs.

#### Reason
Asynchronous worker isolation with exponential backoff ensures robust, fault-tolerant ingestion that scales horizontally under enterprise load.

#### Impact
Member 1 establishes domain interfaces (`BaseIngestionCoordinator`, `IngestionPipelineProgress`). Member 2 implements Celery worker tasks. Member 3 builds the Ingestion Dashboard.

#### Status
ACCEPTED

---

### ADR-035 — Hybrid Retrieval Fusion Strategy: Reciprocal Rank Fusion (RRF) over Weighted Score Summation

#### Date
2026-10-26

#### Context
`devdocs/p2/p2.2.txt` (Chapters 3, 6 & 7) mandates combining dense semantic vector search with sparse keyword search. Dense vector search excels at conceptual similarity but struggles with exact alphanumeric identifiers, error codes, and specific names. Sparse full-text search (BM25 / PostgreSQL `tsvector`) excels at exact term matches but fails on synonyms or semantic paraphrase. Combining the two requires a robust rank aggregation strategy.

#### Decision
1. Implement **Reciprocal Rank Fusion (RRF)** to combine dense and sparse search results:
   $$\text{RRF\_Score}(d) = \frac{w_{\text{dense}}}{k + r_{\text{dense}}(d)} + \frac{w_{\text{sparse}}}{k + r_{\text{sparse}}(d)}$$
   with default smoothing parameter $k = 60$, $w_{\text{dense}} = 0.65$, and $w_{\text{sparse}} = 0.35$.
2. Candidate Retrieval:
   - Retrieve top $N_1 = 30$ chunks from dense vector similarity (pgvector cosine distance).
   - Retrieve top $N_2 = 30$ chunks from sparse full-text search (`tsvector @@ websearch_to_tsquery`).
   - Merge candidate pool and sort by descending $\text{RRF\_Score}$.
3. Fallback:
   - If either search method returns zero results (e.g. specialized acronyms with no vector neighbor or non-lexical terms), the opposing method gracefully populates the candidate pool without dividing by zero.

#### Alternatives Considered
- Direct Score Summation (normalized vector score + BM25 score): Rejected because BM25 scores are unbounded $[0, \infty)$ while cosine similarities are bounded $[-1, 1]$, causing score distortion across diverse queries.
- Pure Vector Search: Rejected due to degradation on exact serial numbers, acronyms, and specialized code identifiers.

#### Reason
RRF is scale-invariant, hyperparameter-resilient, and empirically proven in information retrieval literature to outperform linear score combinations across heterogeneous search backends.

#### Impact
Member 1 specifies `BaseHybridSearchService` and `RRFRetrievalPipeline`. Member 2 implements the SQL query generator and rank aggregator. Member 4 conducts latency profiling.

#### Status
ACCEPTED

---

### ADR-036 — Multi-Factor Neural Reranking and Context Relevance Weighting

#### Date
2026-10-26

#### Context
`devdocs/p2/p2.2.txt` (Chapter 8) specifies that raw hybrid search returns dozens of candidate chunks that vary widely in document freshness, organization priority, and contextual density. Feeding raw chunks directly into the LLM increases token costs and risks attention dilution ("Lost in the Middle").

#### Decision
1. Implement a **Two-Tier Reranking Pipeline**:
   - **Tier 1 (Cross-Encoder / Bi-Encoder Scoring)**: Computes fine-grained semantic interaction score $S_{\text{semantic}}(Q, C) \in [0, 1]$.
   - **Tier 2 (Enterprise Metadata Heuristics)**:
     - Document Freshness $S_{\text{freshness}} = \exp(-\Delta t / 180\text{ days})$.
     - Scoped Alignment $S_{\text{scope}} \in \{0.0, 0.5, 1.0\}$ prioritizing the user's active department and project.
2. Composite Rerank Score:
   $$\text{Score}_{\text{final}} = 0.70 \cdot S_{\text{semantic}} + 0.15 \cdot S_{\text{freshness}} + 0.15 \cdot S_{\text{scope}}$$
3. Truncation: Select top $K = 5$ scoring chunks for prompt context assembly.

#### Alternatives Considered
- Heavy Cross-Encoder on all 1,000+ document chunks: Rejected due to unacceptable latency ($> 2,000\text{ ms}$).
- No Reranking (pass top-5 RRF directly): Rejected because RRF does not account for document freshness or enterprise departmental relevance.

#### Reason
Two-tier reranking bounds latency to $< 100\text{ ms}$ while ensuring top-tier context precision for the LLM.

#### Impact
Member 1 provides `BaseReranker` contract. Member 2 integrates reranking into `RAGService`. Member 4 benchmarks reranking throughput.

#### Status
ACCEPTED

---

### ADR-037 — Context Assembly, Zero-Hallucination Guardrails, and Verifiable Citation Provenance

#### Date
2026-10-26

#### Context
`devdocs/p2/p2.2.txt` (Chapters 9, 10, 11, 13 & 14) mandates that every generated response must be grounded in enterprise documents, include verifiable citations (document title, page, section, chunk ID), and strictly refrain from hallucinating policies when knowledge is absent.

#### Decision
1. **Context Window Assembly**:
   - Token budget: Maximum 3,000 tokens for retrieved chunks.
   - Chunks are assembled with explicit provenance envelopes:
     `[Source <ID>: <Document Title> | Page <P> | Section <S>]\n<Content>`
2. **Strict Grounding Prompt**:
   - The LLM is conditioned with a negative constraint: *"Answer the user's question solely based on the provided context. If the context does not contain sufficient facts to answer the question, state clearly: 'I do not have sufficient information in the organization knowledge base to answer this question.' Never invent or extrapolate policies."*
3. **Confidence Scoring & Circuit Breaker**:
   - If mean chunk relevance score $\text{Confidence} < 0.35$, bypass LLM synthesis and immediately return the standardized out-of-knowledge response, saving tokens and eliminating hallucination risk.
4. **Citation Extraction & Verification**:
   - The engine automatically extracts citation markers from the response, validates them against the provided context chunks, and enriches the API response with full metadata (document title, version, page, section, excerpt, download/preview URL).

#### Alternatives Considered
- Permitting LLM parametric general knowledge: Rejected — enterprise knowledge compliance requires strict grounded attribution.
- Post-hoc citation search: Rejected — prone to misattribution and slow latency.

#### Reason
Grounded prompting coupled with confidence thresholding guarantees enterprise trust, auditability, and verifiable provenance for corporate compliance.

#### Impact
Member 1 delivers `BaseContextBuilder`, `BaseCitationFormatter`, and prompt templates. Member 2 implements citation parsing and database persistence. Member 3 builds the Citation Drawer UI.

#### Status
ACCEPTED

---

### ADR-038 — Deterministic Agentic Task Planning & Directed Acyclic Graph (DAG) Workflow Orchestration

#### Date
2026-10-27

#### Context
`devdocs/p2/p2.3.txt` (Chapters 3, 6 & 8) specifies that enterprise user requests frequently encompass complex, multi-step operations (e.g. "Find all marketing reports from last month, summarize them, and notify the team"). Relying on unconstrained recursive LLM tool-calling loops ("ReAct loops") leads to non-deterministic execution paths, infinite loops, high token consumption, and unpredictable latencies in an enterprise environment.

#### Decision
1. Implement a **Deterministic DAG Task Planner**:
   - The user request is parsed into an explicit, structured `TaskPlan` composed of ordered `TaskStep` nodes.
   - Each step specifies `step_id`, target `tool_name`, validated `input_parameters`, and explicit `dependencies` ($step_j \in \text{deps}(step_i) \implies j < i$).
2. Topological Sequential & Parallel Execution:
   - Independent steps are eligible for parallel execution where thread-safe.
   - Dependent steps receive outputs from prerequisite steps passed via a shared `WorkflowExecutionContext`.
3. Circuit Breakers:
   - Maximum 10 steps per workflow.
   - Per-step execution timeout of 10.0 seconds.
   - Workflow overall execution deadline of 30.0 seconds.

#### Alternatives Considered
- Unconstrained autonomous ReAct loops: Rejected due to risk of unbounded token cost and infinite tool calling loops.
- Static hardcoded workflow scripts: Rejected because enterprise users require dynamic combinations of tools.

#### Reason
DAG-based planning gives full transparency, predictability, auditable task state, and clean dependency management for multi-step enterprise automation.

#### Impact
Member 1 implements `BaseAssistantPlanner` and `TaskPlan` contracts. Member 2 develops the backend `WorkflowOrchestrator`. Member 3 visualizes the execution graph in `WorkflowVisualizer.tsx`.

#### Status
ACCEPTED

---

### ADR-039 — Dynamic Enterprise Tool-Calling Registry with Enforced RBAC Boundaries

#### Date
2026-10-27

#### Context
`devdocs/p2/p2.3.txt` (Chapters 7 & 14) mandates that the AI Assistant interact with platform services through modular tools (Document, Semantic Search, Analytics, Report, User, Project, Notification). An AI Assistant must never bypass the security model or execute actions beyond the calling user's permissions.

#### Decision
1. **Unified Tool Interface (`BaseTool`)**:
   - Every tool declares: `name`, `description`, `category`, `required_permissions`, `is_destructive`, and `parameters_schema`.
2. **Pre-Execution Security & Tenancy Validation**:
   - Prior to tool execution, the runner checks the user's JWT security context against `required_permissions`.
   - All tool queries automatically enforce the caller's `organization_id` tenant boundary.
3. **Core Platform Tool Registry**:
   - `DocumentTool`: Retrieval and metadata inspection of tenant documents.
   - `SearchTool`: Hybrid RAG search execution.
   - `AnalyticsTool`: System and organizational KPI queries.
   - `ReportTool`: Structured multi-format report synthesis.
   - `UserTool`: User profile and team roster lookups.
   - `ProjectTool`: Project metadata, workspace association, and status.
   - `NotificationTool`: Delivery of alerts and event notices.

#### Alternatives Considered
- Direct database mutation from LLM prompts: Strongly rejected as a severe SQL injection and privilege escalation vector.
- External function calling without RBAC checks: Rejected because user permission boundaries must be enforced inside the application service layer.

#### Reason
Formal tool contracts ensure least-privilege execution, total tenant isolation, and modularity for adding future tools.

#### Impact
Member 1 specifies `BaseTool` and `BaseToolRegistry`. Member 2 implements core tools connecting to services. Member 4 conducts tool security auditing.

#### Status
ACCEPTED

---

### ADR-040 — Two-Phase Commit Human-in-the-Loop (HITL) Approval Gating for Destructive Operations

#### Date
2026-10-27

#### Context
`devdocs/p2/p2.3.txt` (Chapter 10) mandates that destructive, irreversible, or policy-critical operations (e.g. deleting documents, removing users, modifying tenant permissions, archiving workspaces) must not execute autonomously without human review and confirmation.

#### Decision
1. **Safety Classification**:
   - Tools and actions are tagged as either `SAFE_AUTO` or `CRITICAL_CONFIRMATION_REQUIRED`.
2. **Two-Phase Approval Workflow**:
   - **Phase 1 (Preparation & Hold)**: When a task planner identifies a destructive step, the workflow sets status to `WAITING_APPROVAL`, creates an `AssistantApproval` record with status `PENDING`, and halts execution.
   - **Phase 2 (Review & Commit)**:
     - If the authorized reviewer submits an `APPROVE` decision, execution resumes, the tool mutates state, and status updates to `COMPLETED`.
     - If the reviewer submits a `REJECT` decision, the workflow terminates immediately with status `CANCELLED` and logs the rejection reason.
3. **Expiration**:
   - Unreviewed approval requests expire after 24 hours to prevent stale execution of outdated intents.

#### Alternatives Considered
- Optimistic execution with post-hoc rollback: Rejected — deleted files or removed permissions cannot always be cleanly rolled back and cause user distress.
- Completely disallowing destructive actions via AI: Rejected — enterprise administrators require assisted batch operations with oversight.

#### Reason
Guarantees human accountability, zero unintended data loss, compliance with enterprise risk governance, and audit traceability.

#### Impact
Member 1 provides approval contracts. Member 2 implements approval ORM tables and endpoints. Member 3 builds the `ApprovalModal.tsx` UI component.

#### Status
ACCEPTED

---

### ADR-041 — Enterprise Entity & Relationship Ontology Model, Normalization & Disambiguation Strategy

#### Date
2026-10-27

#### Context
`devdocs/p2/p2.4.txt` (Chapters 4, 5, 7 & 8) specifies that enterprise knowledge consists of heterogeneous, interconnected entities across organizational (Organization, Department, Team, Employee), knowledge (Document, Policy, SOP, Meeting, Report), operational (Project, Task, Milestone, Risk, Decision), and technical concepts. Without a strict ontology, named entity recognition generates noisy, fragmented, and duplicate graph nodes (e.g. "K8s", "Kubernetes", "kubernetes-cluster" referring to the same technology; or "HR", "People Ops", "Human Resources").

#### Decision
1. **Four-Tier Enterprise Ontology**:
   - Categorize entities into standardized `EntityType` enums: `ORGANIZATION`, `DEPARTMENT`, `TEAM`, `EMPLOYEE`, `DOCUMENT`, `POLICY`, `SOP`, `MEETING`, `REPORT`, `PROJECT`, `TASK`, `MILESTONE`, `RISK`, `DECISION`, `TECHNOLOGY`, `TOPIC`.
   - Enforce canonical relationship verbs (`WORKS_IN`, `LEADS`, `PARTICIPATES_IN`, `AUTHORED`, `CONTAINS`, `REFERENCES`, `APPLIES_TO`, `DEPENDS_ON`, `DISCUSSED`, `EXPERT_IN`).
2. **Entity Normalization & Disambiguation Pipeline**:
   - Normalize entity names via NFKC Unicode normalization, whitespace trimming, and case standardization.
   - Maintain alias dictionary for common organizational acronyms and product names.
   - Use token and fuzzy Levenshtein similarity ($> 0.88$ threshold) to match incoming entities against existing tenant entities before creating new nodes.
   - Increment `mention_count` and merge source document IDs into existing entity nodes upon duplicate detection.
3. **Multi-Tenant Boundary Constraint**:
   - Every node and edge is partition-scoped with `organization_id`. Normalization and deduplication never cross tenant boundaries.

#### Alternatives Considered
- Open-domain unconstrained entity types: Rejected — leads to explosive graph sparsity and invalid traversal paths.
- External graph-store microservice (Neo4j / Neptune) for MVP: Deferred — introduces extra operational complexity, operational cost, and separate authentication layers during initial development; PostgreSQL relational adjacency modeling handles the MVP scale with zero extra container footprint.

#### Reason
A controlled enterprise ontology combined with canonical entity normalization guarantees high graph density, semantic coherence, and accurate multi-hop reasoning.

#### Impact
Member 1 specifies ontology contracts (`EntityType`, `RelationType`, `BaseEntityExtractor`). Member 2 implements normalization and persistence in `kg_entities`. Member 3 renders type-specific badges and icons in the Knowledge Explorer UI.

#### Status
ACCEPTED

---

### ADR-042 — Graph-Enhanced Retrieval-Augmented Generation (GraphRAG) with Contextual Subgraph Expansion

#### Date
2026-10-27

#### Context
`devdocs/p2/p2.4.txt` (Chapter 14) mandates that KEEP evolve beyond standard vector semantic search by incorporating Knowledge Graph relationships into RAG query synthesis. Pure vector search retrieves text chunks in isolation, missing structural connections like departmental policy dependencies, project contributors, or cross-document hierarchies.

#### Decision
1. **Hybrid Graph-RAG Dual-Retrieval Pipeline**:
   - **Step 1 (Entity Resolution)**: Extract key entities from the user query using fast dictionary matching and lightweight NER.
   - **Step 2 (Local Subgraph Traversal)**: For each identified entity, query the Knowledge Graph to extract its 1-to-2 hop semantic neighborhood (direct relationships, connected projects, parent departments, linked documents).
   - **Step 3 (Context Fusion & Assembly)**: Serialize the extracted relational triples into a concise, human-readable **Knowledge Graph Context Envelope**:
     ```text
     [KNOWLEDGE GRAPH RELATIONSHIPS]
     - Project Alpha (PROJECT) CONTAINS Architecture Spec (DOCUMENT)
     - Security Policy v2 (POLICY) APPLIES_TO Engineering (DEPARTMENT)
     - Alice (EMPLOYEE) EXPERT_IN Cybersecurity (TOPIC)
     ```
   - **Step 4 (Prompt Augmentation)**: Inject the Knowledge Graph Context Envelope alongside vector passage chunks into the LLM synthesis prompt.
2. **Subgraph Token Budget**:
   - Cap the subgraph context to a maximum of 20 relevant triples or 500 tokens to preserve the majority of the context window for retrieved document passages.

#### Alternatives Considered
- Graph-only retrieval without vector search: Rejected — fails to capture nuanced narrative text and unstructured explanations.
- Dumping entire graph into prompt: Rejected — exceeds LLM token limits and causes attention confusion.

#### Reason
Graph-RAG provides structural awareness, provenance links, and organizational hierarchy context that vector similarity alone cannot deliver.

#### Impact
Member 1 provides `BaseGraphRAGAugmenter` contract. Member 2 integrates subgraph retrieval into `RAGService`. Member 4 benchmarks GraphRAG answer quality and latency.

#### Status
ACCEPTED

---

### ADR-043 — Multi-Hop Graph Traversal, Recursive Impact Analysis, and PageRank Expertise Scoring

#### Date
2026-10-27

#### Context
`devdocs/p2/p2.4.txt` (Chapters 10, 12 & 13) requires KEEP to answer complex organizational questions such as: "Which projects depend on this policy?", "Who are the subject matter experts on Kubernetes?", and "What is the blast radius of modifying this SOP?". These operations require traversing multi-hop dependency chains and calculating contributor centrality.

#### Decision
1. **Relational Adjacency Traversal via PostgreSQL Recursive CTEs**:
   - Implement breadth-first multi-hop graph walks in PostgreSQL using Recursive Common Table Expressions with array cycle detection (`NOT (target.id = ANY(path))`) and configurable `max_depth` ($1 \le \text{depth} \le 3$).
2. **Impact Analysis Engine**:
   - Given a root entity (e.g. Policy or Component), recursively traverse outgoing dependency relations (`DEPENDS_ON`, `APPLIES_TO`, `GOVERNED_BY`, `BLOCKS`).
   - Group downstream affected entities by type (Departments, Projects, Tasks) with path distance and impact severity score.
3. **Expertise Discovery Algorithm (Weighted Contributor Centrality)**:
   - Calculate expertise score for employees based on multi-relational contributions to a topic or domain:
     $$\text{Score}(u, T) = 3.0 \cdot \text{AuthoredDocs}(u, T) + 2.0 \cdot \text{ProjectContributions}(u, T) + 1.5 \cdot \text{MeetingMentions}(u, T)$$
   - Return ranked contributors with verified source artifact citations.

#### Alternatives Considered
- In-memory graph loading (NetworkX) on every request: Rejected — poor scaling on large entity sets and high memory overhead per worker process.
- Storing precomputed impact matrices: Rejected — graph is dynamic and updates incrementally as documents are uploaded.

#### Reason
PostgreSQL Recursive CTEs execute fast ($< 50\text{ ms}$ for 3-hop traversals over 100k edges) while keeping persistence atomic with zero distributed sync issues.

#### Impact
Member 1 defines traversal interfaces (`GraphQuerySpec`, `ImpactAnalysisResult`, `ExpertiseRank`). Member 2 implements SQL CTE generators. Member 3 builds the `ImpactAnalysisWidget.tsx` and `ExpertiseDirectory.tsx` UI components.

#### Status
ACCEPTED

---

### ADR-044 — Multi-Dimensional Knowledge Health Scoring (KHS) & Decomposition Model

#### Date
2026-10-28

#### Context
`devdocs/p2/p2.5.txt` (Chapters 2, 9, 13) mandates the calculation of an objective, actionable **Knowledge Health Score (KHS)** (0–100) representing institutional knowledge vitality, coverage, freshness, quality, and redundancy across departments.

#### Decision
1. Implement a decomposed linear health scoring model:
   $$KHS = \min(100, \max(0, 0.30 \cdot C_{cov} + 0.25 \cdot C_{fresh} + 0.25 \cdot C_{qual} + 0.20 \cdot C_{ret} - 0.15 \cdot C_{dup}))$$
2. Decompose into 4 transparent tiers: Excellent ($\ge 85$), Good ($70-84$), Fair ($50-69$), and At Risk ($< 50$).
3. Persist point-in-time calculation snapshots in `analytics_snapshots` with a 300-second Redis cache to eliminate redundant computation.

#### Alternatives Considered
- Black-box LLM scoring: Rejected — inconsistent outputs, unexplainable to leadership, non-deterministic.
- Single metric (e.g. document count only): Rejected — volume does not imply freshness, completeness, or retrieval quality.

#### Reason
Decomposition allows leadership to instantly pinpoint *why* a score dropped (e.g., stale HR documentation or high redundancy in Marketing).

#### Impact
Member 1 provides mathematical formulation and test contracts. Member 2 implements DB aggregations and snapshots. Member 3 builds the executive health gauge and breakdown cards.

#### Status
ACCEPTED

---

### ADR-045 — Hybrid Statistical Time-Series Forecasting & Z-Score Anomaly Detection

#### Date
2026-10-28

#### Context
`devdocs/p2/p2.5.txt` (Chapters 7, 8) requires forecasting future organizational growth (documents, storage runway, AI query volume) and alerting on operational anomalies (sudden drop in collaboration, abnormal deletion bursts, spike in retrieval failures).

#### Decision
1. **Statistical OLS Linear Trend Regression with Standard Error Envelopes**:
   - Compute slope $\beta$ and intercept $\alpha$ over a rolling 30-day baseline to forecast 30-, 60-, and 90-day horizons with 95% confidence intervals ($\pm 1.96 \cdot \text{SE}$).
   - Calculate storage capacity runway (days until 85% and 95% threshold breaches).
2. **Dynamic Z-Score Anomaly Detection**:
   - Maintain rolling mean $\mu$ and standard deviation $\sigma$ across activity indicators.
   - Flag events with $Z \ge 2.0$ (Medium), $Z \ge 2.5$ (High), and $Z \ge 3.0$ (Critical).

#### Alternatives Considered
- Heavy deep learning forecasting (e.g. Prophet / LSTM): Rejected — excessive CPU/GPU footprint and operational latency for sub-second dashboard rendering.
- Static threshold alerts: Rejected — unable to adapt to different tenant sizes and growing organizations.

#### Reason
Statistical OLS regression and Z-score testing provide sub-millisecond execution, high interpretability, and robust performance on multi-tenant databases.

#### Impact
Member 1 provides forecasting and anomaly contracts. Member 2 implements analytical services. Member 3 builds predictive charts with confidence bounds.

#### Status
ACCEPTED

---

### ADR-046 — Prioritized Strategic AI Recommendations Engine & Multi-Tenant Decision Support

#### Date
2026-10-28

#### Context
`devdocs/p2/p2.5.txt` (Chapters 12, 14, 16) specifies that KEEP must generate actionable, prioritized organizational recommendations (e.g. archiving stale documents, merging duplicate knowledge, filling uncovered department knowledge gaps, resolving orphan graph entities).

#### Decision
1. **Priority Index ($PI$) Algorithm**:
   $$PI = \frac{\text{Impact Score} (1-10) \times 1.5}{\text{Effort Score} (1-5)}$$
   Sort active recommendations descending by $PI$ to ensure leadership focuses on high-impact, low-effort wins.
2. **Lifecycle State Machine**:
   Recommendations transition through `ACTIVE` $\rightarrow$ `APPLIED` or `DISMISSED` with action audit payloads.
3. **Automated Executive Briefing Synthesis**:
   Synthesize concise, multi-bullet executive summaries summarizing weekly trend deltas, top risks, and high-priority recommendations.

#### Alternatives Considered
- Unranked recommendations: Rejected — causes alert fatigue for executive users.
- Permanent static suggestions: Rejected — suggestions must be dynamically updated as documents are uploaded or resolved.

#### Reason
Priority Index ranking and actionable state transitions transform raw analytics into a proactive operational management system.

#### Impact
Member 1 specifies recommendation taxonomy and contracts. Member 2 provides ORM models, migration, and CRUD endpoints. Member 3 implements the interactive recommendation panel.

#### Status
ACCEPTED

---

### ADR-047 — Pluggable Multi-Tenant Enterprise Connector Lifecycle & Integration Gateway Architecture

#### Date
2026-10-28

#### Context
`devdocs/p3/p3.1.txt` (Chapters 3, 5, 15) mandates that KEEP evolve into a centralized enterprise intelligence hub by securely integrating with external SaaS platforms (Google Drive, Microsoft 365, GitHub, Slack, Jira, Notion, Confluence). The system requires a standardized connector lifecycle and gateway architecture to isolate external vendor APIs from internal RAG processing.

#### Decision
1. **Pluggable Base Connector Adapter Pattern**:
   - Define abstract interface `BaseConnectorAdapter` enforcing uniform lifecycle methods: `authenticate()`, `test_connection()`, `discover_resources()`, `fetch_resource_content()`, and `disconnect()`.
   - Each SaaS integration implements this adapter, isolating platform-specific SDKs, rate limits, and pagination details.
2. **Deterministic Lifecycle State Machine**:
   - Connectors transition across verified states: `CONFIGURED` $\rightarrow$ `AUTHENTICATING` $\rightarrow$ `CONNECTED` $\rightarrow$ `SYNCING` $\rightarrow$ `HEALTHY` (or `DEGRADED` / `ERROR` upon communication failure).
3. **Multi-Tenant Gateway Routing**:
   - All connector instances and sync jobs are strictly isolated by `organization_id`.

#### Alternatives Considered
- Direct ad-hoc API calls within RAG pipelines: Rejected — creates brittle vendor couplings, complicates credential rotation, and breaks rate-limit controls.
- Third-party managed ETL services (e.g. Fivetran): Rejected — compromises customer data sovereignty and lacks custom KEEP permission mapping.

#### Reason
Standardized adapter contracts ensure any future SaaS platform can be added without modifying core RAG, vector search, or database models.

#### Impact
Member 1 provides abstract contracts and mock test adapter. Member 2 implements REST endpoints and persistent ORM models. Member 3 builds the Integration Dashboard. Member 4 monitors connector health.

#### Status
ACCEPTED

---

### ADR-048 — Standardized External Document Normalization, Metadata Mapping & Incremental Change Detection Engine

#### Date
2026-10-28

#### Context
`devdocs/p3/p3.1.txt` (Chapters 7, 8, 9, 10) mandates that diverse external formats (Google Docs, Slack message threads, GitHub markdown repositories, Jira tickets) be converted into a uniform KEEP document schema while detecting incremental updates to avoid redundant re-embedding.

#### Decision
1. **Canonical Normalized Document Envelope**:
   - Standardize all ingested external resources into `NormalizedDocument` tracking: `external_id`, `source_platform`, `source_url`, `title`, `raw_content`, `mime_type`, `author`, `department`, `tags`, timestamps, and permissions.
2. **Cryptographic Delta Fingerprinting**:
   - Compute SHA-256 content checksums $\text{SHA-256}(\text{Raw Content} + \text{MIME})$.
   - Contrast against previous sync state to categorize resources as `NEW`, `UPDATED`, `DELETED`, or `UNCHANGED`.
3. **Incremental Sync Window**:
   - For platforms supporting modified timestamp queries, request only resources modified since `last_sync_at - 300\text{s}` (5-minute safety buffer against clock skew).

#### Alternatives Considered
- Full re-indexing on every sync: Rejected — unsustainable API consumption and vector embedding compute costs for enterprises with > 100k files.
- Relying solely on external version numbers: Rejected — platforms like Slack and GitHub do not provide unified file version integers.

#### Reason
SHA-256 fingerprinting guarantees 100% accurate change detection across all platforms with zero unnecessary chunking or re-embedding.

#### Impact
Member 1 defines normalizer contracts and SHA-256 change detector. Member 2 integrates with `DocumentService` and `document_chunks`. Member 3 surfaces sync delta statistics on the dashboard.

#### Status
ACCEPTED

---

### ADR-049 — Token-Encrypted Multi-Provider Authentication, Secret Storage & Cross-Platform RBAC Permission Translation

#### Date
2026-10-28

#### Context
`devdocs/p3/p3.1.txt` (Chapters 6, 13) requires supporting multiple authentication schemes (OAuth 2.0, Personal Access Tokens, API Keys, Service Accounts) and preserving source platform access controls so users cannot search content they do not have rights to view.

#### Decision
1. **Authenticated Symmetric Secret Encryption at Rest**:
   - Encrypt all refresh tokens, client secrets, and API keys using Fernet (AES-128-CBC with HMAC-SHA256 authenticated encryption) seeded from the organization application key. Plaintext credentials are never persisted.
2. **Cross-Platform Access Control Mapping**:
   - Map external permission levels (`Admin`, `Editor`, `Viewer`, `Channel Member`) into standard KEEP RBAC roles (`OrgAdmin`, `Manager`, `Member`, `Guest`).
   - Store `allowed_roles` on normalized records to enforce tenant-level search isolation.
3. **Automated Token Refresh**:
   - The authentication service checks access token expiry before sync jobs and triggers refresh flows transparently.

#### Alternatives Considered
- Storing tokens in plaintext in PostgreSQL: Rejected — severe security vulnerability violating enterprise compliance standards (SOC 2, ISO 27001).
- Discarding external permissions: Rejected — causes serious privilege escalation by allowing unauthorized employees to view sensitive executive docs in AI search.

#### Reason
Token encryption and role mapping ensure enterprise-grade security and zero-trust data sovereignty across all external connections.

#### Impact
Member 1 specifies `BaseAuthenticator` and `AuthCredentials` contracts. Member 2 implements encrypted database columns and OAuth token exchange. Member 3 builds secure credential configuration drawers.

#### Status
ACCEPTED

