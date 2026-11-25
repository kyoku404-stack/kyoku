# Phase 4.11 — Proactive Enterprise Intelligence Architecture

## 1. Overview & Objectives
Phase 4.11 upgrades KEEP from reactive Q&A and event-triggered execution into a proactive enterprise intelligence platform. Rather than alerting on every change, KEEP monitors authorized knowledge sources, compares versions and historical context, validates evidence and provenance, deduplicates and ranks candidates, enforces tenant/RBAC governance, and surfaces ranked, evidence-backed insights to authorized users.

### Responsibility Boundaries
- **Phase 4.9 (Autonomous Workflow Engine):** Adapts execution toward a defined goal.
- **Phase 4.10 (Event-Driven Agents):** Initiates approved workflows from events and schedules.
- **Phase 4.11 (Proactive Intelligence):** Evaluates observed changes and patterns to determine what merits attention, why it matters, and who is authorized to see it.
- **Phase 4.12 (Human-in-the-Loop):** Deferred — approval workflows remain handled by Phase 4.3/4.9 when explicitly triggered.

---

## 2. Layered Module Architecture
Implemented under `backend/app/agents/intelligence/` and `backend/app/agents/intelligence_detectors/` (with compatibility re-exports in `backend/app/intelligence/` and `backend/app/intelligence_detectors/`):

```
Authorized Sources (Documents, Versions, Knowledge Graph, Research Runs, Phase 4.10 Events)
  │
  ▼
IntelligenceDetectors (SignificantChange, KnowledgeGap, Contradiction, Staleness, EmergingTrend)
  │  -> Produce bounded IntelligenceCandidate records (facts separated from explanations)
  ▼
EvidenceValidator & Provenance Checks
  │  -> Verify evidence refs exist & caller/audience authorized; mark missing evidence as limitations
  ▼
Deduplication & Suppression Engine
  │  -> Unique deduplication keys + scoped cooldown windows
  ▼
Prioritization & Ranking Engine
  │  -> Deterministic S = 100(0.30I + 0.25R + 0.25E + 0.10U + 0.10N)
  ▼
IntelligencePolicyEngine (Zero-Trust Tenant, RBAC, Source Re-check & Redaction)
  │
  ▼
Intelligence Feed, Feedback, Dismiss/Resolve Lifecycle & Optional Approved Workflow Investigation
```

---

## 3. Core Contracts & Lifecycle
- **Categories (`InsightCategory`):** `knowledge_gap`, `contradiction`, `stale_knowledge`, `significant_change`, `emerging_trend`
- **Statuses (`InsightStatus`):** `candidate` → `validated` → `published` | `suppressed` | `withheld` → `investigating` | `dismissed` | `resolved`
- **Feedback Values (`FeedbackType`):** `useful`, `irrelevant`, `already_known`, `incorrect`, `needs_more_evidence`
- **Suppression Scopes:** `tenant`, `audience`, `user` (per-user dismissals do not alter organization-wide insight visibility for other authorized users unless org-wide resolution/dismissal is requested by an authorized role).

---

## 4. Security & Zero-Trust Invariants
1. `tenant_id`, `user_id`, and `roles` always derive from KEEP's verified JWT/auth context.
2. Evidence references (`evidence_refs`) store pointers rather than duplicating restricted document text into insight records.
3. Source access is re-checked when an insight or its evidence is viewed (`GET /insights/{id}`, `GET /insights/{id}/evidence`), ensuring revoked permissions immediately block access.
4. Detectors failing during a scan are recorded in `intelligence_runs.detector_errors` without silently losing the run.
5. An insight never autonomously launches unapproved workflows or bypasses Phase 4.3/4.6 authorization.
