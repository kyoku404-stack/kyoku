# Enterprise AI Assistant & Agentic Workflows Architecture Specification

> **Specification Reference**: `devdocs/p2/p2.3.txt` (Chapters 1–20)  
> **Phase**: Phase 2.3 — Enterprise AI Assistant, Agentic Workflows & Intelligent Task Automation  
> **Author**: Member 1 (Project Lead & AI Architect)  
> **Status**: APPROVED & ACTIVE  
> **ADRs**: ADR-038, ADR-039, ADR-040  

---

## 1. Executive Summary & Vision

In Phase 2.2, KEEP established enterprise Retrieval-Augmented Generation (RAG) for grounded Question-Answering with verifiable citations. Phase 2.3 elevates KEEP from a reactive question-answering system into an **Agentic AI Assistant Platform**. 

The Enterprise AI Assistant acts as an intelligent digital coworker capable of:
1. Understanding complex natural language instructions and user intent.
2. Formulating multi-step execution plans represented as Directed Acyclic Graphs (DAGs).
3. Invoking enterprise platform tools (Document, Semantic Search, Analytics, Reporting, User, Project, Notification).
4. Enforcing strict Role-Based Access Control (RBAC) and tenant isolation across all tool calls.
5. Gating destructive or sensitive operations behind Human-in-the-Loop (HITL) approval workflows.
6. Generating rich organizational reports (meeting summaries, weekly rollups, department analytics).
7. Proactively suggesting optimizations (duplicate knowledge, inactive projects, missing documentation).

```
                            [ User Request ]
                                   │
                                   ▼
                       ┌───────────────────────┐
                       │ Intent Detection & NLU │
                       └───────────┬───────────┘
                                   │
                                   ▼
                       ┌───────────────────────┐
                       │   DAG Task Planner    │
                       └───────────┬───────────┘
                                   │
                                   ▼
                       ┌───────────────────────┐
                       │   Execution Engine    │
                       └───────────┬───────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
 ┌──────────────┐          ┌──────────────┐           ┌──────────────┐
 │  RAG Search  │          │  Enterprise  │           │  Approval    │
 │    Tool      │          │  Tools API   │           │  Gate (HITL) │
 └──────┬───────┘          └──────┬───────┘           └──────┬───────┘
        │                         │                          │
        └─────────────────────────┼──────────────────────────┘
                                  │
                                  ▼
                       ┌───────────────────────┐
                       │  Response Generator   │
                       └───────────┬───────────┘
                                   │
                                   ▼
                       [ UI Command Center ]
```

---

## 2. Natural Language Understanding (NLU) Pipeline

Every incoming user instruction traverses a deterministic 5-stage NLU pipeline:

```
[Raw Input] ──> [1. Language Normalization] ──> [2. Intent Classification] 
            ──> [3. Entity Extraction]      ──> [4. Context Resolution] 
            ──> [5. Task Plan Formulation]
```

### 2.1 Intent Classification Hierarchy
Requests are categorized into one of six core intents:

| Intent Enum | Description | Primary Route |
| :--- | :--- | :--- |
| `KNOWLEDGE_QA` | Natural language questions on policies, facts, or guidelines | RAG Search Engine |
| `DOCUMENT_SUMMARIZATION` | Summarizing uploaded files, contracts, or sections | Document Tool + LLM Summarizer |
| `REPORT_GENERATION` | Aggregating data into structured reports (Weekly, Project, KPI) | Report Tool + Analytics Engine |
| `ACTION_EXECUTION` | Performing state-mutating actions (inviting users, tags) | Enterprise Tool Suite |
| `RECOMMENDATION_DISCOVERY`| Proactive knowledge health and optimization queries | Recommendation Engine |
| `CONVERSATIONAL_FOLLOWUP`| Continuing context from a prior multi-turn exchange | Session Memory Router |

### 2.2 Entity Extraction
The NLU engine extracts structured slots:
- `document_identifiers`: Titles, filenames, or chunk UUIDs.
- `temporal_filters`: Date ranges (e.g., "last month", "Q3 2026", "yesterday").
- `department_or_project`: Department names or project tags.
- `action_type`: Specific operations requested (`export`, `delete`, `invite`, `summarize`).

---

## 3. Task Planning & DAG Workflow Orchestration

Complex multi-step user prompts are translated into a sequence of atomic tasks structured as a Directed Acyclic Graph (DAG).

### 3.1 Task Graph Structure
Each node in the DAG represents an atomic executable step:
- `step_id`: Unique integer index.
- `tool_name`: Identifier in the tool registry.
- `input_parameters`: Mapped from user prompt or prior task outputs.
- `dependencies`: List of `step_id`s that must complete before execution.
- `requires_approval`: Boolean flag indicating whether human confirmation is required.
- `retry_policy`: Max retries with exponential backoff.

### 3.2 Dynamic Tool Registry
The system provides a unified registry of enterprise tools:

```
                               ┌─────────────────────────┐
                               │  BaseTool Registry      │
                               └────────────┬────────────┘
         ┌───────────────────┬──────────────┴──────────────┬───────────────────┐
         ▼                   ▼                             ▼                   ▼
┌─────────────────┐ ┌─────────────────┐           ┌─────────────────┐ ┌─────────────────┐
│  DocumentTool   │ │   SearchTool    │           │  AnalyticsTool  │ │   ReportTool    │
│ (Fetch, Filter) │ │ (Hybrid RAG)    │           │ (KPIs, Trends)  │ │ (Markdown/PDF)  │
└─────────────────┘ └─────────────────┘           └─────────────────┘ └─────────────────┘
         ▲                   ▲                             ▲                   ▲
         │                   │                             │                   │
┌─────────────────┐ ┌─────────────────┐           ┌─────────────────┐ ┌─────────────────┐
│    UserTool     │ │   ProjectTool   │           │NotificationTool │ │ ComplianceTool  │
│(Profiles, Roles)│ │(Status, Members)│           │ (Alerts, Emails)│ │ (Audit, Policy) │
└─────────────────┘ └─────────────────┘           └─────────────────┘ └─────────────────┘
```

Each tool implements a strict interface:
- `name`: Tool identifier string.
- `description`: Self-describing schema for LLM tool selection.
- `category`: Functional domain (`KNOWLEDGE`, `ANALYTICS`, `ADMINISTRATION`, `PRODUCTIVITY`).
- `required_permissions`: RBAC permissions checked before invocation.
- `is_destructive`: Triggers HITL gating if `True`.
- `execute(parameters, security_context)`: Async execution method.

---

## 4. Human-in-the-Loop (HITL) Approval Gating

To safeguard enterprise data, operations classified as destructive, irreversible, or policy-critical cannot be executed autonomously without human confirmation.

### 4.1 Safety Gating Policy
Operations requiring explicit human sign-off:
1. Deleting or archiving documents.
2. Removing users or changing enterprise RBAC role assignments.
3. Archiving or deleting project workspaces.
4. Modifying tenant-wide security policies.
5. Exporting unredacted confidential analytics.

### 4.2 Two-Phase Approval Workflow
```
[Task Planner] ──> Detect Destructive Tool
               ──> Create AssistantApproval Record (Status: PENDING)
               ──> Yield Execution with WAITING_APPROVAL Status
               ──> Emit Notification to Authorized Approver
               ──> [User Reviews in UI Modal]
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
    [APPROVED]               [REJECTED]
         │                       │
         ▼                       ▼
  Resume Execution         Abort Step with
  Commit Mutation          AUDIT_REJECTED Log
```

---

## 5. Conversational Memory & State Management

The assistant maintains structured context across multi-turn interactions:

1. **Short-Term Session Memory**:
   - Rolling window of previous prompts and synthesized responses.
   - Active workflow state (active steps, completed outputs, pending approvals).
   - Temporary entity context (e.g., active document being discussed).
2. **Long-Term Enterprise Memory**:
   - User interaction preferences (preferred report format, department scope).
   - Historical workflow completion logs.
3. **Tenant Boundary Guarantee**:
   - Memory is strictly partitioned by `organization_id` and `user_id`.
   - Cross-tenant context leakage is mathematically prevented.

---

## 6. Enterprise Report Generation Engine

The assistant automates the synthesis of multi-source organizational reports:

### 6.1 Supported Report Types
- `MEETING_SUMMARY`: Action items, decisions made, attendee follow-ups.
- `WEEKLY_ROLLUP`: Department activities, new documents ingested, query metrics.
- `PROJECT_STATUS`: Milestones, blocker analysis, recent document contributions.
- `DEPARTMENT_ANALYTICS`: Knowledge base usage, top queries, unanswered topics.
- `KNOWLEDGE_SYNTHESIS`: Multi-document executive briefings.

### 6.2 Output Formats
- `MARKDOWN`: Interactive structured document rendered directly in the UI.
- `PDF`: Printable executive summary.
- `DOCX`: Editable word processing document.

---

## 7. Proactive Recommendation Engine

The assistant continuously mines enterprise telemetry to deliver actionable recommendations:
1. **Frequently Accessed Documents**: Surfaces trending policies and specs.
2. **Knowledge Gaps**: Detects recurring user queries with low RAG confidence.
3. **Duplicate Knowledge Detection**: Identifies overlapping document uploads.
4. **Inactive Projects & Stale Docs**: Highlights workspaces without activity in >90 days.

---

## 8. Multi-Agent Framework (Future Roadmap)

In future phases, the monolithic assistant orchestrator will decompose into specialized autonomous agents:
- `KnowledgeAgent`: Handles deep semantic exploration and RAG synthesis.
- `DocumentAgent`: Manages document lifecycle, OCR, and classification.
- `AnalyticsAgent`: Computes statistical aggregates and anomaly detection.
- `ComplianceAgent`: Verifies policy alignment and GDPR/SOC2 constraints.
