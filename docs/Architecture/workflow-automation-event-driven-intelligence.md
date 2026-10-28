# Workflow Automation, Notifications & Event-Driven Intelligence Architecture (Phase 3.4)

## 1. Executive Summary & Architectural Vision
Phase 3.4 transforms KEEP from an intelligent enterprise knowledge repository into an autonomous operations platform. In modern enterprise settings, cross-functional teams execute hundreds of repetitive coordination workflows daily—document review assignments, policy approval requests, knowledge ingestion triggers, meeting summary broadcasts, and scheduled compliance audits.

Phase 3.4 introduces an enterprise event-driven automation framework that monitors organizational events in real time, routes them through a high-performance event bus, evaluates conditional business rules, orchestrates multi-step workflows, incorporates AI intelligence into process execution, coordinates human-in-the-loop approvals, and delivers contextual notifications across in-app, email, Slack, and Microsoft Teams channels.

Key capabilities include:
- **Event-Driven Pub/Sub Ingestion**: High-throughput decoupled event bus capturing user, document, project, AI, and system events with sub-100ms latency.
- **Composable Multi-Step Workflow Engine**: Directed acyclic graph (DAG) step execution with conditional branching, parallel dispatch, retry logic, timeout safeguards, and deterministic state transitions.
- **AI-Powered Autonomous Steps**: Native workflow actions for automated document summarization, duplicate detection, reviewer recommendation, department auto-tagging, and metadata extraction.
- **Multi-Channel Notification Dispatcher**: Centralized notification delivery engine supporting in-app badges, email notifications, webhooks for Slack and Microsoft Teams, real-time unread badges, and granular user preferences.
- **Human-in-the-Loop (HITL) Governance & Approvals**: Formal multi-stage approval pipelines for sensitive operations (confidential document deletion, policy publication, privilege escalation) with permanent audit trails.
- **Enterprise Cron & Scheduled Automation**: Dynamic task scheduler supporting hourly, daily, weekly, monthly, and standard 5-part cron expressions for automated maintenance and executive reporting.
- **Pre-Configured Automation Templates**: Out-of-the-box reusable enterprise templates for document review, employee onboarding, meeting briefings, and knowledge audits.
- **Telemetry, Analytics & SLA Observability**: Live metrics tracking workflow success rates, step execution latency, delivery speeds, and approval turnaround times.

---

## 2. Event-Driven System Architecture Blueprint

```
                     Enterprise Event Producers
 [User Lifecycle]   [Document Operations]   [AI Services]   [Connectors & System]
        │                     │                   │                   │
        └──────────────┬──────┴───────────────────┴───────────────────┘
                       │
                       ▼
       +───────────────────────────────────────────────+
       |         Enterprise Event Processing Bus       |
       |  (Publish-Subscribe, Event Typing, In-Memory) |
       +───────────────────────────────────────────────+
                       │
                       ▼
       +───────────────────────────────────────────────+
       |          Workflow Orchestration Engine        |
       |  (Pattern Matcher, RBAC/ABAC Gate, DAG Stepper|
       +───────────────────────────────────────────────+
         │                     │                     │
         ▼                     ▼                     ▼
+─────────────────+   +─────────────────+   +─────────────────+
|   AI Actions    |   | Business Logic  |   | Approval Gateway|
|  - Summarizer   |   |  - Role Assign  |   |  - Manager Rev. |
|  - PII Scan     |   |  - Doc Archive  |   |  - Decision Log |
|  - Reviewer Rec |   |  - Project Move |   |  - SLA Timeout  |
+─────────────────+   +─────────────────+   +─────────────────+
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                               ▼
       +───────────────────────────────────────────────+
       |        Multi-Channel Notification Router      |
       |  (In-App, Email, Slack, Teams, User Prefs)    |
       +───────────────────────────────────────────────+
                               │
                               ▼
       +───────────────────────────────────────────────+
       |        Workflow Audit & Analytics Store       |
       |  (PostgreSQL, Execution History, Prometheus)  |
       +───────────────────────────────────────────────+
```

---

## 3. Core Functional Subsystems

### 3.1 Enterprise Event Bus & Event Catalog
- **Event Schema Structure**:
  - `event_id`: UUIDv4
  - `event_type`: Hierarchical dot-separated event key (`document.uploaded`, `user.login`, `ai.summary_generated`, `connector.sync_completed`)
  - `source`: Producer domain string
  - `organization_id`: Multi-tenant quarantine identifier
  - `actor_id`: Initiator user UUID (or system)
  - `payload`: Structured JSON payload with event parameters
  - `timestamp`: UTC ISO-8601 timestamp
- **Supported Event Families**:
  - `user.*`: `user.registered`, `user.login`, `user.logout`, `user.password_reset`, `user.role_changed`
  - `document.*`: `document.uploaded`, `document.updated`, `document.deleted`, `document.classified`, `document.ocr_completed`
  - `project.*`: `project.created`, `project.task_assigned`, `project.completed`, `project.milestone_reached`
  - `ai.*`: `ai.summary_generated`, `ai.rag_completed`, `ai.graph_updated`, `ai.anomaly_detected`
  - `system.*`: `system.backup_completed`, `system.storage_warning`, `system.connector_synced`, `system.security_alert`

### 3.2 Workflow Orchestration Engine & State Machine
- **Lifecycle States**:
  - `DRAFT`: Workflow rule authored but inactive.
  - `ACTIVE`: Workflow actively listening for triggering events.
  - `RUNNING`: Execution currently processing DAG steps.
  - `WAITING_APPROVAL`: Execution paused pending manager or admin approval.
  - `COMPLETED`: All steps executed successfully.
  - `FAILED`: Execution terminated with unhandled step error.
  - `CANCELLED`: Execution halted by administrator or timeout.
- **Rule Evaluation**:
  - Evaluates matching events against predicate logic (JSON schema checks, attribute equality, numerical thresholds).
  - Validates organizational tenant boundaries and actor role permissions before initiating steps.

### 3.3 AI-Powered Automation Actions
- **AI Document Summarizer**: Automatically condenses document content upon upload and attaches executive briefings.
- **Smart Reviewer Suggester**: Analyzes document subject matter and graph node ownership to automatically assign the ideal domain expert reviewer.
- **Duplicate Document Detector**: Computes semantic embedding cosine similarities to detect and flag redundant asset uploads.
- **Department & Metadata Classifier**: Analyzes content keywords to propose appropriate taxonomy tags and departments.

### 3.4 Multi-Channel Notification Engine
- **Channels**:
  - `IN_APP`: Persistent relational record delivered to user's Notification Center with unread badges.
  - `EMAIL`: Formatted transactional email with contextual action buttons.
  - `SLACK`: Incoming webhook payload formatted with Block Kit rich cards.
  - `TEAMS`: Adaptive card payload dispatched to Microsoft Teams webhook endpoints.
- **Priority Tiers**: `LOW`, `NORMAL`, `HIGH`, `CRITICAL`.
- **User Preference Matrix**: Configurable opt-in/opt-out matrix per channel and category (Task, Approval, System, AI).

### 3.5 Human-in-the-Loop (HITL) Approvals
- Operations flagged with `requires_approval` pause execution, generate an approval ticket, and notify the designated approver.
- Supports `APPROVE` and `REJECT` actions with required review comments.
- Once approved, the workflow resumes execution of dependent downstream steps.

### 3.6 Scheduled Cron Automation
- Recurring background scheduler polling enabled cron rules.
- Supported intervals: Hourly, Daily (at specified UTC hour), Weekly (on specified day), Monthly, or custom 5-field cron syntax (`minute hour day-of-month month day-of-week`).

---

## 4. SLA & Performance Targets
- **Event Detection Latency**: < 100 ms from event emission to bus handler.
- **Workflow Initiation Latency**: < 500 ms from trigger match to first step execution.
- **Notification Delivery Latency**: < 2.0 s from step completion to recipient in-app badge update.
- **Approval Processing Latency**: < 1.0 s from user action to workflow state update.
