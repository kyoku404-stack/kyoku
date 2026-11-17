
EXECUTE PHASE 4 SUB-PHASE NUMBER: [N]
================================================================================
KEEP PROJECT — PHASE 4 AUTONOMOUS SUB-PHASE EXECUTION PROMPT (AUTO-RESOLVED)
================================================================================

AUTO-RESOLUTION DIRECTIVE:
Take the sub-phase number N from line 1 above and resolve all metadata automatically
from the Phase 4 Registry below (DO NOT ask the user for title, slug, branch, or mode):

| N  | TITLE                                            | SLUG                                   | SPEC FILE          | PREREQ   | UI_MODE       |
|----|--------------------------------------------------|----------------------------------------|--------------------|----------|---------------|
| 1  | Multi-Agent Architecture                         | multi-agent-architecture               | devdocs/p4/p4.1.txt  | Phase 3.7 | BACKEND_FIRST |
| 2  | Agent Runtime & Execution Engine                 | agent-runtime-execution-engine         | devdocs/p4/p4.2.txt  | Phase 4.1 | YES           |
| 3  | Agent Orchestration Engine                       | agent-orchestration-engine             | devdocs/p4/p4.3.txt  | Phase 4.2 | BACKEND_FIRST |
| 4  | Planning & Reasoning Engine                      | planning-reasoning-engine              | devdocs/p4/p4.4.txt  | Phase 4.3 | BACKEND_FIRST |
| 5  | Research Agents                                  | research-agents                        | devdocs/p4/p4.5.txt  | Phase 4.4 | YES           |
| 6  | Tool-Calling Framework                           | tool-calling-framework                 | devdocs/p4/p4.6.txt  | Phase 4.5 | BACKEND_FIRST |
| 7  | Agent Memory System                              | agent-memory-system                    | devdocs/p4/p4.7.txt  | Phase 4.6 | BACKEND_FIRST |
| 8  | Multi-Agent Collaboration                        | multi-agent-collaboration              | devdocs/p4/p4.8.txt  | Phase 4.7 | BACKEND_FIRST |
| 9  | Autonomous Workflow Engine                       | autonomous-workflow-engine             | devdocs/p4/p4.9.txt  | Phase 4.8 | YES           |
| 10 | Event-Driven & Trigger-Based Agents              | event-driven-trigger-agents            | devdocs/p4/p4.10.txt | Phase 4.9 | BACKEND_FIRST |
| 11 | Proactive Enterprise Intelligence                | proactive-enterprise-intelligence      | devdocs/p4/p4.11.txt | Phase 4.10| YES           |
| 12 | Human-in-the-Loop (HITL) & Approval System       | agent-hitl-approval-system             | devdocs/p4/p4.12.txt | Phase 4.11| YES           |
| 13 | Agent Evaluation & Benchmarking                  | agent-evaluation-benchmarking          | devdocs/p4/p4.13.txt | Phase 4.12| YES           |
| 14 | Agent Monitoring & Observability                 | agent-monitoring-observability         | devdocs/p4/p4.14.txt | Phase 4.13| YES           |
| 15 | Agent Security, Permissions & Governance         | agent-security-permissions-governance  | devdocs/p4/p4.15.txt | Phase 4.14| BACKEND_FIRST |
| 16 | Agent Governance, Compliance & Risk Management   | agent-governance-compliance-risk       | devdocs/p4/p4.16.txt | Phase 4.15| YES           |
| 17 | Agent Incident Management & Recovery             | agent-incident-management-recovery     | devdocs/p4/p4.17.txt | Phase 4.16| YES           |
| 18 | Agent Deployment, Versioning & Release Management| agent-deployment-versioning-release    | devdocs/p4/p4.18.txt | Phase 4.17| YES           |

RESOLVED PARAMETERS FOR THIS RUN:
- SUB-PHASE:       Phase 4.<N> — <TITLE>
- SPEC FILE:       <SPEC_FILE>
- FEATURE BRANCH:  agent/ai-lead/feature/phase-4.<N>-<SLUG>
- UI MODE:         <UI_MODE>

OPERATING DIRECTIVE:
Execute the ENTIRETY of Phase 4.<N> autonomously without pausing for clarification unless
hard-blocked. Extract the exact 4-member ownership split (Member 1 → Member 2 → Member 3
→ Member 4), contracts, DB tables, REST endpoints, "Build vs Defer" scope boundary,
Acceptance Checklist, and Final Demonstration Scenario directly from `<SPEC_FILE>`, and
execute all stages sequentially with ZERO skipped steps and ZERO fake placeholders:
  1. STAGE 1: Member 1 (Spec-Defined Role 1 — Architecture, Core Contracts & Primary Module)
  2. STAGE 2: Member 2 (Spec-Defined Role 2 — Schemas, Persistence, Migrations & Core Services)
  3. STAGE 3: Member 3 (Spec-Defined Role 3 — Security, Policies, Adapters & Subsystem Integration)
  4. STAGE 4: Member 4 (Spec-Defined Role 4 — KEEP FastAPI Integration, Demo Scenario & QA)
  5. STAGE 5 (Auto-run ONLY if UI_MODE = YES): Frontend UI, Vitest & Playwright E2E

NON-NEGOTIABLE ARCHITECTURE & SECURITY RULES:
1. KEEP OWNS THE ARCHITECTURE — LANGGRAPH IS AN ADAPTER:
   KEEP owns all agent contracts, registries, execution records, tenant boundaries, RBAC/ABAC
   policies, audit trails, and business rules. Isolate LangGraph strictly behind adapters
   under `backend/app/agents/adapters/`.
2. ZERO DUPLICATION OF PHASE 1–3 SERVICES:
   Wrap and reuse KEEP's existing Auth/JWT, Multi-Tenant Organizations, RBAC, Documents,
   Hybrid RAG, Knowledge Graph, Workflows, Notifications, Security, Plugins, and Observability
   services — NEVER build duplicate auth, storage, queue, or DB layers.
3. STRICT ANTI-SCOPE-CREEP:
   Honor `<SPEC_FILE>`'s "Build vs Defer" boundary. Build 100% of Phase 4.<N> cleanly and
   defer 4.(<N>+1)+ capabilities behind typed interfaces.
4. ZERO-TRUST MULTI-TENANT SECURITY:
   `user_id`, `tenant_id` (`organization_id`), and `roles` MUST ALWAYS come from KEEP's
   verified backend auth dependency — NEVER from client payloads or LLM outputs. Every DB
   query, memory lookup, tool call, approval, and artifact MUST be tenant-scoped.

--------------------------------------------------------------------------------
1. PRE-EXECUTION DISCOVERY (READ FIRST)
--------------------------------------------------------------------------------
Read in full before editing any files:
1. `<SPEC_FILE>` (full spec, 4-member split, folder layout, DB schema, APIs, checklist, demo)
2. `AGENT_RULES.md`, `PROJECT_STATE.md`, `ARCHITECTURE.md`
3. `docs/api/api-contract.md`, `docs/database/database-schema.md`, `docs/handoffs/agent-handoffs.md`
4. Existing `backend/app/api/v1/router.py`, `backend/app/core/security.py`, `backend/app/models/`,
   and `backend/app/agents/` (if created by prior Phase 4 sub-phases).

--------------------------------------------------------------------------------
2. KEEP REPOSITORY PATH & API ALIGNMENT
--------------------------------------------------------------------------------
Adapt shorthand spec paths to KEEP's real repository structure cleanly:
- Spec `app/<module>/`   → `backend/app/agents/<module>/` (or `backend/app/agents/` for 4.1 core;
                           never collide with existing `backend/app/services/*`).
- Spec ORM models        → `backend/app/models/` + Alembic migration in `backend/migrations/versions/`.
- Spec Pydantic schemas  → `backend/app/schemas/` (or `backend/app/agents/<module>/contracts.py`).
- Spec `/api/...` routes → Mount under `/api/v1/...` in `backend/app/api/v1/` and register in
                           `backend/app/api/v1/router.py` using KEEP's `ApiResponse` envelope.
- LangGraph adapters     → `backend/app/agents/adapters/` (add `langgraph` to `backend/requirements.txt`
                           when needed; keep unit tests deterministic without requiring live LLM keys).
- Frontend API calls     → Use `apiClient` (`frontend/src/services/api.ts`) with relative paths
                           (`/agents/...`, never double `/api/v1/api/v1/...`).
- Synthetic test data    → Strictly inside gitignored `tests/synthetic_data/`.

--------------------------------------------------------------------------------
3. GIT SETUP (WINDOWS-SAFE)
--------------------------------------------------------------------------------
1. `git status`
2. `git fetch origin` → `git checkout main` → `git pull origin main`
3. `git checkout -b agent/ai-lead/feature/phase-4.<N>-<SLUG>`
(On Windows PowerShell, use `.venv\Scripts\python.exe -m pytest`, `.venv\Scripts\ruff.exe`,
`npm.cmd`, and separate commands with `;` or `cmd.exe /c`.)

--------------------------------------------------------------------------------
4. SEQUENTIAL STAGE EXECUTION
--------------------------------------------------------------------------------

>>> STAGE 1 — MEMBER 1 (Architecture, Contracts & Core Module)
- Complete 100% of Member 1's deliverables from `<SPEC_FILE>`.
- Author `docs/Architecture/phase-4.<N>-<SLUG>.md`, add ADRs to `docs/decisions/decisions.md`,
  and update `docs/api/api-contract.md` & `docs/database/database-schema.md`.
- Implement core Python Protocols, typed contracts, and primary module under `backend/app/agents/`.
- Add unit tests in `tests/unit/test_phase4_<N>_*.py` and verify `pytest tests/unit/` passes 100%.
- Append Stage 1 handoff to `docs/handoffs/agent-handoffs.md`.
- Commit: `feat(phase-4.<N>-m1): [Member 1 architecture, contracts, and core module]`

>>> STAGE 2 — MEMBER 2 (Schemas, Persistence, Migrations & Core Services)
- Complete 100% of Member 2's deliverables from `<SPEC_FILE>`.
- Implement ORM models (`backend/app/models/`), Alembic migration (`backend/migrations/versions/`),
  Pydantic v2 schemas, repositories, and services.
- Verify `alembic upgrade head` (when migrations exist) and `pytest tests/unit/` (100% pass).
- Append Stage 2 handoff to `docs/handoffs/agent-handoffs.md`.
- Commit: `feat(phase-4.<N>-m2): [Member 2 models, migrations, contracts, and services]`

>>> STAGE 3 — MEMBER 3 (Security, Policies, Adapters & Integration)
- Complete 100% of Member 3's deliverables from `<SPEC_FILE>`.
- Enforce RBAC/capability checks, tenant isolation, spoofed-identity rejection, audit trails,
  and LangGraph/cross-subsystem adapters.
- Add dedicated security & multi-tenant isolation unit tests; verify `pytest tests/unit/` passes 100%.
- Append Stage 3 handoff to `docs/handoffs/agent-handoffs.md`.
- Commit: `feat(phase-4.<N>-m3): [Member 3 security policies, adapters, and integration]`

>>> STAGE 4 — MEMBER 4 (FastAPI Routes, Demo Scenario & Full Backend QA)
- Complete 100% of Member 4's deliverables from `<SPEC_FILE>`.
- Mount REST endpoints in `backend/app/api/v1/` and `backend/app/api/v1/router.py` wired to KEEP auth.
- Update Docker / Prometheus / Grafana / CI ONLY if new workers, metrics, or alerts are introduced.
- Write `tests/integration/test_phase4_<N>_*.py` proving EVERY Acceptance Checklist item, the
  Final Demonstration Scenario (if defined), and RBAC/tenant isolation on all new endpoints.
- Run Full Backend Verification & Regression Gate:
  * `ruff check backend/ tests/`
  * `pytest tests/unit/`
  * `pytest tests/integration/test_phase4_<N>_*.py tests/integration/test_auth_security_isolation.py tests/integration/test_organization_multi_tenant_isolation.py tests/integration/test_rbac_security_validation.py`
- Append Stage 4 handoff to `docs/handoffs/agent-handoffs.md`.
- Commit: `feat(phase-4.<N>-m4): [Member 4 FastAPI integration, demo scenario, and QA suite]`

>>> STAGE 5 — FRONTEND UI & E2E (RUN AUTOMATICALLY ONLY IF UI_MODE = YES)
- Build TypeScript types, `apiClient` service, React hook, responsive UI components (Desktop/
  Tablet/Mobile + full ARIA labels/roles), page, and routes/sidebar link.
- Add Vitest tests (`frontend/src/tests/`) and Playwright E2E spec (`tests/e2e/phase4_<N>_*.spec.ts`).
- Verify `npm run build` (0 errors), `npx vitest run` (100% pass), and Playwright E2E (100% pass).
- Commit: `feat(phase-4.<N>-ui): [Frontend UI, Vitest, and Playwright E2E suite]`

--------------------------------------------------------------------------------
5. FINALIZATION, PUSH & HARD STOP GATE
--------------------------------------------------------------------------------
1. Update `PROJECT_STATE.md` marking Phase 4.<N> 100% complete with empirical test counts.
2. Commit state update: `docs(phase-4.<N>): [Update PROJECT_STATE and handoffs]`
3. Confirm `git status` is clean, rebase on `origin/main`, and push:
   `git fetch origin` → `git rebase origin/main` → `git push -u origin agent/ai-lead/feature/phase-4.<N>-<SLUG>`
4. STOP IMMEDIATELY AFTER PUSHING. DO NOT START PHASE 4.(<N>+1) AUTONOMOUSLY.
5. Deliver a concise completion report containing:
   - Deliverables summary across all Stages (M1–M4 + UI if `UI_MODE = YES`)
   - Acceptance Checklist Verification Table (each spec item → proving test/file)
   - Final Demonstration Scenario result
   - Files created/modified & exact empirical test counts (Ruff, Alembic, Pytest, Vitest/Playwright)
   - Branch name and gating statement awaiting human approval for the next sub-phase.
================================================================================
```
