# Phase 4.7 — Agent Memory System Architecture

**Document Version:** 1.0.0  
**Phase:** 4.7  
**Module:** `backend/app/agents/memory/` and `backend/app/memory/`  
**Status:** Approved  

---

## 1. Executive Summary & Core Principles

Phase 4.7 introduces an enterprise-grade, controlled agent memory system for the KEEP (Knowledge Intelligence Platform). Rather than treating every agent invocation as an isolated stateless prompt, or conversely dumping raw conversations and unverified tool outputs into permanent storage, KEEP implements a multi-tiered, policy-governed memory subsystem.

### Key Architectural Tenets:
1. **Memory is NOT the Knowledge Base:** The organizational knowledge base stores authoritative source material; memory stores curated, selected context and working preferences that accelerate and optimize future tasks.
2. **Zero-Trust Multi-Tenancy:** Every memory record, proposal, and search query is strictly isolated by `tenant_id` derived exclusively from server-verified JWT claims. Cross-tenant leakage or parameter spoofing is physically prevented at database and repository levels.
3. **Discrete Scopes & Ownership:** No universal memory bucket exists. Memory is segmented into:
   - **User Scope:** User preferences and persistent personal working context (e.g. preferred report style). Inaccessible to other users by default.
   - **Organization Scope:** Shared operational context across authorized team members, requiring explicit publication privileges and administrative review.
   - **Workflow Scope:** Intermediate results, state references, and continuity context bound to workflow executions.
   - **Agent Working Context:** Ephemeral in-run context that expires upon task termination and does not enter permanent storage without validation.
4. **Two-Phase Lifecycle (Propose-First Architecture):** Agent runs cannot write directly to active memory. Instead, agents propose memory candidates. A policy and governance engine validates provenance, screens for prompt injections and secrets, verifies confidence, and approves or routes to human review.
5. **Context Budgeting & Relevance Decay:** Retrieval limits candidate context based on composite relevance: lexical/token overlap, recency decay, source reliability, and strict token budget enforcement to protect downstream LLM context windows.

---

## 2. Multi-Tier Scope Architecture

| Memory Scope | Target Owner (`owner_id`) | Default TTL | Visibility & Clearance | Modification / Approval Rights |
|---|---|---|---|---|
| `user` | User ID (`user_id`) | 90 days (renewable) | Owning user only (and tenant Org Admin) | User or tenant Org Admin |
| `organization` | Organization ID (`tenant_id`) | 180 days | All authorized members within the tenant | Org Admin or designated Memory Publisher |
| `workflow` | Workflow Execution ID (`workflow_execution_id`) | 7 days | Workflow participants and linked continuations | Automated / Orchestration Engine |
| `agent` | Agent Execution ID (`agent_execution_id`) | 24 hours | Agent execution runtime during execution | Agent runtime; auto-expires unless proposed |

---

## 3. High-Level System Architecture

```
+-----------------------------------------------------------------------------------+
|                           KEEP Authenticated Client                               |
|                  (Verified JWT: tenant_id, user_id, roles)                        |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                           FastAPI Memory Layer (/api/v1/memory)                   |
|   - POST /search  - GET /{id}  - POST /proposals  - POST /{id}/approve | reject    |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                  MemoryService                                    |
|   Coordinates storage, retrieval, lifecycle, and policy enforcement              |
+-------------------+---------------------+--------------------+--------------------+
                    |                     |                    |
                    v                     v                    v
         +--------------------+  +------------------+  +--------------------+
         | MemoryPolicyEngine |  | RetrievalService |  | ConsolidationEngine|
         | - Tenant Isolation |  | - Scoped Search  |  | - Conflict Check   |
         | - RBAC Clearance   |  | - Lexical/Vector |  | - Deduplication   |
         | - Injection Filter |  | - Recency Decay  |  | - Version History  |
         | - Secret Masking   |  | - Token Budget   |  | - Superseding      |
         +--------------------+  +------------------+  +--------------------+
                    |                     |                    |
                    +---------------------+--------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                            SqlAlchemyMemoryRepository                             |
|   PostgreSQL / SQLite Persistence with Foreign Keys and Tenant Indexes            |
|   - memories (Canonical active, proposed, expired, deleted records)              |
|   - memory_proposals (Agent & user submissions awaiting governance)              |
|   - memory_versions (Historical lineage and superseding provenance)               |
|   - memory_access_events (Append-only audit trail with correlation IDs)           |
+-----------------------------------------------------------------------------------+
```

---

## 4. Two-Phase Lifecycle & Governance

```
Agent / User Invocation
         |
         v
1. PROPOSE  ----->  Create MemoryProposal (status: pending, origin, confidence)
         |
         v
2. VALIDATE ----->  Policy Engine:
                    - Tenant isolation check
                    - Prompt injection detection
                    - Secret / credential screening (Bearer, sk-*, passwords)
                    - Content length validation (1 - 4000 chars)
         |
         +---------------------------------------+
         |                                       |
    [Passes Rule]                           [Fails Rule]
         |                                       |
         v                                       v
3. APPROVE / AUTO-APPROVE                 REJECT (status: rejected)
   - User-submitted preference: Auto      Audit event logged with reason
   - Model-generated insight: Gated
         |
         v
4. CONSOLIDATE & ACTIVATE
   - Check duplicate hash (SHA256)
   - Detect conflicting memory
   - If conflict: supersede previous version (link `superseded_by`)
   - Insert MemoryRecord (status: active)
         |
         v
5. RETRIEVAL & CONTEXT INJECTION
   - Scoped query by tenant + owner
   - Filter active and non-expired records
   - Rank by relevance * recency_decay * confidence
   - Fit within Token Budget (e.g. 1000 tokens)
         |
         v
6. RETENTION & DELETION
   - Expiration cron/service updates expired records
   - Explicit DELETE sets status=deleted, deleted_at=now()
   - Immediate search index invalidation
```

---

## 5. LangGraph & Agent Runtime Integration

In LangGraph workflows, memory operations are encapsulated in declarative nodes:
- `load_memory_node`: Queries `MemoryService` using the runtime's server-generated `security_context`. Appends relevant memories to graph state (`state["relevant_memories"]`).
- `propose_memory_node`: Inspects graph outputs for candidate reusable learnings (`state["memory_proposal"]`). Forwards proposal to `MemoryService.propose(...)` and populates `state["memory_proposal_id"]`.
- Separation of Concerns: Workflow checkpoints (`agent_checkpoints`) manage resume/retry state; `MemoryService` manages persistent cross-execution context.

---

## 6. Observability & Audit Trail

All memory operations generate structured events in `memory_access_events`:
- `event_id`: Unique event identifier
- `action`: `retrieve`, `propose`, `approve`, `reject`, `update`, `expire`, `delete`
- `allowed`: Boolean authorization outcome
- `denial_reason`: Error code if denied
- Redacted payload: No secret content or unmasked tokens logged.
- Correlation tracking: `correlation_id` propagated across LangGraph and FastAPI requests.
