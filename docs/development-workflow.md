# KEEP — Development & Collaboration Workflow (docs/development-workflow.md)

> **Official Four-Agent / Multi-Developer Workflow Protocol**  
> *Owner: Member 1 (Project Lead & AI Architect)*

---

## 1. Monorepo Branch Isolation Model

All development in KEEP operates under strict branch isolation. Direct commits to `main` and `develop` are strictly prohibited.

```
main (Production Releases)
  ▲
  │ (Sprint Release / Milestone Review)
develop (Integration Branch)
  ▲
  ├── agent/backend/feature/phase-X.Y-<name>      (Member 1 / Member 2)
  ├── agent/frontend/feature/phase-X.Y-<name>     (Member 3)
  ├── agent/ingestion/feature/phase-X.Y-<name>    (Member 2 / Member 3)
  └── agent/devops/feature/phase-X.Y-<name>       (Member 4)
```

---

## 2. Standard Feature Lifecycle

```
1. Task Assignment & Extraction from devdocs/
   │
   ▼
2. Git Sync & Branch Creation
   git checkout develop && git pull origin develop
   git checkout -b agent/<DOMAIN>/feature/phase-X.Y-<slug>
   │
   ▼
3. Local Implementation (Domain Restricted)
   - Code within assigned folders only
   - Update contracts/schemas if cross-domain changes are required
   │
   ▼
4. Empirical Verification & Automated Testing
   - Pytest unit and integration tests
   - Frontend build & test verification
   - Zero unhandled exceptions / zero console error logs
   │
   ▼
5. Documentation & Handoff Logging
   - Update PROJECT_STATE.md
   - Add structured entry to docs/handoffs/agent-handoffs.md
   │
   ▼
6. Commit, Rebase & Push
   git add .
   git commit -m "feat(phase-X.Y): description"
   git fetch origin develop
   git rebase origin/develop
   git push -u origin agent/<DOMAIN>/feature/phase-X.Y-<slug>
   │
   ▼
7. Human Gating & Pull Request Review
   - Stop execution and present structured summary to human reviewer.
```

---

## 3. Cross-Domain Interaction & Handoff Rules

1. **API Contract Changes**:
   - If a backend agent modifies an API payload, they must first update `docs/api/api-contract.md` before implementing the endpoint.
2. **Database Schema Evolution**:
   - If a database model or column changes, update `docs/database/database-schema.md` and generate an Alembic migration in `/backend/app/db/migrations/`.
3. **Formal Handoffs**:
   - Record completed work in `docs/handoffs/agent-handoffs.md` with explicit instructions and required action items for receiving agents.
