# KEEP — Knowledge Extraction & Enterprise Platform

> **An Enterprise-Grade, AI-Powered Knowledge Extraction, Semantic Search, and Decision-Support Ecosystem.**

---

## 1. Project Overview

**KEEP (Knowledge Extraction & Enterprise Platform)** is an advanced enterprise intelligence platform designed to bridge the gap between unstructured organizational knowledge and automated decision-making. Standard document repositories and simple RAG systems retrieve documents based on basic similarity. KEEP constructs a fully connected **Enterprise Knowledge Graph**, linking documents, users, teams, projects, departments, policies, and operational metrics.

### Key Capabilities
- **Multimodal Knowledge Ingestion**: Automated document parsing, OCR text extraction, intelligent chunking, and high-dimensional vector embedding.
- **Hybrid RAG & Semantic Search**: Combines vector similarity with BM25 keyword search, reranking, and citation-backed answer synthesis.
- **Enterprise Knowledge Graph**: Semantic relationship mapping across organizational entities.
- **AI-Powered Analytics & Executive Dashboards**: Proactive anomaly detection, operational insights, and trend forecasting.
- **Enterprise Connectors & Workflows**: Integrations with cloud storage, project tools, communication platforms, and custom plugin SDKs.
- **Zero-Trust Security & Compliance**: Strict multi-tenant isolation, Role-Based Access Control (RBAC), and immutable audit logging.

---

## 2. Official Technology Stack

- **Frontend**: Node.js 22 LTS, React / Next.js, TypeScript 5+, Tailwind CSS, Zustand / Redux Toolkit.
- **Backend API**: Python 3.12+, FastAPI, Pydantic v2, AsyncIO.
- **Database & Storage**: PostgreSQL 16 (Relational & Multi-Tenant), SQLAlchemy 2.0 ORM, Alembic migrations.
- **Vector Search & AI**: pgvector / Qdrant / Chroma vector indexing, LangChain / LlamaIndex, SentenceTransformers, OpenAI / Local LLMs / Ollama.
- **Caching & Async Workers**: Redis, Celery / Taskiq processing queue for OCR and embedding background jobs.
- **Infrastructure & Quality**: Docker, Docker Compose, GitHub Actions CI/CD, Pytest, Playwright E2E.

---

## 3. Repository Architecture & Directory Layout

```text
kyoku/
├── devdocs/                # OFFICIAL Phase 0-3 Project Specifications (Immutable Source of Truth)
├── docs/                   # Evolving Engineering Documentation
│   ├── api/                # API Contract Specifications (api-contract.md)
│   ├── database/           # Database Schema Specifications (database-schema.md)
│   ├── integration/        # Cross-Component Integration Tracking (integration-status.md)
│   ├── decisions/          # Architecture Decision Records & Assumptions (decisions.md)
│   ├── handoffs/           # Asynchronous Agent Handoff Logs (agent-handoffs.md)
│   └── agent-ownership.md  # Machine-readable 4-Agent Ownership Matrix
├── frontend/               # React / Next.js / TypeScript Frontend Workspace
├── backend/                # FastAPI Backend & Processing Engine Workspace
├── infrastructure/         # Production & Cloud Deployment Configurations
├── docker/                 # Container Dockerfiles (Dockerfile.backend, Dockerfile.frontend)
├── scripts/                # Development, Database & Operational Scripts
├── tests/                  # Automated Verification Infrastructure
│   ├── unit/               # Fast Unit Tests (Pytest / Jest)
│   ├── integration/        # Database & API Integration Tests
│   └── e2e/                # Playwright End-to-End Automated UI Verification
├── .github/                # GitHub Workflows CI/CD, PR Template, Issue Templates, CODEOWNERS
├── AGENT_RULES.md          # MANDATORY Operating Policy for Autonomous Development Agents
├── PROJECT_STATE.md        # Single Shared Status & Progress File
├── ARCHITECTURE.md         # Master Technical Architecture Blueprint
├── CONTRIBUTING.md         # Workflow, Branching & Commit Guidelines
├── docker-compose.yml      # Local Multi-Container Development Environment
├── .env.example            # Environment Variable Template (No Secrets)
└── .gitignore              # Git Ignore Safeguards
```

---

## 4. Documentation Strategy

To ensure four autonomous Antigravity agents operate safely without conflicts or knowledge decay:

1. **`devdocs/`**: Official project requirements for Phase 0 through Phase 3. **Immutable reference.**
2. **`AGENT_RULES.md`**: Strict operating policies, safety rules, and verification standards for autonomous agents.
3. **`PROJECT_STATE.md`**: Live single-source-of-truth status tracking for phase progress across all components.
4. **`ARCHITECTURE.md`**: High-level system architecture, data flows, and technology stack reference.
5. **`docs/`**: Living engineering specs (APIs, Database Schemas, Integration Status, ADRs, Agent Handoffs).

---

## 5. Four-Agent Autonomous Ownership Model

Development is partitioned across four specialized Antigravity agents working in isolated feature branches:

| Agent | Core Ownership Domain | Primary Focus |
| :--- | :--- | :--- |
| **Agent 1 — Backend / AI Infrastructure** | `/backend/app/api`, `/backend/app/services/rag` | FastAPI routers, Auth, RAG Engine, REST APIs |
| **Agent 2 — Frontend** | `/frontend/src/` | React/Next.js components, UI/UX, State, API client |
| **Agent 3 — Database / Data / Ingestion**| `/backend/app/models`, `/backend/app/services/ingestion` | PostgreSQL schemas, SQLAlchemy, Ingestion pipeline, OCR, Vector DB |
| **Agent 4 — DevOps / QA / Integration** | `/infrastructure`, `/docker`, `.github/`, `/tests/` | CI/CD pipelines, Docker, Pytest, Playwright E2E, Cross-component QA |

---

## 6. Development & Verification Workflow

1. **Inspect Specifications**: Read `devdocs/`, `AGENT_RULES.md`, `PROJECT_STATE.md`, and `ARCHITECTURE.md`.
2. **Branch Isolation**: Create a feature branch matching your domain:
   - `agent/backend/feature/<name>`
   - `agent/frontend/feature/<name>`
   - `agent/ingestion/feature/<name>`
   - `agent/devops/feature/<name>`
3. **Implementation & Testing**: Write clean code and run unit & integration tests (`pytest`, `npm test`).
4. **Browser & Log Verification**: Execute Playwright browser verification for UI features and inspect server logs.
5. **Pull Request**: Open PR using `.github/pull_request_template.md`. PRs require review and human approval before merging.

---

## 7. Quick Start (Local Setup)

```bash
# Clone the repository
git clone <repository-url>
cd kyoku

# Start all services with Docker Compose
docker-compose up --build
```

- Frontend App: `http://localhost:3000`
- Backend API Docs (Swagger): `http://localhost:8000/docs`

---

## 8. License & Governance

Internal Enterprise Project. All rights reserved. Managed under the KEEP Four-Agent Autonomous Development Framework.