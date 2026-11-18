# KEEP Phase 4.5 — Research Agents Architecture

**Status:** Approved & Implemented  
**Owner:** Member 1 (Research Agent Core)  
**Specification Reference:** `devdocs/p4/p4.5.txt`  
**Prerequisites:** Phase 4.1 (`AgentRegistry`), Phase 4.2 (`AgentRuntime`), Phase 4.3 (`KeepOrchestrationService`), Phase 4.4 (`KeepPlanningService`)

---

## 1. Architectural Mandate & Platform Integration

Phase 4.5 introduces KEEP's first specialized investigative agent (`research_agent`) that transforms complex multi-document questions into traceable, evidence-backed research reports while strictly reusing KEEP's existing authentication, authorization, retrieval, runtime, orchestration, and planning infrastructure.

```
KEEP Client / Frontend (`/agents/research`)
        │
        ▼
FastAPI Research API (`backend/app/api/v1/research.py`)
  • KEEP Bearer JWT auth & RBAC (`agent.view`, `agent.invoke`)
  • Re-verifies permissions on every `/report` and `/evidence` read
        │
        ▼
Phase 4.4 Planner  ──►  Phase 4.3 Orchestrator  ──►  Phase 4.2 AgentRuntime
                                                            │
                                                            ▼
                                     KeepResearchAgent (`agent_id="research_agent"`)
                                     capabilities: knowledge.research, evidence.synthesis, citation.validation
                                                            │
                                                            ▼
                                   Controlled Research Graph (`backend/app/agents/research/graph.py`)
                                     1. Retrieve authorized evidence (`KeepKnowledgeAdapter`)
                                     2. Deduplicate, sanitize untrusted passages & check coverage
                                     3. Cross-source synthesis & contradiction detection
                                     4. Citation integrity & claim-support quality validation
                                     5. Bounded self-correction (max 1 retry) or qualified partial report
                                     6. Persist run, evidence, findings & audit events
```

### Non-Negotiable Invariants
1. **Evidence Before Conclusions (ADR-080):** Every factual finding MUST cite at least one valid `evidence_id` collected during that investigation. Fabricated citation IDs are rejected by `validate_evidence_references()`.
2. **Reuse KEEP Retrieval (ADR-081):** Research retrieval wraps KEEP's existing `KeepKnowledgeAdapter` with strict tenant isolation, access-tier filtering, and untrusted-content sanitization — zero duplicate vector databases.
3. **Contradiction Transparency:** Conflicting sources are surfaced explicitly via `ContradictionRecord` and `has_contradiction=True` rather than silently averaged or hidden.
4. **No Invented Findings on Empty Evidence:** When retrieval yields zero authorized passages, the graph short-circuits cleanly to `status="insufficient_evidence"` with `findings=[]` and actionable `unresolved_questions`.
5. **Bounded Self-Correction & Re-Authorized Reads (ADR-082):** Citation correction is capped at `max_correction_attempts = 1` (preventing infinite loops), and `/report` + `/evidence` re-verify caller permissions before exposing restricted passages.

---

## 2. Controlled Research Graph Topology (`graph.py`)

```
START ──► retrieve ──► [evidence found?]
                           ├── No  ──► insufficient_evidence ──► persist ──► END
                           └── Yes ──► synthesize ──► validate_quality
                                                          ├── Valid ──► persist ──► END
                                                          └── Invalid & attempts < 1
                                                                ──► correct_once ──► validate_quality
                                                                      ├── Valid   ──► persist ──► END
                                                                      └── Invalid ──► finalize_partial ──► persist ──► END
```

---

## 3. Extension Seam for Phase 4.6 (Tool-Calling Framework)

Phase 4.5 scopes research exclusively to authorized internal KEEP knowledge sources. Phase 4.6 (`Tool-Calling Framework`) will introduce a controlled, policy-checked tool registry that Research Agents can call via `ResearchRetrievalInterface` without modifying `ResearchReport`, `EvidenceItem`, citation validation, or persistence schemas.
