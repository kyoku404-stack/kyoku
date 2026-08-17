# KEEP — Four-Agent Autonomous Development Operating Policy (AGENT_RULES.md)

> **Mandatory Policy for all Antigravity Autonomous Agents working on the KEEP Project.**  
> Compliance with this document is strictly required. No agent may deviate from these rules without human authorization.

---

## 1. Core Operating Principles

1. **`devdocs/` is the Single Source of Project Specifications**:
   - `devdocs/` defines all functional, technical, and architectural requirements for Phase 0 through Phase 3.
   - Agents must never redefine or ignore requirements specified in `devdocs/`.
2. **Git is the Source of Truth**:
   - Code, documentation, schemas, and configurations must be tracked in Git.
3. **Four-Agent Ownership Isolation**:
   - Work within your designated component boundaries. Cross-domain edits require notification and formal handoffs via `docs/handoffs/agent-handoffs.md`.
4. **Empirical Verification Required**:
   - No task is complete without test execution, build validation, and log verification.

---

## 2. Git & Workspace Rules

- **Branch Isolation**:
  - **NEVER** modify or commit directly to `main` or `develop`.
  - Always work on assigned feature branches following the naming convention:
    - `agent/backend/feature/<feature-name>` (Agent 1)
    - `agent/frontend/feature/<feature-name>` (Agent 2)
    - `agent/ingestion/feature/<feature-name>` (Agent 3)
    - `agent/devops/feature/<feature-name>` (Agent 4)
- **Pre-Execution Check**:
  - Run `git status` and `git fetch` before beginning any task.
  - Pull latest updates from `develop` into your feature branch frequently.
- **Diff Inspection**:
  - Always run `git diff` before committing to ensure no unintended files or leftover debug logs are included.
- **Merge & Push Policy**:
  - **DO NOT** merge your own Pull Request. Merging requires review and human approval.
  - **DO NOT** force-push (`git push --force`) under any circumstances.
  - **DO NOT** overwrite another agent's active branch or files outside your ownership.

---

## 3. Mandatory Documentation Rules

Before writing any code or initiating any task, every agent must inspect and read:
1. `devdocs/` (Relevant Phase & Sub-Phase documents)
2. `AGENT_RULES.md` (This document)
3. `PROJECT_STATE.md` (Current project status)
4. `ARCHITECTURE.md` (System architecture blueprint)
5. `docs/api/api-contract.md` (API contracts)
6. `docs/database/database-schema.md` (Database models & schemas)
7. `docs/handoffs/agent-handoffs.md` (Handoff status from previous agents)

---

## 4. Development & Implementation Rules

- **Inspect Before Implementation**:
  - Inspect existing codebase to determine what is already implemented. Do not duplicate existing utilities or services.
- **Architecture Compliance**:
  - Adhere strictly to the layered architecture (FastAPI router -> Service -> Repository -> ORM for Backend; Component -> Service/Store -> API client for Frontend).
- **Assumptions & Deviations**:
  - If a requirement is ambiguous or underspecified, document it as an assumption in `docs/decisions/decisions.md`. Do not silently invent requirements.
- **Refactoring Limits**:
  - Avoid opportunistic refactoring of working code owned by other agents unless directly required for integration and approved.

---

## 5. Testing & Verification Rules

Every implementation MUST pass the following verification steps before claiming completion:
- **Backend (Agent 1 / Agent 3)**:
  - Run unit tests with `pytest`.
  - Verify database migrations run cleanly with `alembic upgrade head`.
  - Check log files for zero unhandled exceptions or hidden tracebacks.
- **Frontend (Agent 2)**:
  - Run frontend component/unit tests (`npm test`).
  - Run build verification (`npm run build`).
  - Conduct browser verification for user-facing UI flows.
- **DevOps / QA (Agent 4)**:
  - Execute end-to-end integration tests.
  - Verify CI workflow runs cleanly (`.github/workflows/ci.yml`).

---

## 6. Conflict Resolution & Handoffs

- **Cross-Agent Handoffs**:
  - When completing work that another agent depends on, update `docs/handoffs/agent-handoffs.md` with:
    - Implemented features & changed files
    - API endpoints added/updated
    - Database migration status
    - Required next actions for the receiving agent
- **Architectural Conflicts**:
  - Escalate cross-component contract disputes or breaking changes to `docs/decisions/decisions.md` and request human review.

---

## 7. Security & Secret Protection

- **NEVER** commit:
  - Passwords, API keys, JWT secret keys, DB credentials, private keys (`.pem`, `.key`).
  - Real environment files (`.env`).
- Always use `.env.example` for environment variable templates with placeholder values.
- Verify `.gitignore` is active and respected before every commit.

---

## 8. Definition of Done (DoD)

A task or sub-phase is considered **DONE** only when:
1. All sub-phase requirements in `devdocs/` are met.
2. Code is clean, typed, and follows standard conventions.
3. Unit, integration, and E2E tests pass.
4. Documentation in `docs/` (`api-contract.md`, `database-schema.md`, `PROJECT_STATE.md`) is updated.
5. Pull Request is created with the PR template completed.
6. Verification evidence (logs, test results, browser screenshots) is attached.
