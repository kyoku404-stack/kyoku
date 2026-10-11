# Master Organizational Hierarchy, Multi-Tenancy & AI Workspace Architecture Specification

> **Phase 1.5 Architectural Blueprint: Organization, Team & Workspace Management**  
> **Author**: Member 1 (Project Lead & AI Architect)  
> **Target Audience**: Member 2 (Backend Lead), Member 3 (Frontend Lead), Member 4 (DevOps Lead)  
> **Specification Reference**: `devdocs/p1/p1.5.txt` (Chapters 1–21)  
> **Status**: APPROVED & LOCKED FOR PHASE 1.5 IMPLEMENTATION  

---

## 1. Executive Summary & Architectural Goals

The KEEP platform is built from the ground up as an enterprise-grade, multi-tenant knowledge management and artificial intelligence retrieval system. Unlike personal productivity or single-tenant applications, KEEP organizes all human intelligence, operational workflows, and unstructured knowledge assets within a strict, hierarchical enterprise structure.

Every resource—from raw uploaded PDFs and meeting audio recordings to vector chunks, Knowledge Graph semantic nodes, and conversational AI session histories—is strictly owned by an organization and scoped across departments, teams, and projects.

### Core Objectives for Phase 1.5:
1. **Multi-Tenant Structural Hierarchy**: Formalize the 4-tier organizational taxonomy:
   $$\text{Organization} \longrightarrow \text{Departments} \longrightarrow \text{Teams} \longrightarrow \text{Projects} \longrightarrow \text{Knowledge Resources}$$
2. **Hard Multi-Tenant Isolation**: Implement zero-trust cryptographic and database-level tenancy barriers, guaranteeing absolute data quarantine between enterprise tenants.
3. **Multi-Tier Context Scoping for AI Memory**: Define how AI queries and retrieval mechanisms dynamically navigate organizational levels to provide relevant context without privacy leakage.
4. **Hierarchical RBAC Permission Governance**: Extend the Phase 1.4 RBAC engine with granular organizational lifecycle permissions (`org:*`, `dept:*`, `team:*`, `project:*`, `invitation:*`, `member:*`).
5. **Standardized API & Persistence Blueprint**: Provide the formal architectural baseline for Backend (Member 2), Frontend (Member 3), and DevOps/QA (Member 4) execution.

---

## 2. Master Organizational Hierarchy Architecture

### 2.1 The 4-Tier Hierarchy Blueprint

The platform models enterprise organizations as a directed containment tree:

```
                            ┌────────────────────────┐
                            │      Organization      │
                            │   (Root Tenant Unit)   │
                            └───────────┬────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    │                                       │
        ┌───────────▼───────────┐               ┌───────────▼───────────┐
        │      Departments      │               │   Global Workspaces   │
        │ (Functional Division) │               │   & Enterprise Docs   │
        └───────────┬───────────┘               └───────────────────────┘
                    │
        ┌───────────▼───────────┐
        │         Teams         │
        │  (Collaborative Unit) │
        └───────────┬───────────┘
                    │
        ┌───────────▼───────────┐
        │       Projects        │
        │  (Goal-Bound Sandbox) │
        └───────────┬───────────┘
                    │
    ┌───────────────┼───────────────┬───────────────┐
    │               │               │               │
┌───▼───┐       ┌───▼───┐       ┌───▼───┐       ┌───▼───┐
│ Docs  │       │ Tasks │       │ Meets │       │ AI KG │
└───────┘       └───────┘       └───────┘       └───────┘
```

### 2.2 Entity Characteristics and Semantics

| Level | Entity | Scope & Role | Lifecycle & Governance | AI Knowledge Context |
| :--- | :--- | :--- | :--- | :--- |
| **Level 0** | **Organization** | Top-level tenant container. Represents the legal or corporate entity (e.g. Acme Corp). | Created by Org Admin during onboarding. Controls enterprise settings, billing quotas, and security policies. | Forms the **Hard Boundary**. Vector search and LLM context will NEVER cross this boundary under any circumstance. |
| **Level 1** | **Department** | Broad functional business unit (e.g., Engineering, Human Resources, Sales, Legal, Finance). | Managed by Department Managers and Org Admins. Groups related teams and high-level departmental initiatives. | Scopes department-wide policies, handbooks, compliance manuals, and cross-team knowledge. |
| **Level 2** | **Team** | Operational unit executing shared charters (e.g., Backend Team, Frontend Team, AI Research Team). | Led by Team Leads. Contains members, shared team documents, and assigned projects. | Scopes operational team meetings, sprint retrospectives, internal guides, and domain FAQs. |
| **Level 3** | **Project** | Focused, time-bound, or outcome-bound collaborative workspace (e.g., "Project Helios", "Q4 Security Audit"). | Created by Project Managers or Members. Contains specific documents, meetings, tasks, and discussions. | Forms the **Primary Retrieval Focus**. AI queries within a project workspace prioritize project documents first. |

---

## 3. Multi-Tenant Isolation & Zero-Trust Quarantine

### 3.1 Multi-Tenancy Model: Scoped Logical Partitioning

KEEP utilizes a **row-level multi-tenant logical partitioning model** with enforced PostgreSQL relational foreign keys, composite unique constraints, and cryptographic JWT claim gating.

```
                           ┌─────────────────────────┐
                           │   Incoming HTTP / SSE   │
                           │   Authorization Header  │
                           └────────────┬────────────┘
                                        │
                                        ▼
                           ┌─────────────────────────┐
                           │   FastAPI Dependency    │
                           │  `get_current_user()`   │
                           │  Extract `org_id` Claim │
                           └────────────┬────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    │                                       │
                    ▼                                       ▼
       [Relational Persistence]               [AI / Vector Retrieval]
    SELECT * FROM documents                 SELECT chunk_id FROM document_chunks
    WHERE organization_id = :org_id         WHERE organization_id = :org_id
      AND is_deleted = FALSE;                 AND project_id = :project_id;
```

### 3.2 Tenant Isolation Defense in Depth

1. **Authentication Layer**:
   - The user's signed JWT contains an immutable `org_id` claim.
   - The token signature is verified on every request using asymmetric public keys or cryptographic secret rotation.
2. **FastAPI Tenant Dependency**:
   - `TenantContext` dependency extracts `org_id` directly from the validated token.
   - Query parameters or path parameters requesting a specific `organization_id` are strictly verified against the caller's JWT `org_id`. Any mismatch raises HTTP `403 Forbidden` (`TENANT_ACCESS_DENIED`).
3. **Repository Layer Guardrails**:
   - Every database query executed through `BaseRepository` automatically injects `organization_id == tenant_context.org_id`.
   - Cross-tenant queries are structurally prohibited at the query builder layer.
4. **AI & Vector Quarantine**:
   - Vector similarity queries executed through `pgvector` or Qdrant must apply the hard metadata filter `organization_id = :tenant_id`.
   - Candidate chunks retrieved during Hybrid RAG are filtered against the caller's `AISecurityContext` before prompt synthesis.

---

## 4. Multi-Tier AI Knowledge Context Scoping

### 4.1 AI Retrieval Routing & Scope Fallback

When a user interacts with the AI Assistant or submits a search query, the system dynamically routes retrieval across organizational tiers based on the user's active workspace context:

$$\text{Active Workspace Context} = (\text{Organization ID}, \text{Department ID}, \text{Team ID}, \text{Project ID})$$

```
                   User Submits AI Prompt
                             │
                             ▼
               Determine User Workspace Scope
                             │
         ┌───────────────────┼───────────────────┐
         │ (In Project)      │ (In Team)         │ (Org-Wide)
         ▼                   ▼                   ▼
   ┌───────────┐       ┌───────────┐       ┌───────────┐
   │ Project   │       │ Team      │       │ Org-Wide  │
   │ Retrieval │       │ Retrieval │       │ Retrieval │
   └─────┬─────┘       └─────┬─────┘       └─────┬─────┘
         │                   │                   │
         └─────────────┬─────┴───────────────────┘
                       │
                       ▼
       Permission & Document-Level Access Gating
                       │
                       ▼
         Dynamic Context Synthesis & LLM Call
```

### 4.2 Retrieval Scoping Matrix

| Scope Level | Retrieval Strategy | Document Filtering Criteria | Use Case |
| :--- | :--- | :--- | :--- |
| **Project-Specific** | Highly focused | `project_id == active_project.id` | "What are the remaining deliverables for Sprint 3?" |
| **Team-Level** | Departmental & Team | `team_id == user_team.id` OR `project_id IN user_team_projects` | "Where is the backend API deployment checklist?" |
| **Department-Level**| Functional group | `department_id == user_dept.id` | "What is Engineering's code review standard?" |
| **Org-Wide** | Enterprise global | `organization_id == user_org.id` AND `is_public_in_org == TRUE` | "What is our company annual leave policy?" |

### 4.3 AI Workspace Settings & Governance

Each organization defines workspace-level AI configurations in `organization_settings`:
- `default_llm`: Default foundation model for the workspace (e.g., `gpt-4o`, `claude-3-5-sonnet`, `llama-3.1-70b`).
- `embedding_model`: Text embedding model (e.g., `text-embedding-3-small`, `all-MiniLM-L6-v2`).
- `citation_preferences`: Citation formatting style (`in-text-brackets`, `footnote`, `structured-card`).
- `monthly_token_quota`: Organization-wide token expenditure ceiling.
- `enable_department_isolation`: Strict mode preventing cross-department RAG fallback without explicit Manager approval.

---

## 5. Organizational RBAC & Permissions Review

### 5.1 Hierarchical Role Definitions for Phase 1.5

| Role | Hierarchy Level | Scope of Authority |
| :--- | :---: | :--- |
| **SuperAdmin** | 5 | Platform-wide system maintenance, multi-tenant diagnostics, system health. |
| **OrgAdmin** | 4 | Complete governance over the enterprise organization: creates departments, configures workspace settings, invites members, manages billing. |
| **ProjectManager** | 3 | Full control over assigned projects, team charters, sprint tasks, and document management within their departments/teams. |
| **Member** (Employee)| 2 | Active contributor: creates documents, creates tasks within assigned projects, executes AI queries, participates in team chats. |
| **Viewer** | 1 | Read-only access: searches approved public documents, views project dashboards, views meeting transcripts. |

### 5.2 Granular Organization Management Permissions Taxonomy

```python
# Organization Governance
ORG_CREATE = "org:create"
ORG_READ = "org:read"
ORG_UPDATE = "org:update"
ORG_DELETE = "org:delete"
ORG_SETTINGS = "org:settings"

# Department Management
DEPT_CREATE = "dept:create"
DEPT_READ = "dept:read"
DEPT_UPDATE = "dept:update"
DEPT_DELETE = "dept:delete"

# Team Management
TEAM_CREATE = "team:create"
TEAM_READ = "team:read"
TEAM_UPDATE = "team:update"
TEAM_DELETE = "team:delete"

# Project Management
PROJECT_CREATE = "project:create"
PROJECT_READ = "project:read"
PROJECT_UPDATE = "project:update"
PROJECT_DELETE = "project:delete"
PROJECT_MEMBERSHIP = "project:membership"

# Member & Invitation Governance
INVITATION_CREATE = "invitation:create"
INVITATION_READ = "invitation:read"
INVITATION_REVOKE = "invitation:revoke"
MEMBER_READ = "member:read"
MEMBER_UPDATE = "member:update"
MEMBER_REMOVE = "member:remove"
```

### 5.3 Role-to-Permission Mapping Matrix

| Permission | OrgAdmin | ProjectManager | Member (Employee) | Viewer |
| :--- | :---: | :---: | :---: | :---: |
| `org:create` | ✗ (SuperAdmin) | ✗ | ✗ | ✗ |
| `org:read` | ✓ | ✓ | ✓ | ✓ |
| `org:update` | ✓ | ✗ | ✗ | ✗ |
| `org:delete` | ✓ | ✗ | ✗ | ✗ |
| `org:settings`| ✓ | ✗ | ✗ | ✗ |
| `dept:create` | ✓ | ✗ | ✗ | ✗ |
| `dept:read` | ✓ | ✓ | ✓ | ✓ |
| `dept:update` | ✓ | ✗ | ✗ | ✗ |
| `team:create` | ✓ | ✓ | ✗ | ✗ |
| `team:read` | ✓ | ✓ | ✓ | ✓ |
| `team:update` | ✓ | ✓ | ✗ | ✗ |
| `project:create`| ✓ | ✓ | ✓ | ✗ |
| `project:read`| ✓ | ✓ | ✓ | ✓ |
| `project:update`| ✓ | ✓ | ✗ | ✗ |
| `project:delete`| ✓ | ✓ | ✗ | ✗ |
| `invitation:create`| ✓ | ✓ | ✗ | ✗ |
| `member:manage`| ✓ | ✗ | ✗ | ✗ |

---

## 6. Audit & Activity Tracking Requirements

Every organization-level operational mutation must emit an immutable structured event to the `activity_logs` table:

1. `ORGANIZATION_CREATED`: Root workspace initialized with admin identity.
2. `ORGANIZATION_UPDATED`: Changes to domain, company size, timezone, or logo.
3. `DEPARTMENT_CREATED` / `DEPARTMENT_UPDATED`: Department structural adjustments.
4. `TEAM_CREATED` / `TEAM_UPDATED`: Team formation and lead assignment.
5. `INVITATION_SENT`: User invited to organization, team, or department.
6. `INVITATION_ACCEPTED`: User completes registration via invite token.
7. `MEMBER_ROLE_CHANGED`: Privilege escalation or reduction.
8. `MEMBER_REMOVED`: Member soft-deleted or removed from tenant workspace.
9. `PROJECT_CREATED` / `PROJECT_ARCHIVED`: Project lifecycle transitions.

---

## 7. Downstream Responsibilities & Handoff Plan

- **Member 2 (Backend Lead)**: Implement FastAPI routers (`backend/app/api/v1/organizations.py`, `backend/app/api/v1/departments.py`, `backend/app/api/v1/teams.py`, `backend/app/api/v1/projects.py`, `backend/app/api/v1/invitations.py`), services, and multi-tenant repository enforcement.
- **Member 3 (Frontend Lead)**: Build organization setup wizard, department/team configuration screens, member invitation modals, project dashboards, and workspace settings forms in `frontend/src/`.
- **Member 4 (DevOps Lead)**: Seed multi-tenant departments and teams in `backend/app/db/seed.py`, author tenant isolation integration tests, and update CI test matrices.
