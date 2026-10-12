# Master Authorization Architecture Specification

> **Phase 1.6 Architectural Blueprint: User Role Management & Authorization Framework**
> **Author**: Member 1 (Project Lead & AI Architect)
> **Target Audience**: Member 2 (Backend Lead), Member 3 (Frontend Lead), Member 4 (DevOps Lead)
> **Specification Reference**: `devdocs/p1/p1.6.txt` (Chapters 1-19)
> **Status**: APPROVED & LOCKED FOR PHASE 1.6 IMPLEMENTATION

---

## 1. Executive Summary & Architectural Goals

Authentication (Phase 1.4) established *who you are*. Authorization (Phase 1.6) establishes *what you are allowed to do*.

Every API endpoint, every document, every project workspace, and every AI inference call in KEEP must be gated through a centralized, deterministic, multi-layered authorization framework. This specification defines that framework as an implementable blueprint, describing the policy engine, permission inheritance model, resource-level ownership rules, middleware pipeline, AI retrieval authorization filters, and audit trail contracts.

### Core Objectives for Phase 1.6:
1. **Centralized Policy Engine**: A single, testable `BaseAuthorizationPolicyEngine` evaluates all access decisions based on role, resource ownership, project membership, and organizational scope.
2. **Resource-Level Authorization**: Access decisions combine the caller's role with the specific resource being accessed (not just blanket role checks).
3. **Ownership Rules**: Certain resources grant additional permissions to their owners regardless of base role (e.g., a Document uploader can delete their own upload).
4. **AI Retrieval Authorization**: The RAG pipeline inherits all authorization filters before retrieving or injecting knowledge into LLM context.
5. **Audit Trail**: Every authorization decision — granted or denied — emits a structured event to the `activity_logs` table.
6. **Future-Ready**: Design supports seamless extension to Attribute-Based Access Control (ABAC) in later phases.

---

## 2. Authorization Pipeline Architecture

Every incoming request passes through a sequential middleware chain before reaching business logic:

```
Incoming HTTP Request
         |
         v
1. JWT Validation Layer
   (Verify signature, expiry, extract org_id claim)
         |
         v
2. User & Tenant Resolution
   (Load User record, resolve OrganizationID, verify ACTIVE)
         |
         v
3. Role & Permission Loading
   (user.role -> ROLE_PERMISSIONS -> AISecurityContext.permissions)
         |
         v
4. Organization Isolation Check
   (target resource.org_id == caller.org_id?)
   NO -> IMMEDIATE 403 (AUTH_ORGANIZATION_MISMATCH)
         |
         v
5. Permission Engine Evaluation
   (BaseAuthorizationPolicyEngine.evaluate_access)
   (required_permission in caller.permissions?)
         |
         v
6. Resource-Level Ownership Check
   (BaseResourceOwnershipChecker.is_owner)
   (Owner may override role restrictions for own resources)
         |
         v
7. Policy Decision -> AuthorizationDecision { allowed, reason, error_code }
         |
   [ALLOWED]         [DENIED -> 403]
   Execute Logic     Return AuthorizationError
         |                 |
         v                 v
8. Emit Audit Log    8. Emit Audit Log
   PERMISSION_GRANTED    PERMISSION_DENIED
```

Authorization occurs **after authentication** but **before** business logic execution.

---

## 3. Permission Model (Phase 1.6)

### 3.1 Action-Based Permission Keys

Permissions are granular, action-oriented strings (not role names). This allows fine-grained enforcement at every endpoint and supports future custom role configuration.

| Domain       | Permissions                                                                    |
| :----------- | :----------------------------------------------------------------------------- |
| **Document** | `document.create`, `document.read`, `document.update`, `document.delete`       |
| **Project**  | `project.create`, `project.read`, `project.manage`, `project.membership`       |
| **Meeting**  | `meeting.create`, `meeting.read`, `meeting.manage`                             |
| **AI**       | `ai.chat`, `ai.search`, `ai.admin`, `ai.config`                                |
| **Org**      | `organization.create`, `organization.manage`, `organization.settings`          |
| **Users**    | `user.invite`, `user.manage`, `user.view`                                      |
| **Analytics**| `analytics.view`, `analytics.export`                                           |
| **Audit**    | `audit.read`                                                                   |

### 3.2 Role to Permission Matrix (Phase 1.6 Canonical)

| Permission              | OrgAdmin | ProjectManager | Employee | Viewer |
| :---------------------- | :------: | :------------: | :------: | :----: |
| `organization.create`   | No (SA)  | No             | No       | No     |
| `organization.manage`   | Yes      | No             | No       | No     |
| `organization.settings` | Yes      | No             | No       | No     |
| `user.invite`           | Yes      | Yes            | No       | No     |
| `user.manage`           | Yes      | No             | No       | No     |
| `user.view`             | Yes      | Yes            | Yes      | Yes    |
| `project.create`        | Yes      | Yes            | Yes      | No     |
| `project.manage`        | Yes      | Yes (scoped)   | No       | No     |
| `project.membership`    | Yes      | Yes (scoped)   | No       | No     |
| `document.create`       | Yes      | Yes            | Yes      | No     |
| `document.read`         | Yes      | Yes            | Yes      | Yes    |
| `document.update`       | Yes      | Yes            | Yes (own)| No     |
| `document.delete`       | Yes      | Yes (scoped)   | No       | No     |
| `meeting.create`        | Yes      | Yes            | No       | No     |
| `meeting.read`          | Yes      | Yes            | Yes      | Yes    |
| `ai.chat`               | Yes      | Yes            | Yes      | Yes    |
| `ai.search`             | Yes      | Yes            | Yes      | Yes    |
| `ai.admin`              | Yes      | No             | No       | No     |
| `ai.config`             | Yes      | No             | No       | No     |
| `analytics.view`        | Yes      | Yes            | Yes      | Yes    |
| `audit.read`            | Yes      | No             | No       | No     |

Notes:
- `organization.create` is reserved exclusively for `SuperAdmin`.
- ProjectManager `project.manage` and `project.membership` are scoped to projects they own.
- Employee `document.update` is scoped to documents they uploaded — enforced via ownership check.

---

## 4. Resource-Level Authorization Model

### 4.1 ResourceAuthorizationContext

Every resource access decision is evaluated using a `ResourceAuthorizationContext`, which captures the caller's identity alongside the target resource's ownership and organizational metadata:

```python
@dataclass
class ResourceAuthorizationContext:
    # Caller identity
    caller_id: UUID
    caller_role: str
    caller_org_id: UUID
    caller_project_ids: set[UUID]
    caller_team_ids: set[UUID]
    caller_dept_id: UUID | None

    # Target resource metadata
    resource_id: UUID
    resource_type: ResourceType    # DOCUMENT, PROJECT, MEETING, CHAT_SESSION, TEAM, etc.
    resource_org_id: UUID
    resource_owner_id: UUID | None
    resource_project_id: UUID | None
    required_permission: str       # e.g. "document.delete"
```

### 4.2 Decision Flow

```
ResourceAuthorizationContext
        |
        v
Step 1: Tenant Boundary
  caller_org_id == resource_org_id?
  NO -> DENY (AUTH_ORGANIZATION_MISMATCH)
        |
        v
Step 2: Permission Check
  required_permission in caller.permissions?
  NO -> goto Step 3
  YES -> goto Step 4
        |
        v
Step 3: Ownership Override
  caller_id == resource_owner_id?
  YES -> ALLOW (owner bypass for permitted operations)
  NO  -> DENY (AUTH_PERMISSION_DENIED)
        |
        v
Step 4: Project Membership (if resource is project-scoped)
  resource_project_id in caller_project_ids?
  NO  -> DENY (AUTH_RESOURCE_FORBIDDEN)
  YES -> ALLOW
```

### 4.3 Ownership Override Table

| Resource Type  | Owner              | Ownership Bypass Grants                          |
| :------------- | :----------------- | :----------------------------------------------- |
| `DOCUMENT`     | Uploader           | `document.update`, `document.delete` on own docs |
| `MEETING`      | Organizer          | `meeting.manage` on own meetings                 |
| `CHAT_SESSION` | Session creator    | Full read/delete of own chat sessions            |
| `PROJECT`      | Organization (n/a) | Always requires membership — no bypass           |
| `TEAM`         | Organization (n/a) | Always requires explicit role — no bypass        |

---

## 5. Authorization Error Codes

All authorization failures return a standardized JSON envelope:

```json
{
  "success": false,
  "error": {
    "code": "AUTH_PERMISSION_DENIED",
    "message": "You do not have permission to perform this action.",
    "details": {
      "required_permission": "document.delete",
      "user_role": "Member"
    }
  }
}
```

| Error Code                   | HTTP | Trigger                                              |
| :--------------------------- | :--: | :--------------------------------------------------- |
| `AUTH_PERMISSION_DENIED`     | 403  | User lacks the required permission for the action    |
| `AUTH_ROLE_REQUIRED`         | 403  | Endpoint requires a minimum role not held by caller  |
| `AUTH_RESOURCE_FORBIDDEN`    | 403  | Resource exists but user is not a project member     |
| `AUTH_ORGANIZATION_MISMATCH` | 403  | Cross-tenant access attempt detected                 |
| `AUTH_POLICY_FAILED`         | 403  | Policy engine evaluation returned a DENY verdict     |

---

## 6. AI Retrieval Authorization

### 6.1 Principle

AI modules — RAG search, knowledge graph traversal, conversational context injection — **must inherit the same authorization filters** as the REST API. A user who cannot `document.read` a file via the API cannot have that file's contents injected into their AI prompt context.

### 6.2 Authorization Filter Chain for RAG

```
User submits AI chat prompt
        |
        v
1. Build RAGSecurityContext from AISecurityContext
   (org_id, role, allowed_document_ids, accessible_project_ids)
        |
        v
2. BaseAIAuthorizationFilter.filter_knowledge_candidates()
   Prune retrieval candidates by:
   - organization_id match (hard boundary)
   - document.read permission in caller permissions
   - project membership (project_id in caller_project_ids)
   - department isolation flag (enable_department_isolation)
        |
        v
3. BaseAIAuthorizationFilter.authorize_kg_traversal()
   KG entity traversal returns only nodes where:
   - source_document is accessible to caller
   - entity.organization_id == caller.org_id
        |
        v
4. Authorized chunks only enter prompt assembly (BaseContextBuilder)
        |
        v
5. LLM generation with filtered, authorized context only
```

### 6.3 AI Authorization Permission Requirements

| AI Operation              | Required Permission | Scope Restriction                                     |
| :------------------------ | :------------------ | :---------------------------------------------------- |
| RAG Chat Query            | `ai.chat`           | Documents accessible within caller's active project   |
| Semantic Search           | `ai.search`         | Documents within caller's workspace scope             |
| KG Entity Traversal       | `ai.search`         | Entities linked to caller-accessible documents only   |
| AI Model Configuration    | `ai.config`         | OrgAdmin only                                         |
| AI Admin (audit/quotas)   | `ai.admin`          | OrgAdmin only                                         |

---

## 7. Authorization Audit Logging

Every authorization decision (ALLOW or DENY) must emit an immutable record to `activity_logs`:

| Field             | Value                                               |
| :---------------- | :-------------------------------------------------- |
| `event_type`      | `PERMISSION_GRANTED` or `PERMISSION_DENIED`         |
| `user_id`         | Authenticated caller UUID                           |
| `organization_id` | Tenant boundary UUID                                |
| `resource_type`   | `DOCUMENT`, `PROJECT`, `MEETING`, `AI_QUERY`, etc.  |
| `resource_id`     | Target resource UUID                                |
| `action`          | Permission string (e.g. `document.delete`)          |
| `decision`        | `ALLOW` or `DENY`                                   |
| `error_code`      | `null` on ALLOW, `AUTH_*` error code on DENY        |
| `ip_address`      | Caller IP from request context                      |
| `created_at`      | UTC timestamp                                       |

These audit logs support compliance reporting, security incident investigation, and SOC 2 readiness.

---

## 8. Policy Engine Design

### 8.1 Abstract Contracts (Member 1 Domain)

`BaseAuthorizationPolicyEngine` — the central evaluation contract:

```python
class BaseAuthorizationPolicyEngine(ABC):
    @abstractmethod
    def evaluate_access(
        self,
        context: ResourceAuthorizationContext,
    ) -> AuthorizationDecision:
        """Evaluates all authorization rules. Returns ALLOW or DENY with reason."""

    @abstractmethod
    def evaluate_bulk_access(
        self,
        contexts: list[ResourceAuthorizationContext],
    ) -> list[AuthorizationDecision]:
        """Bulk evaluation for filtering lists of resources (e.g. search results)."""
```

`BaseResourceOwnershipChecker` — ownership bypass evaluation:

```python
class BaseResourceOwnershipChecker(ABC):
    @abstractmethod
    def is_owner(
        self,
        caller_id: UUID,
        resource_type: ResourceType,
        resource_id: UUID,
        organization_id: UUID,
    ) -> bool:
        """Returns True if caller is the designated owner of the resource."""
```

`BaseAIAuthorizationFilter` — AI retrieval authorization (RAG domain):

```python
class BaseAIAuthorizationFilter(ABC):
    @abstractmethod
    def filter_knowledge_candidates(
        self,
        candidates: list[RetrievalResult],
        security_context: RAGSecurityContext,
    ) -> list[RetrievalResult]:
        """Prunes RAG candidates to only those authorized for the caller."""

    @abstractmethod
    def authorize_kg_traversal(
        self,
        entities: list[KGEntityRecord],
        security_context: RAGSecurityContext,
    ) -> list[KGEntityRecord]:
        """Filters KG entities to only those from caller-accessible documents."""
```

### 8.2 Implementation Strategy (for Member 2)

The concrete `AuthorizationPolicyEngine` in `backend/app/core/authorization.py` must:
1. Perform **tenant validation** first — fast short-circuit on mismatch.
2. Expand role to permission set using `ROLE_PERMISSIONS` from `backend/app/services/ai/interfaces.py`.
3. Check `required_permission in permissions` — grant if present.
4. If denied by role, invoke `BaseResourceOwnershipChecker.is_owner()` — grant if owner and operation is ownership-eligible.
5. If resource is project-scoped, verify `resource_project_id in caller_project_ids`.
6. Return `AuthorizationDecision` with structured `error_code` and `reason`.
7. Always emit `activity_logs` audit entry regardless of decision.

### 8.3 Future ABAC Extension Point

```python
@abstractmethod
def evaluate_policy_rules(
    self,
    context: ResourceAuthorizationContext,
    custom_rules: list[PolicyRule],
) -> AuthorizationDecision:
    """Phase 3+ extension: evaluate organization-defined ABAC policy rules."""
```

---

## 9. Downstream Responsibilities & Handoff Plan

- **Member 2 (Backend Lead)**:
  - Implement `AuthorizationPolicyEngine` (concrete) in `backend/app/core/authorization.py`.
  - Implement `require_permission(permission: str)` FastAPI dependency in `backend/app/api/dependencies/authorization.py`.
  - Wire authorization middleware into all Phase 1.5 org/dept/team/project/member endpoints.
  - Implement resource-level ownership checks in `DocumentService`, `MeetingService`, and `ProjectService`.
  - Implement concrete `AIAuthorizationFilter` in `backend/app/services/ai/authorization.py`.

- **Member 3 (Frontend Lead)**:
  - Implement role-aware conditional UI rendering (hide/disable buttons based on `user.role`).
  - Build `AccessDeniedPage` for 403 responses.
  - Build `PermissionGuard` component wrapping action triggers.
  - Update `ProtectedRoute` to support `requiredPermission` prop for permission-level guards.

- **Member 4 (DevOps Lead)**:
  - Author authorization unit tests covering policy engine, ownership bypass, and cross-tenant rejection.
  - Author integration tests for all protected endpoints verifying 403 on insufficient permissions.
  - Author privilege escalation, horizontal access, and vertical access security tests.
  - Verify audit log emission on authorization events.
