# Phase 4.8 — Multi-Agent Collaboration Architecture

**Document Version:** 1.0.0  
**Phase:** 4.8  
**Module:** `backend/app/agents/collaboration/` and `backend/app/collaboration/`  
**Status:** Approved  

---

## 1. Executive Summary & Core Principles

Phase 4.8 builds the collaboration layer for the KEEP (Knowledge Intelligence Platform) that enables multiple specialized agents (e.g. Research, Analysis, Review, Synthesis) to work collectively on shared complex enterprise objectives.

Unlike basic multi-agent setups that permit unstructured, conversational loops between LLMs, KEEP enforces **bounded, traceable, evidence-backed, and permission-aware** collaboration.

### Key Architectural Tenets:
1. **Shared Objectives & Explicit Task Ownership:** Every collaboration session operates under a validated high-level objective. Subtasks are assigned to registered Phase 4.1 agents with strict prerequisites, inputs, statuses, and bounded execution attempts.
2. **Controlled Message Routing:** Agents NEVER invoke or message each other directly over raw network sockets or unrestricted chat streams. All communication flows through a central `CollaborationMessageService` enforcing schema validation, role capabilities, tenant isolation, and audit logging.
3. **Evidence-Backed Findings:** Findings submitted by agents must link to verified KEEP evidence records (`evidence_refs`). The platform guarantees that source access rights are verified before citations enter collaborative state.
4. **Peer Review & Deterministic Conflict Resolution:** Completed findings undergo peer review. Conflicting claims between agents (e.g. conflicting metrics or contradictory root-cause analyses) are explicitly surfaced as `CollaborationConflict` entities, routed through bounded revision cycles, or transparently declared in the final synthesis report with explicit uncertainty boundaries.
5. **Separation of Collaboration vs Orchestration:** Phase 4.3 coordinates workflow execution step-by-step; Phase 4.8 defines how specialized agents exchange context, peer-review findings, and resolve disagreements within that workflow.

---

## 2. Multi-Agent Collaboration Lifecycle

```
[Authenticated Client Request]
         | (POST /api/v1/collaborations)
         v
+-----------------------------------------------------------------------------------+
|                        CollaborationSession Initialized                           |
|   (session_id, tenant_id, requested_by, objective, max_agents, require_review)   |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                           LangGraph Collaboration Graph                           |
|                                                                                   |
|  1. DISPATCH TASKS  -------------------> Research Agent (Grounded Evidence)       |
|                                          |                                        |
|  2. SHARE FINDINGS  <-------------------+ Evidence References + Provenance        |
|         |                                                                         |
|         v                                                                         |
|  3. EXECUTE ANALYSIS ------------------> Analysis Agent (Interpretation)         |
|         |                                                                         |
|         v                                                                         |
|  4. PEER REVIEW     ------------------> Review Agent (Claim & Citation Integrity) |
|         |                                                                         |
|         +---> [Accepted] --------------> 6. SYNTHESIZE REPORT                    |
|         |                                   (Synthesis Agent - Consolidated)      |
|         +---> [Needs Revision] --------> 5. BOUNDED REVISION (Max 2 Attempts)    |
|         |                                                                         |
|         +---> [Conflict Detected] -----> 5. CONFLICT RESOLVER                     |
|                                             - Deterministic Evidence Check        |
|                                             - Unresolved Contradictions Declared  |
|                                             - Escalated for Human Review if needed|
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                             Final Collaboration Report                            |
|     (Executive Summary, Grounded Findings, Limitations, Open Contradictions)      |
+-----------------------------------------------------------------------------------+
```

---

## 3. Core Subsystems & Responsibilities

| Subsystem | File / Component | Primary Responsibilities |
|---|---|---|
| **Session Manager** | `session_manager.py`, `service.py` | Creates and tracks `CollaborationSession` records, limits participants (1–8), manages terminal state transitions (`completed`, `failed`, `cancelled`). |
| **Task Dispatcher** | `task_dispatcher.py` | Dispatches subtasks to registered agents (`research_agent`, `analysis_agent`, `review_agent`, `synthesis_agent`), manages dependency graphs and retry counts. |
| **Messaging & Routing** | `messaging.py` | Validates, sanitizes, and persists `CollaborationMessage` items with correlation tracking and secret redaction. |
| **Findings Catalog** | `findings.py` | Records `CollaborationFinding` items, verifies evidence references, and preserves provenance. |
| **Peer Review** | `review.py` | Evaluates claims and citations, producing `ReviewResult` (`accepted`, `rejected`, `needs_revision`, `conflict_detected`). |
| **Conflict Resolution** | `conflict_resolution.py` | Detects contradictory assertions, applies deterministic resolution rules, and escalates unresolvable disputes without dropping them. |
| **LangGraph Workflow** | `graph.py` | Coordinates the end-to-end multi-agent execution pipeline. |
| **REST API** | `backend/app/api/v1/collaboration.py` | Exposes authenticated, tenant-isolated endpoints for starting sessions, querying progress, and submitting human conflict resolutions. |

---

## 4. Zero-Trust Security & Multi-Tenancy

- **Verified Context Exclusivity:** All sessions, tasks, messages, findings, reviews, and conflict resolutions require verified JWT identity (`tenant_id`, `user_id`, `roles`).
- **Cross-Tenant Boundary Enforcement:** Repository queries, message deliveries, and task dispatching verify `tenant_id` at the database index level. Cross-tenant access is rejected with `COLLABORATION_TENANT_ISOLATION_VIOLATION`.
- **Secret Redaction:** Communication payloads are screened for API keys, bearer tokens, and credentials before persistence.
