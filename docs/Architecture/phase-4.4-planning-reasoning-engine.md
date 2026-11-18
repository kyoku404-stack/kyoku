# KEEP Phase 4.4 — Planning & Reasoning Engine Architecture

**Status:** Approved & Implemented  
**Owner:** Member 1 (Goal Understanding & Plan Generation)  
**Specification Reference:** `devdocs/p4/p4.4.txt`  
**Prerequisites:** Phase 4.1 (`Multi-Agent Architecture`), Phase 4.2 (`Agent Runtime`), Phase 4.3 (`Agent Orchestration Engine`)

---

## 1. Architectural Mandate & Separation of Concerns

- **Phase 4.3 (Orchestration Engine)** executes a defined multi-agent workflow graph, tracking state, parallel branches, failures, and checkpoints over Phase 4.2 `AgentRuntime`.
- **Phase 4.4 (Planning & Reasoning Engine)** determines *what* tasks are needed to satisfy a complex natural-language user request, arranges their dependency DAG & parallel execution layers, binds each task to real Phase 4.1 registered agent capabilities, validates all 9 safety/security/budget/approval checks, persists immutable plan revisions, and hands off **only validated, authorized plans** to Phase 4.3.

**Core Security Principle (ADR-077):** The LLM proposes a structured plan, but **KEEP validates everything**. A model can never invent agents, grant itself permissions, bypass tenant boundaries, loop infinitely, or execute arbitrary code.

```
KEEP Client / FastAPI (`/api/v1/plans`)
  • KEEP Bearer JWT auth & RBAC (`agent.view`, `agent.invoke`)
        │
        ▼
KeepPlanningService (`backend/app/agents/planning/service.py`)
  1. GoalParser (`goal_parser.py`)           — NL request -> GoalSpec (+ ambiguity detection)
  2. PlanGenerator (`plan_generator.py`)     — GoalSpec -> candidate ExecutionPlan (structured JSON)
  3. TaskDecomposer & DependencyGraph        — DAG cycle check, input/output refs, parallel layers
  4. CapabilityAgentSelector                 — Resolves required capabilities via real Phase 4.1 AgentRegistry
  5. PlanValidator & KeepPlanningPolicyEngine— 9-point security, RBAC, budget, evidence & approval checks
  6. PlanRepository (`plan_repository.py`)   — Persists plans, immutable revisions, tasks, audit events
        │
        ▼  (ONLY when status == "validated" & re-authorized!)
PlanOrchestrationBridge (`orchestrator_bridge.py`)
  • Compiles ExecutionPlan execution_layers -> Phase 4.3 KeepStateGraph + RuntimeNodeInvoker
  • Submits through Phase 4.3 KeepOrchestrationService -> Phase 4.2 AgentRuntime
```

---

## 2. Planning Pipeline States & Bounded Regeneration

| Plan Status | Executable via `/execute`? | Meaning |
|---|---|---|
| `draft` | No (`409`) | Candidate plan prior to validation |
| `clarification_required` | No (`409`) | Goal is underspecified/ambiguous; returns structured `clarification_questions` |
| `validated` | **Yes** | Passed all 9 checks; eligible for Phase 4.3 submission |
| `approval_required` | No (`409`) | Contains write/sensitive/side-effecting actions; gated until Phase 4.12 HITL approval |
| `rejected` | No (`409`) | Violated graph integrity, missing capabilities, policy, RBAC, or budgets |
| `submitted` | No (`409`) | Already submitted to Phase 4.3 (`workflow_execution_id` recorded) |

Bounded Regeneration: If the initial generated plan fails structural validation or requests unavailable capabilities, `KeepPlanningService` may trigger bounded regeneration up to `max_replans` (default `2`, hard cap `3`). Exhausting the budget terminates cleanly as `rejected` — infinite loops are impossible.

---

## 3. Nine-Point Plan Validation Gate (`validator.py`)

1. **Graph Integrity:** Unique task IDs, no self-dependencies, no missing dependencies, DAG acyclicity (Kahn's topological sort).
2. **Input/Output Compatibility:** Every `input_refs` entry resolves to an `output_key` produced by a strict transitive upstream dependency.
3. **Capability Resolution:** Every required task maps to an enabled registered agent in Phase 4.1 `AgentRegistry` possessing ALL required capabilities (never trusting LLM-guessed agent names).
4. **Authorization & Tenant Isolation:** Trusted JWT `AgentContext`, prompt-injection screening via Phase 3.3 `DefaultAIGuardrailEngine`, and RBAC capability-tier checks (`read`/`write`/`sensitive`).
5. **Resource Budgets:** Enforces `max_tasks <= 20`, token budget, duration budget, parallel fan-out width, and `replan_count <= max_replans`.
6. **Evidence Requirements:** When the goal requires evidence, verifies an upstream retrieval/search task precedes synthesis/recommendation tasks.
7. **Approval Requirements:** Marks `approval_required=True` (fail-closed) whenever a task invokes a `write`/`sensitive` capability or sets `is_side_effecting=True`.
8. **Version Consistency:** Stamps `policy_version`, `plan.version`, and every resolved `agent_version`.
9. **Safe Replanning:** Revising a plan preserves immutable prior revisions, records `revision_reason`, increments `replan_count`, and re-runs authorization from scratch.

---

## 4. Extension Seams for Later Phases

- **Phase 4.5 (Research Agents):** Specialized research agents register new capabilities in Phase 4.1 `AgentRegistry`; `CapabilityAgentSelector` automatically selects them without changing Phase 4.4's planner.
- **Phase 4.12 (HITL & Approval System):** Plans marked `approval_required` expose `approval_reasons`; Phase 4.12 will attach signed approval records enabling `/execute` cleanly.
