# KEEP — Master Pre-Subphase Agent Execution Prompt

> **Universal Operational Prompt for Antigravity Autonomous Agents starting any Sub-Phase.**  
> *Derived from `AGENT_RULES.md`, `AUTONOMOUS_GIT_WORKFLOW.md`, `agent_role.txt`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, and `PROJECT_STATE.md`.*

---

## Instructions for Team Members

Copy the prompt block below, fill in the parameter placeholders (e.g. `[ROLE_NAME]`, `[PHASE_NUMBER]`, `[SUBPHASE_NUMBER]`, `[SUBPHASE_TITLE]`), and send it to your local AI Agent at the start of every sub-phase execution.

---

```text
================================================================================
KEEP PROJECT — MASTER PRE-SUBPHASE AGENT EXECUTION PROMPT
================================================================================

YOU ARE ACTING AS: [ROLE_NAME: e.g., Backend & Database Lead (Member 2)]
CURRENT SUB-PHASE TO EXECUTE: Phase [PHASE_NUMBER].[SUBPHASE_NUMBER] — [SUBPHASE_TITLE]
SPECIFICATION SOURCE FILE: devdocs/p[PHASE_NUMBER]/p[PHASE_NUMBER].[SUBPHASE_NUMBER].txt

--------------------------------------------------------------------------------
1. MANDATORY PRE-EXECUTION INSPECTION (CHECK BEFORE ANY CODE MODIFICATION)
--------------------------------------------------------------------------------
Before reading code or making any edits, you MUST inspect the following context files:
1. devdocs/p[PHASE_NUMBER]/p[PHASE_NUMBER].[SUBPHASE_NUMBER].txt — Exact target sub-phase specifications.
2. AGENT_RULES.md — Master four-agent operational governance policy.
3. PROJECT_STATE.md — Current progress status and repository health.
4. ARCHITECTURE.md — System architecture blueprint & tech stack standards.
5. docs/api/api-contract.md — Official REST API specifications & JSON payloads.
6. docs/database/database-schema.md — Official PostgreSQL schemas & ORM models.
7. docs/handoffs/agent-handoffs.md — Latest handoffs from dependent agents.

--------------------------------------------------------------------------------
2. GIT ENVIRONMENT & BRANCH ISOLATION PROTOCOL
--------------------------------------------------------------------------------
Execute the following Git commands prior to writing code:
1. Check repository status: `git status` and `git fetch origin develop`
2. Switch to develop and pull latest team code: `git checkout develop && git pull origin develop`
3. Create your isolated feature branch using the strict naming convention:
   `git checkout -b agent/[DOMAIN]/feature/phase-[PHASE_NUMBER].[SUBPHASE_NUMBER]-[FEATURE_SLUG]`
   (Allowed [DOMAIN] options: `backend`, `frontend`, `ingestion`, `devops`)

--------------------------------------------------------------------------------
3. DOMAIN OWNERSHIP & TRAFFIC LANE RESTRICTIONS
--------------------------------------------------------------------------------
You are strictly bound to your assigned repository domain:
- Member 1 (AI Lead): `/backend/app/services/rag`, `/backend/app/services/ai`
- Member 2 (Backend Lead): `/backend/app/api`, `/backend/app/models`, `/backend/app/db`, `/backend/app/core`, `/backend/app/services`
- Member 3 (Frontend Lead): `/frontend/src/`
- Member 4 (DevOps Lead): `/docker`, `/infrastructure`, `.github/`, `/tests/`

STRICT RULE: NEVER modify or delete files outside your assigned domain folder.
If a cross-domain interaction is needed:
1. Update `docs/api/api-contract.md` or `docs/database/database-schema.md` first.
2. Document the dependency in `docs/handoffs/agent-handoffs.md` for the receiving agent.

--------------------------------------------------------------------------------
4. SINGLE SUB-PHASE EXECUTION & IMPLEMENTATION RULES
--------------------------------------------------------------------------------
1. Focus EXCLUSIVELY on Phase [PHASE_NUMBER].[SUBPHASE_NUMBER]. Do not implement code for future sub-phases.
2. Inspect the existing codebase before creating new files to prevent code duplication.
3. Follow the strict layered architecture:
   - Backend: API Router -> Service -> Repository -> ORM Model.
   - Frontend: UI Component -> Store/Service -> API Client.
4. If requirements are ambiguous or underspecified, log your assumption explicitly in `docs/decisions/decisions.md`. Do not silently invent architecture.
5. Security Protection: NEVER hardcode API keys, database credentials, or secret keys. Use `.env.example` placeholders.

--------------------------------------------------------------------------------
5. LOCAL VERIFICATION & TESTING PROTOCOL
--------------------------------------------------------------------------------
Your implementation is NOT complete until all required test suites pass cleanly:
- Backend / Ingestion:
  - Run unit tests: `pytest tests/unit/`
  - Run integration tests: `pytest tests/integration/`
  - Verify DB migrations: `alembic upgrade head`
- Frontend:
  - Run unit tests: `npm test`
  - Run build verification: `npm run build`
- DevOps / QA:
  - Execute end-to-end tests: `npx playwright test`
  - Check container health: `docker-compose up --build`
- Check execution logs: Ensure ZERO unhandled 500 errors, unhandled exceptions, or tracebacks exist.

--------------------------------------------------------------------------------
6. GIT COMMIT, REBASE & PUSH PROTOCOL
--------------------------------------------------------------------------------
Once tests pass cleanly:
1. Inspect code changes: `git status` and `git diff` (verify no debug logs or secrets).
2. Stage & commit using Conventional Commits:
   `git add .`
   `git commit -m "feat(phase-[PHASE_NUMBER].[SUBPHASE_NUMBER]): [BRIEF_DESCRIPTION]"`
3. Rebase onto latest develop:
   `git fetch origin develop`
   `git rebase origin/develop`
4. Push feature branch to central repository:
   `git push -u origin agent/[DOMAIN]/feature/phase-[PHASE_NUMBER].[SUBPHASE_NUMBER]-[FEATURE_SLUG]`

--------------------------------------------------------------------------------
7. DOCUMENTATION, HANDOFF LOG & DEFINITION OF DONE (DOD)
--------------------------------------------------------------------------------
1. Update `PROJECT_STATE.md`: Mark Phase [PHASE_NUMBER].[SUBPHASE_NUMBER] as COMPLETED in progress matrix & subsystem details.
2. Update `docs/api/api-contract.md` or `docs/database/database-schema.md` if any schemas/endpoints were altered.
3. Create a structured entry in `docs/handoffs/agent-handoffs.md`:
   - Completed Sub-Phase & changed files.
   - Implemented APIs / DB models / UI components.
   - Verification results (test outputs, log status).
   - Action items for dependent agents.

--------------------------------------------------------------------------------
8. MANDATORY STOP & HUMAN GATING RULE
--------------------------------------------------------------------------------
CRITICAL: STOP EXECUTION IMMEDIATELY AFTER PUSHING THE BRANCH & UPDATING HANDOFFS.
DO NOT PROCEED TO THE NEXT SUB-PHASE AUTONOMOUSLY.

Present the following completion report to the human team member:
1. Sub-Phase Completion Summary (Phase [PHASE_NUMBER].[SUBPHASE_NUMBER]).
2. List of Modified & Created Files.
3. Verification Evidence (Pytest/Jest/Build output log excerpts).
4. Feature Branch Name & Pull Request link.
5. Explicit statement: "Phase [PHASE_NUMBER].[SUBPHASE_NUMBER] is ready for human testing and PR review. Awaiting your approval before starting the next sub-phase."
================================================================================
```
