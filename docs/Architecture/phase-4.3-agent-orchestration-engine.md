# KEEP Phase 4.3 — Agent Orchestration Engine Architecture

**Status:** Approved & Implemented  
**Owner:** Member 1 (Orchestration Architecture & Workflow Registry)  
**Specification Reference:** `devdocs/p4/p4.3.txt`  
**Prerequisites:** Phase 4.1 (`Multi-Agent Architecture`), Phase 4.2 (`Agent Runtime & Execution Engine`)

---

## 1. Architectural Mandate & Separation of Concerns

Phase 4.2 executes an **individual agent invocation** (`AgentRuntime`). Phase 4.3 coordinates **multiple registered agents** into deterministic sequential, conditional, and parallel workflows while keeping KEEP in full ownership of workflow definitions, security boundaries, persistence, and observability.

```
KEEP Client / Caller
        │
        ▼
FastAPI Workflow API (`backend/app/api/v1/agent_workflows.py`)
  • KEEP Bearer JWT auth & RBAC (`agent.view`, `agent.invoke`, `agent.manage`)
  • Request validation, Idempotency-Key scoping, canonical ApiResponse envelopes
        │
        ▼
KeepOrchestrationService (`backend/app/agents/orchestration/service.py`)
  ├── WorkflowRegistry (`workflow_registry.py`) — version-pinned approved workflows
  ├── KeepWorkflowPolicyEngine (`policies.py`) — budgets, timeouts, RBAC, cancellation
  ├── WorkflowFailureHandler (`failure_handling.py`) — required vs optional failure rules
  └── WorkflowRecoveryManager (`recovery.py`) — checkpoint resume with mandatory re-auth
        │
        ▼
LangGraph-Compatible Graph Adapter (`backend/app/agents/adapters/langgraph_orchestrator.py`)
  • Typed WorkflowState + explicit branch reducers (no parallel state clobbering)
  • Sequential edges, conditional routing, asyncio.gather parallel fan-out/fan-in
  • Per-node secret-safe checkpointing via KeepGraphCheckpointStore
        │
        ▼  (ALL agent calls routed through RuntimeNodeInvoker — NEVER direct agent.invoke)
KEEP AgentRuntime — Phase 4.2 (`backend/app/agents/runtime/executor.py`)
  • Enforces per-agent policies, timeouts, concurrency limits, retries
  • Persists individual `agent_executions` rows linked to `agent_workflow_steps`
        │
        ▼
Registered KEEP Agents (`AgentRegistry` — Phase 4.1 + 4.2 + 4.3 specialists)
```

### Non-Negotiable Boundary Invariants
1. **No Runtime Bypass:** Graph nodes MUST invoke agents through `RuntimeNodeInvoker` → Phase 4.2 `AgentRuntime.submit(...)`, ensuring every step produces a durable `agent_executions` record linked via `agent_workflow_steps`.
2. **Version Pinning:** Every `WorkflowExecutionRecord` pins `(workflow_id, workflow_version)` at submission time. Disabling a workflow or deploying a newer version never mutates in-flight runs.
3. **Approved Workflows Only:** Clients submit requests to pre-registered `workflow_id` identifiers; arbitrary client-supplied Python code or graph topologies are strictly forbidden.
4. **Zero-Trust Context:** `tenant_id`, `user_id`, `roles`, and `permissions` come exclusively from KEEP's verified JWT `AuthenticatedUser`. Resumed workflows re-verify current caller permissions before executing any subsequent node.
5. **Explicit Partial-Success Semantics:** Required branch failures terminate the workflow as `FAILED`; optional branch failures under `allow_partial_success=True` record structured warnings and resolve to `PARTIALLY_SUCCEEDED`.

---

## 2. Workflow vs. Individual Execution Records

| Dimension | Workflow Execution (`agent_workflow_executions`) | Agent Execution (`agent_executions`) |
|---|---|---|
| Granularity | Complete multi-agent workflow run | Single agent invocation attempt |
| Identity | `workflow_execution_id` (`wfexec_*`), `workflow_id`, `workflow_version` | `execution_id` (`exec_*`), `agent_id`, `agent_version` |
| Lifecycle States | `PENDING`, `RUNNING`, `SUCCEEDED`, `PARTIALLY_SUCCEEDED`, `FAILED`, `CANCELLED`, `TIMED_OUT` | `PENDING`, `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `TIMED_OUT`, `CANCELLED` |
| Linkage | `agent_workflow_steps` links each node to `agent_execution_id` | Shares parent `correlation_id` |
| Checkpoints | `KeepGraphCheckpointStore` scoped to `wf:{tenant_id}:{workflow_execution_id}` | `KeepCheckpointStore` scoped to `{tenant_id}:{task_id}` |

---

## 3. Built-In Phase 4.3 Multi-Agent Workflows

1. **`knowledge_analysis` (`v1.0.0`)** — Sequential + Conditional Routing:
   - `retrieve` (`knowledge_retrieval`) → `route_after_retrieval` → `analyze` (`knowledge_analysis`) OR `no_evidence` → `aggregate`.
   - Proves sequential validated output handoff and conditional limited-evidence handling without hallucination.
2. **`parallel_project_review` (`v1.0.0`)** — Sequential + Conditional + Parallel Fan-Out/Fan-In:
   - `retrieve` (`knowledge_retrieval`) → `route_after_retrieval` → parallel `[extract_decisions (decision_extractor), analyze_risks (risk_analyzer)]` OR `no_evidence` → `aggregate`.
   - Proves concurrent branch execution with reducer-safe state merging and explicit partial-success policy when an optional branch fails.

---

## 4. Extension Seam for Phase 4.4 (Planning & Reasoning Engine)

Phase 4.3 deliberately defers autonomous dynamic planning to Phase 4.4 (`devdocs/p4/p4.4.txt`). The frozen seam between Phase 4.3 and Phase 4.4 is:
- **Planner Output Contract:** Phase 4.4 will emit a validated `ExecutionPlan` referencing only registered `agent_id`s and approved capabilities.
- **Orchestrator Execution Contract:** Phase 4.4 compiles or dispatches its plan through `KeepOrchestrationService` / `KeepStateGraph` + `RuntimeNodeInvoker` without bypassing `KeepWorkflowPolicyEngine`, `AgentRuntime`, or `WorkflowRepositoryInterface`.
- **Zero Redesign Guarantee:** `WorkflowDefinition`, `WorkflowState`, `WorkflowExecutionRecord`, `WorkflowStepLink`, `KeepWorkflowPolicyEngine`, and `KeepGraphCheckpointStore` remain unchanged when Phase 4.4 introduces dynamic planning nodes.
