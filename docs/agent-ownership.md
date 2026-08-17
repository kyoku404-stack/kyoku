# Four-Agent Ownership Model (docs/agent-ownership.md)

This document defines the strict component ownership matrix for the four Antigravity autonomous development agents on the KEEP project.

---

## 1. Domain Ownership Matrix

| System Domain | Primary Agent Owner | Secondary Agent Owner | Directory Paths | Core Responsibilities |
| :--- | :--- | :--- | :--- | :--- |
| **Backend API & Core** | **Agent 1** (Backend/AI) | Agent 4 (DevOps) | `/backend/app/api`, `/backend/app/core` | FastAPI endpoints, Routing, Auth, Middleware, Config, Business logic |
| **AI & RAG Engine** | **Agent 1** (Backend/AI) | Agent 3 (Data) | `/backend/app/services/rag`, `/backend/app/services/ai` | Vector retrieval, RAG prompts, LLM orchestration, Citation generation |
| **Frontend Application** | **Agent 2** (Frontend) | Agent 4 (DevOps) | `/frontend/src/` | React/Next.js UI, Pages, Components, State, API client, Styling |
| **Database & Models** | **Agent 3** (Database/Data) | Agent 1 (Backend) | `/backend/app/models`, `/backend/app/db` | PostgreSQL schemas, SQLAlchemy ORM models, Alembic migrations |
| **Ingestion & Knowledge Graph** | **Agent 3** (Database/Data) | Agent 1 (Backend) | `/backend/app/services/ingestion`, `/backend/app/services/graph` | Document extraction, OCR, Chunking, Vector embedding, Graph triples |
| **DevOps & Infrastructure** | **Agent 4** (DevOps/QA) | Agent 1 (Backend) | `/docker`, `/infrastructure`, `.github/` | Docker Compose, Dockerfiles, GitHub Actions CI/CD workflows |
| **QA & Verification** | **Agent 4** (DevOps/QA) | All Agents | `/tests/` | Unit test infrastructure, Integration test suites, Playwright E2E tests |

---

## 2. Interaction & Editing Rules

1. **Primary Ownership**:
   - The Primary Agent is solely responsible for implementing feature code within their assigned directory paths.
2. **Cross-Domain Dependencies**:
   - If Agent 1 needs a new database table, Agent 1 must request the table schema from Agent 3 or log a handoff in `docs/handoffs/agent-handoffs.md`.
   - If Agent 2 requires a new API endpoint, Agent 2 must reference `docs/api/api-contract.md` and collaborate with Agent 1.
3. **Secondary Agent Role**:
   - Secondary Agents may inspect code and provide test coverage, integration checks, or infrastructure support. They must not refactor or rewrite Primary Agent code without approval.
