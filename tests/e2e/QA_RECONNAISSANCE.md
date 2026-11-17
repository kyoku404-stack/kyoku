# KEEP Platform — Autonomous QA Reconnaissance Report (`QA_RECONNAISSANCE.md`)
**Date:** 2026-11-09  
**Target Environment:** Local Development / Isolated QA  
**Agent Role:** KEEP Autonomous QA Lead  
**Governing Specification:** `KEEP Platform — Antigravity Autonomous QA & E2E Verification Master Plan (v2.0.0)`  
**Repository Branch:** `agent/ai-lead/feature/phase-3.7-final-qa-security-audit-production-release`  
**Commit SHA:** `1637b8d71b2505d490f1c5a4ecf332333f9648d8`  
**Repository Health:** GREEN (Phase 1.1–1.10, Phase 2.1–2.5, Phase 3.1–3.7 100% Complete)  

---

## 1. Repository Context & Environment Manifest

| Property | Value / Configuration | Evidence Source |
| :--- | :--- | :--- |
| **Repository Root** | `C:\Users\Kaustubh Dhone\kyoku` | System workspace root |
| **Frontend Framework** | React 18.3, TypeScript 5.5, Vite 5.4, Tailwind CSS 3.4 | `frontend/package.json`, `frontend/vite.config.ts` |
| **Frontend Dev Port** | **Port 3000** (`host: 0.0.0.0`, proxy `/api` -> `http://localhost:8000`) | `frontend/vite.config.ts#L15-L23` |
| **Frontend Package Manager** | `npm` (verified via `frontend/package-lock.json`) | `frontend/package-lock.json` |
| **Backend Framework** | FastAPI (0.110+), Pydantic v2 (2.6+), Python 3.12+ | `backend/requirements.txt`, `pyproject.toml` |
| **Backend Dev Port** | **Port 8000** (`host: 0.0.0.0`) | `backend/app/core/config.py#L24-L25` |
| **Primary Relational DB** | PostgreSQL 16 + `pgvector` (`keep_db`, port 5432) | `docker-compose.yml`, `backend/app/core/config.py` |
| **Caching & Broker** | Redis 7 (`keep-redis`, port 6379) | `docker-compose.yml` |
| **Migrations Engine** | Alembic (1.13+) — Current Head: `1b2c3d4e5f6a` | `backend/migrations/versions/` |
| **E2E Automation** | Playwright (`@playwright/test` 1.63.0) | `tests/e2e/playwright.config.ts` |

---

## 2. Confirmed Frontend Routes & Components

Verified against `frontend/src/routes/paths.ts` and `frontend/src/routes/index.tsx`:

| Route Path | Associated Page Component | Primary Purpose & Features |
| :--- | :--- | :--- |
| `/` | `HomePage` | Application root overview and system summary |
| `/dashboard` | `DashboardPage` | Executive telemetry, quick actions, KPI widgets |
| `/auth/login` | `LoginPage` | User login, JWT token acquisition, session start |
| `/auth/register` | `RegisterPage` | Tenant organization registration & owner account |
| `/auth/forgot-password` | `ForgotPasswordPage` | Password reset dispatch token form |
| `/auth/reset-password` | `ResetPasswordPage` | Token-based password reset confirmation |
| `/profile` | `ProfilePage` | User preferences, avatar, light/dark theme switch |
| `/organization` | `OrganizationPage` | Organization metadata, tenant profile, domain whitelist |
| `/organization/setup` | `OrgSetupPage` | Post-registration organization onboarding wizard |
| `/organization/settings` | `OrgSettingsPage` | Administrative tenant security & retention policies |
| `/departments` | `DepartmentsPage` | Department CRUD, head assignment, member counts |
| `/teams` | `TeamsPage` | Team groupings, department mapping, avatars |
| `/projects` | `ProjectsPage` | Project portfolio, Kanban board with task drag-drop |
| `/members` | `MembersPage` | Tenant member directory, role assignment, revocation |
| `/invitations/accept` | `AcceptInvitationPage` | Tokenized team member invitation acceptance |
| `/documents` | `DocumentsPage` | Knowledge document repository, filtering, detail drawer |
| `/upload` | `UploadPage` | Multimodal drag-and-drop file upload (PDF/DOCX/TXT/PNG) |
| `/ingestion` | `IngestionPage` | AI Ingestion pipeline telemetry, chunk inspection, retries |
| `/search` | `SearchPage` | Hybrid RAG search (dense vector + BM25 keyword) |
| `/chat` or `/rag` | `RAGChatPage` | RAG knowledge conversation with live source citations |
| `/assistant` | `AssistantPage` | Autonomous agent workflows, tool calling, personas |
| `/graph` | `KnowledgeGraphPage` | Interactive 2D/3D knowledge graph visualizer |
| `/intelligence` | `EnterpriseIntelligencePage` | Predictive analytics, executive forecasts, anomalies |
| `/integrations` | `IntegrationsPage` | Cloud connectors (GDrive, SharePoint, Slack, Jira) |
| `/collaboration` | `CollaborationPage` | Real-time shared team workspaces, channels, notes |
| `/security` | `SecurityGovernancePage` | DLP rules, compliance audits, PII masking oversight |
| `/workflows` | `WorkflowAutomationPage` | Visual trigger-condition-action workflow builder |
| `/plugins` | `PluginManagementPage` | Extension marketplace, sandboxed plugin management |
| `/system` | `SystemOperationsPage` | Infrastructure telemetry, cache flushing, backups |
| `/system/release` | `ProductionReleasePage` | Pre-flight readiness gauge (7 gates), SemVer release |
| `/meetings` | `MeetingsPage` | Meeting recording ingestion, transcription, action items |
| `/analytics` | `AnalyticsPage` | Historical query metrics, P95 latency distributions |
| `/audit/logs` | `AuditLogsPage` | Immutable tenant security audit trail |
| `/health` | `HealthPage` | Liveness & readiness probes |
| `/observability` | `ObservabilityPage` | Prometheus metrics & distributed tracing dashboards |
| `/access-denied` | `AccessDeniedPage` | 403 Forbidden defensive barrier page |

---

## 3. Confirmed Backend Routers & API Endpoints

Verified against `backend/app/api/v1/router.py` (30 mounted routers):

| Router Module | Route Prefix | Key Endpoints / Operations | Authorization / Tenant Scope |
| :--- | :--- | :--- | :--- |
| `auth` | `/api/v1/auth` | `/login`, `/register`, `/refresh`, `/logout`, `/me` | Public login/register; Bearer token for session |
| `users` | `/api/v1/users` | `/me`, `/{id}`, `/` | Strict `organization_id` tenancy scoping |
| `organizations` | `/api/v1/organizations`| `/`, `/current`, `/setup` | `OrgAdmin` / `SuperAdmin` boundary enforcement |
| `departments` | `/api/v1/departments` | `/`, `/{id}` | `DEPT_READ`, `DEPT_CREATE`, `DEPT_DELETE` |
| `teams` | `/api/v1/teams` | `/`, `/{id}`, `/{id}/members` | `TEAM_READ`, `TEAM_CREATE`, `TEAM_DELETE` |
| `projects` | `/api/v1/projects` | `/`, `/{id}`, `/{id}/tasks` | `PROJECT_READ`, `PROJECT_CREATE`, `PROJECT_MANAGE` |
| `invitations` | `/api/v1/invitations` | `/`, `/{token}/accept`, `/{id}/revoke`| Token validation; `INVITATION_CREATE` |
| `members` | `/api/v1/members` | `/`, `/{id}/role`, `/{id}` | `MEMBER_READ`, `MEMBER_UPDATE`, `MEMBER_REMOVE` |
| `documents` | `/api/v1/documents` | `/upload`, `/`, `/{id}`, `/{id}/versions` | `DOCUMENT_CREATE`, `DOCUMENT_READ`, `DOCUMENT_DELETE` |
| `ingestion` | `/api/v1/ingestion` | `/jobs`, `/jobs/{id}`, `/jobs/{id}/retry` | Asynchronous parser & chunking telemetry |
| `search` | `/api/v1/search` | `/hybrid`, `/semantic`, `/keyword` | `AI_SEARCH` / `SEARCH_QUERY` |
| `rag` | `/api/v1/rag` | `/query`, `/citations`, `/evaluate` | `AI_CHAT`, context injection |
| `chat` | `/api/v1/chat` | `/sessions`, `/{id}/messages`, `/stream` | **Server-Sent Events (SSE)** at `/stream` |
| `assistant` | `/api/v1/assistant` | `/conversations`, `/tools/execute` | Tool calling execution engine |
| `graph` | `/api/v1/graph` | `/entities`, `/relationships`, `/search` | `GRAPH_READ`, `GRAPH_BUILD` |
| `analytics` | `/api/v1/analytics` | `/overview`, `/queries`, `/anomalies` | `ANALYTICS_VIEW`, `ANALYTICS_EXPORT` |
| `dashboard` | `/api/v1/dashboard` | `/summary`, `/metrics` | Role-filtered executive dashboard KPIs |
| `activity` | `/api/v1/activity` | `/recent`, `/stream` | Real-time user & tenant activity feed |
| `audit` | `/api/v1/audit` | `/logs`, `/export` | `AUDIT_READ` (OrgAdmin & SuperAdmin only) |
| `notifications` | `/api/v1/notifications`| `/`, `/{id}/read`, `/preferences` | Event-driven alerts & preferences |
| `connectors` | `/api/v1/connectors` | `/`, `/{id}/sync`, `/{id}/oauth` | `CONNECTOR_VIEW`, `CONNECTOR_SYNC` |
| `collaboration` | `/api/v1/collaboration` | `/workspaces`, `/channels`, `/notes` | Multi-user team workspaces |
| `security` | `/api/v1/security` | `/dlp/rules`, `/compliance/export` | `SECURITY_VIEW`, `SECURITY_MANAGE` |
| `workflows` | `/api/v1/workflows` | `/`, `/{id}/execute`, `/{id}/toggle` | `WORKFLOW_VIEW`, `WORKFLOW_EXECUTE` |
| `plugins` | `/api/v1/plugins` | `/`, `/{id}/install`, `/{id}/execute` | `PLUGIN_VIEW`, `PLUGIN_INSTALL` |
| `system` | `/api/v1/system` | `/health`, `/metrics`, `/backups`, `/cache/flush` | `SYSTEM_VIEW`, `SYSTEM_MANAGE`, `SYSTEM_BACKUP` |
| `release` | `/api/v1/system/release`| `/readiness`, `/release`, `/releases`, `/security/audit` | `RELEASE_VIEW`, `RELEASE_DEPLOY` (90% SLA gate) |
| `health` | `/health` | `/live`, `/ready` | Public health probes |
| `metrics` | `/metrics` | `/` (Prometheus text format) | System telemetry metrics scrape |

---

## 4. Confirmed Roles, Personas & Permission Matrix

Verified in `backend/app/core/constants.py`, `backend/app/services/ai/interfaces.py`, and `frontend/src/types/permission.ts`:

### User Roles (`UserRole` Enum)
1. `SuperAdmin`: Global platform administrator; cross-organization system management, backups, and release deployments.
2. `OrgAdmin`: Tenant administrator; manages departments, teams, projects, members, invitations, settings, and connectors.
3. `Manager` / `ProjectManager`: Department/Project lead; manages workspaces, documents, workflows, and task assignments.
4. `Member`: Standard employee; searches knowledge, chats with RAG, executes tools, creates notes, and views assigned tasks.
5. `Viewer`: Read-only user. Can view and download documents, read graph nodes, and search knowledge, but **strictly denied** write, update, delete, deploy, or export operations.

### Permission Hierarchy Highlights
- **Viewer Permissions (`VIEWER_PERMISSIONS`):**
  - Allowed: `SEARCH_QUERY`, `DOCUMENT_READ`, `DOCUMENT_DOWNLOAD`, `DOCUMENT_PREVIEW`, `GRAPH_READ`, `CONNECTOR_VIEW`, `WORKSPACE_VIEW`, `SYSTEM_VIEW`, `RELEASE_VIEW`, `ANALYTICS_VIEW`.
  - Denied: `DOCUMENT_CREATE`, `DOCUMENT_UPDATE`, `DOCUMENT_DELETE`, `PROJECT_CREATE`, `TEAM_CREATE`, `DEPT_CREATE`, `USER_MANAGE`, `MEMBER_REMOVE`, `CONNECTOR_SYNC`, `WORKFLOW_EXECUTE`, `PLUGIN_INSTALL`, `SYSTEM_BACKUP`, `RELEASE_DEPLOY`, `AUDIT_READ`.
- **Member Permissions:** Inherits Viewer + `DOCUMENT_CREATE`, `DOCUMENT_UPDATE`, `DOCUMENT_VERSION`, `CHAT_QUERY`, `CHAT_STREAM`, `WORKSPACE_CREATE`, `COMMENT_CREATE`, `WORKFLOW_EXECUTE`.
- **OrgAdmin Permissions:** Inherits Manager + `ORGANIZATION_MANAGE`, `ORGANIZATION_SETTINGS`, `USER_MANAGE`, `DEPT_CREATE`, `DEPT_DELETE`, `CONNECTOR_MANAGE`, `SECURITY_MANAGE`, `AUDIT_READ`, `RELEASE_DEPLOY`.
- **SuperAdmin Permissions:** Inherits OrgAdmin + `ORGANIZATION_CREATE`, global system operations.

---

## 5. Confirmed Tenant Model & Boundary Isolation Strategy

1. **Foreign Key Tenancy Barrier:** All core tables (`users`, `documents`, `projects`, `teams`, `departments`, `chat_sessions`, `kg_entities`, `workspaces`, `workflows`, `plugins`) enforce a non-nullable `organization_id` foreign key.
2. **Authorization Engine (`AuthorizationPolicyEngine`):**
   - Step 1: Evaluates `caller_org_id == resource_org_id`.
   - If tenant mismatch occurs, immediately returns `AuthorizationDecision.deny(ErrorCode.AUTH_ORGANIZATION_MISMATCH)`.
3. **Database Scoping:** All ORM repository queries enforce explicit `where(Model.organization_id == caller.organization_id)` clauses, preventing cross-tenant data leakage even under ID enumeration.
4. **Vector & Graph Isolation:** pgvector embeddings and Knowledge Graph CTE traversals strictly filter by `organization_id`.

---

## 6. Communication Protocols & Streaming Analysis

- **Chat Streaming:** Implemented using **Server-Sent Events (SSE)** via `StreamingResponse(media_type="text/event-stream")` at `/api/v1/chat/stream`.
- **WebSockets (`ws://`):** No native FastAPI WebSocket endpoints are mounted in the backend. Real-time updates for collaboration, notifications, and activity streams operate via REST polling and optimistic client state management.
- **Background Tasks:** Document ingestion, chunking, and embedding generation execute asynchronously via FastAPI background execution and async services (`EnterpriseIngestionService`), with task tokens generated deterministically.

---

## 7. Plan-vs-Implementation Gap Analysis

| Feature in Conceptual Plan | Real Implementation in Codebase | Testing Strategy Alignment |
| :--- | :--- | :--- |
| **Native WebSocket (`ws://`) Endpoints** | Uses **Server-Sent Events (SSE)** for chat streaming and HTTP polling for updates. | Test SSE event stream reader on `/api/v1/chat/stream`; test REST polling for collaboration/notifications. |
| **External Celery Worker Process** | Integrated async ingestion engine (`backend/app/services/ingestion/`). | Verify ingestion job status transitions (`QUEUED` -> `EXTRACTING` -> `CHUNKING` -> `INDEXED`) via `/api/v1/ingestion/jobs`. |
| **Viewer Document Download** | Viewer is explicitly granted `DOCUMENT_DOWNLOAD` and `DOCUMENT_PREVIEW`. | Assert Viewer CAN download documents, but CANNOT upload, edit, or delete them. |
| **Real External Connectors (Google, Slack)** | Mocks and simulated OAuth flows in `/api/v1/connectors`. | Test mock OAuth state transitions, sync triggers, and credential secrecy without real external calls. |
| **Production Release Deployment** | Implements pre-flight scoring engine with SemVer validation and SHA-256 artifact packaging in `/api/v1/system/release`. | Test against local QA fixture; verify readiness calculation >= 90% and audit logging without touching real production clusters. |

---

## 8. Safe Local Startup, Seed & Teardown Commands

### A. Safe Startup
```powershell
# 1. Start persistence containers (Postgres + Redis)
docker compose up -d postgres redis

# 2. Run Alembic migrations to latest schema head
alembic upgrade head

# 3. Seed synthetic multi-tenant test database
python -m backend.app.db.seed

# 4. Start FastAPI Backend (Port 8000)
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# 5. Start Vite Frontend (Port 3000)
cd frontend
npm run dev
```

### B. Safe Verification Commands
```powershell
# Frontend static & type checks
cd frontend
npm run lint
npm run build

# Backend unit & integration test suites
python -m pytest tests/unit -v
python -m pytest tests/integration/test_release_endpoints.py -v

# Playwright E2E smoke & full test execution
cd tests/e2e
npx playwright test smoke.spec.ts --reporter=list
```

### C. Safe Teardown
```powershell
# Stop background processes / containers safely
docker compose down
```

