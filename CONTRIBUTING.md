# Contributing to KEEP (CONTRIBUTING.md)

Thank you for contributing to **KEEP (Knowledge Extraction & Enterprise Platform)**. This project follows a structured, four-agent autonomous development workflow designed for quality, stability, and security.

---

## 1. Getting Started

### Prerequisites
Before setting up the repository, ensure you have the following installed:
- **Git** (Latest stable)
- **Node.js 22 LTS** & `npm`
- **Python 3.12+** & `pip` / `uv`
- **PostgreSQL 16** (or Docker Desktop)
- **Docker Desktop** (Latest)

### Cloning the Repository
```bash
git clone <repository-url>
cd kyoku
```

---

## 2. Environment Setup

### 2.1 Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env
```

### 2.2 Frontend Setup
```bash
cd frontend
npm install
cp ../.env.example .env.local
```

### 2.3 Running with Docker Compose
```bash
docker-compose up --build
```

---

## 3. Four-Agent Autonomous Workflow

Every contribution—whether by a human developer or an Antigravity autonomous agent—must adhere to the following sequence:

```text
Read devdocs/ specifications
       │
       ▼
Inspect PROJECT_STATE.md & ARCHITECTURE.md
       │
       ▼
Inspect existing repository code
       │
       ▼
Create feature branch (agent/<domain>/feature/<name>)
       │
       ▼
Implement scoped changes
       │
       ▼
Run unit & integration tests
       │
       ▼
Run application locally & perform browser verification
       │
       ▼
Commit using Conventional Commits
       │
       ▼
Push feature branch & submit Pull Request
       │
       ▼
Verify CI checks pass
       │
       ▼
Obtain Human Approval & Merge
```

---

## 4. Branch Naming Strategy

Work must be performed in isolated feature branches matching assigned agent domains:

- **Backend / AI Infrastructure (Agent 1)**:  
  `agent/backend/feature/<feature-name>`  
  *Example*: `agent/backend/feature/fastapi-auth-router`

- **Frontend Application (Agent 2)**:  
  `agent/frontend/feature/<feature-name>`  
  *Example*: `agent/frontend/feature/dashboard-layout`

- **Database / Data / Ingestion (Agent 3)**:  
  `agent/ingestion/feature/<feature-name>`  
  *Example*: `agent/ingestion/feature/pdf-ocr-pipeline`

- **DevOps / QA / Infrastructure (Agent 4)**:  
  `agent/devops/feature/<feature-name>`  
  *Example*: `agent/devops/feature/github-actions-ci`

> **CRITICAL**: Never commit directly to `main` or `develop`.

---

## 5. Commit Message Conventions

We enforce [Conventional Commits](https://www.conventionalcommits.org/). Formats must include the Phase/Sub-phase scope where applicable:

- `feat(phase-1.2): implement JWT authentication endpoints`
- `fix(phase-1.3): resolve database migration constraint issue`
- `test(phase-2.1): add ingestion worker unit tests`
- `docs(phase-1.1): update API contract for document upload`
- `chore(deps): update python dependencies`

---

## 6. Pull Request Requirements

Every Pull Request must:
1. Use the official PR Template (`.github/pull_request_template.md`).
2. Include reference to the corresponding `devdocs/` Phase and Sub-phase.
3. Pass all automated CI checks (linting, type checking, unit tests, build).
4. Provide verification evidence (test outputs, log excerpts, or Playwright browser verification results).
5. Receive explicit review and human approval before merging.
