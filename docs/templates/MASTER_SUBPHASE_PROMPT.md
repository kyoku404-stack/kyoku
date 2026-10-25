# KEEP — Master Full Sub-Phase Sequential Execution Prompt

> **Universal End-to-End Operational Prompt for Antigravity Autonomous Agents executing an entire Sub-Phase.**  
> *Orchestrates sequential, uncompromised execution across all four team member roles (Member 1 AI Lead → Member 2 Backend Lead → Member 3 Frontend Lead → Member 4 DevOps Lead) in a single autonomous invocation.*  
> *Derived from `AGENT_RULES.md`, `AUTONOMOUS_GIT_WORKFLOW.md`, `agent_role.txt`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, and `PROJECT_STATE.md`.*

---

## Instructions for Team Members

Copy the prompt block below, fill in the parameter placeholders:
- `[PHASE_NUMBER]` (e.g. `2`)
- `[SUBPHASE_NUMBER]` (e.g. `1` or `2`)
- `[SUBPHASE_TITLE]` (e.g. `AI Knowledge Ingestion Pipeline` or `Vector Database & Semantic Search Architecture`)
- `[FEATURE_SLUG]` (e.g. `ai-ingestion-pipeline` or `vector-database-semantic-search`)
- `[PRIMARY_ROLE_DOMAIN]` (Primary leading domain according to AGENT_RULES.md convention: `ai-lead` / `backend` / `frontend` / `devops`, e.g. `ai-lead` for Phase 2.1/2.2)

Then send it to your local Antigravity AI Agent. The agent will execute all 4 member roles sequentially, maintaining strict domain isolation, enforcing tests and migrations at each step, logging asynchronous handoffs, and producing a complete sub-phase delivery ready for human review.

---

```text
================================================================================
KEEP PROJECT — FULL SUB-PHASE SEQUENTIAL EXECUTION PROMPT
================================================================================

CURRENT SUB-PHASE TO EXECUTE: Phase [PHASE_NUMBER].[SUBPHASE_NUMBER] — [SUBPHASE_TITLE]
SPECIFICATION SOURCE FILE: devdocs/p[PHASE_NUMBER]/p[PHASE_NUMBER].[SUBPHASE_NUMBER].txt
ISOLATED FEATURE BRANCH: agent/[PRIMARY_ROLE_DOMAIN]/feature/phase-[PHASE_NUMBER].[SUBPHASE_NUMBER]-[FEATURE_SLUG]
(or sub-phase lead domain: `agent/ai-lead/feature/...`, `agent/backend/feature/...`, `agent/frontend/feature/...`, `agent/devops/feature/...`)

OPERATING DIRECTIVE:
You are tasked with executing the ENTIRETY of Phase [PHASE_NUMBER].[SUBPHASE_NUMBER] from start to finish.
You will assume the roles of all four team members SEQUENTIALLY, executing their full,
uncompromised deliverables in strict dependency order:
  1. STAGE 1: Member 1 (Project Lead & AI Architect)
  2. STAGE 2: Member 2 (Backend & Database Lead)
  3. STAGE 3: Member 3 (Frontend & UI Lead)
  4. STAGE 4: Member 4 (Integration & DevOps Lead)

CRITICAL QUALITY GUARANTEE:
There must be ZERO loss of quality, ZERO skipped steps, and ZERO simulated placeholders.
Each member role's tasks must be fully coded, tested, verified, and documented before
transitioning to the next member's role.

--------------------------------------------------------------------------------
1. MANDATORY PRE-EXECUTION DISCOVERY & TASK EXTRACTION
--------------------------------------------------------------------------------
Before writing code or making any edits, you MUST inspect:
1. devdocs/p[PHASE_NUMBER]/p[PHASE_NUMBER].[SUBPHASE_NUMBER].txt:
   - Read the overall sub-phase objective and all technical chapters.
   - LOCATE AND READ the "Team Member Responsibilities" Chapter (e.g. Chapter 18/19/20) at the end.
   - EXTRACT the complete deliverables assigned to EACH of the 4 roles:
     * Member 1 (AI Lead & Architect)
     * Member 2 (Backend Lead)
     * Member 3 (Frontend Lead)
     * Member 4 (DevOps & Integration Lead)
2. AGENT_RULES.md — Four-agent operational governance and domain boundary policy.
3. PROJECT_STATE.md — Current milestone progress and repository health.
4. ARCHITECTURE.md — System architecture blueprint & tech stack standards.
5. docs/api/api-contract.md — Current REST API specifications.
6. docs/database/database-schema.md — Current PostgreSQL schemas & ORM models.
7. docs/handoffs/agent-handoffs.md — Previous sub-phase handoffs and baseline states.

--------------------------------------------------------------------------------
2. GIT ENVIRONMENT & SUB-PHASE BRANCH PROTOCOL
--------------------------------------------------------------------------------
Execute the following Git commands prior to writing code:
1. Check repository status: `git status`
2. Fetch latest changes: `git fetch origin`
3. Switch to integration baseline (`main` or `develop`): `git checkout main; git pull origin main`
4. Create the isolated sub-phase feature branch using the strict naming convention:
   `git checkout -b agent/[PRIMARY_ROLE_DOMAIN]/feature/phase-[PHASE_NUMBER].[SUBPHASE_NUMBER]-[FEATURE_SLUG]`
   (Allowed [PRIMARY_ROLE_DOMAIN] values: `ai-lead`, `backend`, `frontend`, `devops` — e.g., `agent/ai-lead/feature/phase-2.2-vector-database-semantic-search`)

--------------------------------------------------------------------------------
3. DOMAIN OWNERSHIP & TRAFFIC LANE GOVERNANCE
--------------------------------------------------------------------------------
While acting in each member's role, strictly respect that member's domain boundary:
- Member 1 (AI Lead): `/backend/app/services/rag`, `/backend/app/services/ai`, `docs/Architecture/`, `docs/decisions/`
- Member 2 (Backend Lead): `/backend/app/api`, `/backend/app/models`, `/backend/app/db`, `/backend/app/core`, `/backend/app/services`, `/backend/migrations`
- Member 3 (Frontend Lead): `/frontend/src/`
- Member 4 (DevOps Lead): `/docker`, `/infrastructure`, `.github/`, `/tests/`
- Shared System Documentation (All): `PROJECT_STATE.md`, `docs/handoffs/agent-handoffs.md`, `docs/api/api-contract.md`, `docs/database/database-schema.md`

NEVER modify a domain outside the currently active member stage.
Cross-domain dependencies must be formalized through API contracts, database schemas, and handoff entries.

--------------------------------------------------------------------------------
4. SEQUENTIAL STAGE-BY-STAGE EXECUTION WORKFLOW
--------------------------------------------------------------------------------

================================================================================
>>> STAGE 1: MEMBER 1 (PROJECT LEAD & AI ARCHITECT)
================================================================================
Scope: High-level architecture, algorithms, ADRs, typed AI contracts, and unit tests.
Deliverables:
1. Author Master Architecture Specification for Phase [PHASE_NUMBER].[SUBPHASE_NUMBER] under `docs/Architecture/`.
2. Author relevant Architecture Decision Records (ADRs) in `docs/decisions/decisions.md`.
3. Update `docs/api/api-contract.md` with new REST endpoints, schemas, and error envelopes.
4. Update `docs/database/database-schema.md` with new tables, vector columns, indexes, and constraints.
5. Implement typed AI domain contracts, interfaces, enums, dataclasses, and abstract base classes in:
   - `backend/app/services/ai/`
   - `backend/app/services/rag/`
6. Authored dedicated unit test suite in `tests/unit/` verifying contracts and algorithms.
7. Verification: Run unit tests: `pytest tests/unit/`
8. Stage Completion:
   - Commit: `git add . && git commit -m "feat(phase-[PHASE_NUMBER].[SUBPHASE_NUMBER]-m1): [Member 1 AI architecture, ADRs, and domain contracts]"`
   - Append Handoff Entry in `docs/handoffs/agent-handoffs.md` detailing contracts for Member 2.

================================================================================
>>> STAGE 2: MEMBER 2 (BACKEND & DATABASE LEAD)
================================================================================
Scope: Relational persistence, Alembic migrations, business services, and FastAPI REST endpoints.
Deliverables:
1. Inspect Member 1's contracts, ADRs, and handoff entry.
2. Implement SQLAlchemy ORM models in `backend/app/models/` matching `docs/database/database-schema.md`.
3. Create and verify Alembic schema migration revision in `backend/migrations/versions/`.
4. Implement business logic and service orchestrators in `backend/app/services/`.
5. Implement Pydantic v2 validation schemas in `backend/app/schemas/` matching `docs/api/api-contract.md`.
6. Implement FastAPI router endpoints in `backend/app/api/v1/` and mount in `backend/app/api/v1/router.py`.
7. Authored backend unit and integration test suites in `tests/unit/` and `tests/integration/`.
8. Verification:
   - Verify DB migrations: `alembic upgrade head`
   - Run unit tests: `pytest tests/unit/`
   - Run integration tests: `pytest tests/integration/`
   - Verify 0 unhandled exceptions or tracebacks.
9. Stage Completion:
   - Commit: `git add . && git commit -m "feat(phase-[PHASE_NUMBER].[SUBPHASE_NUMBER]-m2): [Member 2 ORM models, migrations, services, and REST APIs]"`
   - Append Handoff Entry in `docs/handoffs/agent-handoffs.md` detailing API endpoints for Member 3.

================================================================================
>>> STAGE 3: MEMBER 3 (FRONTEND & UI LEAD)
================================================================================
Scope: TypeScript types, API client, custom hooks, feature components, master page, and routing.
Deliverables:
1. Inspect Member 1 & 2's API contracts, payloads, and handoff entries.
2. Implement TypeScript interfaces, types, and enums in `frontend/src/types/`.
3. Implement Axios/Fetch API client service methods in `frontend/src/services/`.
4. Implement state management and custom React hooks in `frontend/src/hooks/` with real-time polling/mutations.
5. Build modular UI feature components in `frontend/src/features/` with rich aesthetics and responsive design.
6. Build or integrate the master Page in `frontend/src/pages/`.
7. Configure routes in `frontend/src/routes/paths.ts` and `frontend/src/routes/index.tsx`.
8. Update sidebar and top navigation in `frontend/src/components/common/`.
9. Authored frontend unit & component test suites in `frontend/src/tests/`.
10. Verification:
    - Run linting: `npm run lint` (0 errors, 0 warnings)
    - Run unit & component tests: `npm test` (100% pass rate)
    - Run production build: `npm run build` (Clean build)
11. Stage Completion:
    - Commit: `git add . && git commit -m "feat(phase-[PHASE_NUMBER].[SUBPHASE_NUMBER]-m3): [Member 3 UI client, components, page, and routing]"`
    - Append Handoff Entry in `docs/handoffs/agent-handoffs.md` detailing UI elements for Member 4.

================================================================================
>>> STAGE 4: MEMBER 4 (INTEGRATION & DEVOPS LEAD)
================================================================================
Scope: Containerization, Docker Compose, monitoring, Prometheus alerts, Grafana dashboards, and test suites.
Deliverables:
1. Inspect Member 1, 2, and 3 codebases, services, and handoff entries.
2. Update/create Dockerfiles in `docker/` for new workers or background services.
3. Update `docker-compose.yml` and `docker-compose.prod.yml` with services, queues, persistent volumes, and CPU/RAM quotas.
4. Configure Prometheus alerting rules in `infrastructure/prometheus/alert_rules.yml`.
5. Provision/update Grafana dashboards in `infrastructure/grafana/dashboards/`.
6. Update `.github/workflows/ci.yml` with container build checks or verification steps.
7. Authored comprehensive backend integration & performance test suite in `tests/integration/`.
8. Authored Playwright E2E automated test suite in `tests/e2e/` covering complete end-to-end user workflows and responsive breakpoints (Desktop, Tablet, Mobile).
9. Full Verification:
   - Run Ruff linter: `ruff check backend/ tests/ docker/`
   - Run backend test suite: `pytest tests/unit/ tests/integration/`
   - Run frontend test suite: `npm test` in `frontend/`
   - Run frontend build: `npm run build` in `frontend/`
   - Verify Playwright tests: `playwright test --list`
10. Stage Completion:
    - Update `PROJECT_STATE.md`: Mark Phase [PHASE_NUMBER].[SUBPHASE_NUMBER] 100% complete across all 4 roles.
    - Append Handoff Entry in `docs/handoffs/agent-handoffs.md` summarizing full sub-phase DevOps completion.
    - Commit: `git add . && git commit -m "feat(phase-[PHASE_NUMBER].[SUBPHASE_NUMBER]-m4): [Member 4 containerization, infrastructure, and test suites]"`

--------------------------------------------------------------------------------
5. GIT PUSH & BRANCH FINALIZATION PROTOCOL
--------------------------------------------------------------------------------
Once all 4 stages are completed and verified:
1. Inspect git status: `git status` (confirm working tree is clean).
2. Fetch and rebase against remote integration branch:
   `git fetch origin`
   `git rebase origin/main` (or origin/develop)
3. Push the feature branch to central repository:
   `git push -u origin agent/[PRIMARY_ROLE_DOMAIN]/feature/phase-[PHASE_NUMBER].[SUBPHASE_NUMBER]-[FEATURE_SLUG]`

--------------------------------------------------------------------------------
6. MANDATORY CONSOLIDATED COMPLETION REPORT & GATING RULE
--------------------------------------------------------------------------------
CRITICAL: STOP EXECUTION IMMEDIATELY AFTER PUSHING THE BRANCH.
DO NOT PROCEED TO THE NEXT SUB-PHASE AUTONOMOUSLY.

Present the consolidated full sub-phase completion report to the human team member:
1. Executive Summary of completed Phase [PHASE_NUMBER].[SUBPHASE_NUMBER] deliverables across all 4 members:
   - Member 1 (AI Lead & Architect)
   - Member 2 (Backend Lead)
   - Member 3 (Frontend Lead)
   - Member 4 (DevOps Lead)
2. Master List of Created and Modified Files grouped by Member Role.
3. Complete Empirical Verification Evidence (Ruff linter, pytest, vitest, npm build, playwright discovery excerpts).
4. Feature Branch Name & Pull Request creation link.
5. Explicit statement:
   "Phase [PHASE_NUMBER].[SUBPHASE_NUMBER] ([SUBPHASE_TITLE]) is 100% complete across all four member roles, fully verified, and pushed. Awaiting your approval before starting the next sub-phase."
================================================================================
```
