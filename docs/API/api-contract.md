# API Contracts Specification (docs/api/api-contract.md)

> **Official REST & Streaming API Contract for KEEP Enterprise Platform**  
> *Approved by: Member 1 (Project Lead & AI Architect)*  
> *Implementer: Member 2 (Backend Lead) | Consumer: Member 3 (Frontend Lead)*  
> *Derived from: devdocs/p1/p1.2.txt (Chapters 5, 6, 14, 15, 18)*

---

## 1. Global API Standards & Protocols

1. **Base URL**: All endpoints are prefixed with `/api/v1`.
2. **Standard Content Type**: `application/json; charset=utf-8` (or `multipart/form-data` for file uploads, `text/event-stream` for AI streaming).
3. **Authentication**: Authorization header: `Bearer <jwt_access_token>`.
4. **Tenant Isolation**: Tenant context is extracted server-side from JWT claims (`org_id`). Multi-tenant path parameters (where present) must match the JWT tenant boundary.
5. **Standardized Response Envelope**: All endpoints adhere strictly to the uniform JSON envelope defined below.

---

## 2. Standardized JSON Envelope Schemas

### 2.1 Standard Success Envelope (`ApiResponse[T]`)
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {}
}
```

### 2.2 Standard Error Envelope (`ApiErrorResponse`)
```json
{
  "success": false,
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "Invalid email or password.",
    "details": {}
  }
}
```

### 2.3 Standard Pagination Envelope (`PaginatedData[T]`)
```json
{
  "items": [],
  "total": 120,
  "page": 1,
  "page_size": 20,
  "total_pages": 6
}
```

---

## 3. Core REST API Endpoints

### 3.1 Authentication & Identity Management (`/api/v1/auth`)

#### 3.1.1 User Registration
- **Method**: `POST`
- **Path**: `/api/v1/auth/register`
- **Auth**: Public
- **Request Body**:
```json
{
  "email": "jane.doe@enterprise.com",
  "password": "SecurePassword123!",
  "full_name": "Jane Doe",
  "organization_id": "8bc92d11-3456-4211-89ab-1234567890ab",
  "role": "Member"
}
```
- **Response (201 Created)**:
```json
{
  "success": true,
  "message": "User registered successfully.",
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "jane.doe@enterprise.com",
    "full_name": "Jane Doe",
    "role": "Member",
    "organization_id": "8bc92d11-3456-4211-89ab-1234567890ab",
    "is_active": true,
    "created_at": "2026-10-09T00:30:00Z"
  }
}
```
- **Error Codes**: `AUTH_EMAIL_EXISTS` (409), `VALIDATION_ERROR` (422)

#### 3.1.2 User Login
- **Method**: `POST`
- **Path**: `/api/v1/auth/login`
- **Auth**: Public
- **Request Body**:
```json
{
  "email": "user@enterprise.com",
  "password": "SecurePassword123!"
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "dGhpcyBpcy...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "email": "user@enterprise.com",
      "full_name": "Jane Doe",
      "role": "OrgAdmin",
      "organization_id": "8bc92d11-3456-4211-89ab-1234567890ab",
      "is_active": true
    }
  }
}
```
- **Error Codes**: `AUTH_INVALID_CREDENTIALS` (401), `AUTH_ACCOUNT_DISABLED` (403), `AUTH_UNVERIFIED_EMAIL` (403), `VALIDATION_ERROR` (422)

#### 3.1.3 User Logout
- **Method**: `POST`
- **Path**: `/api/v1/auth/logout`
- **Auth**: Bearer JWT (Optional body with refresh token to revoke)
- **Request Body** (Optional):
```json
{
  "refresh_token": "dGhpcyBpcy..."
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Logged out successfully.",
  "data": {
    "logged_out": true
  }
}
```
- **Error Codes**: `AUTH_TOKEN_INVALID` (401)

#### 3.1.4 Refresh Token
- **Method**: `POST`
- **Path**: `/api/v1/auth/refresh`
- **Auth**: Public (Requires refresh token in body)
- **Request Body**:
```json
{
  "refresh_token": "dGhpcyBpcy..."
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Token refreshed successfully.",
  "data": {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eXy01Zz...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```
- **Error Codes**: `AUTH_TOKEN_EXPIRED` (401), `AUTH_TOKEN_INVALID` (401)

#### 3.1.5 Request Password Reset (Forgot Password)
- **Method**: `POST`
- **Path**: `/api/v1/auth/forgot-password`
- **Auth**: Public
- **Request Body**:
```json
{
  "email": "user@enterprise.com"
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Password reset instructions sent if email exists.",
  "data": {
    "email_sent": true
  }
}
```
- **Error Codes**: `VALIDATION_ERROR` (422)

#### 3.1.6 Reset Password (With Token)
- **Method**: `POST`
- **Path**: `/api/v1/auth/reset-password`
- **Auth**: Public
- **Request Body**:
```json
{
  "token": "reset_token_6a1f8...",
  "new_password": "NewSecurePassword456!"
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Password has been successfully reset.",
  "data": {
    "reset_completed": true
  }
}
```
- **Error Codes**: `AUTH_INVALID_RESET_TOKEN` (400), `VALIDATION_ERROR` (422)

#### 3.1.7 Get Current User Profile
- **Method**: `GET`
- **Path**: `/api/v1/auth/me`
- **Auth**: Bearer JWT
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "User profile retrieved.",
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "user@enterprise.com",
    "full_name": "Jane Doe",
    "role": "OrgAdmin",
    "organization_id": "8bc92d11-3456-4211-89ab-1234567890ab",
    "is_active": true,
    "created_at": "2026-08-17T12:00:00Z"
  }
}
```
- **Error Codes**: `AUTH_TOKEN_INVALID` (401), `AUTH_ACCOUNT_DISABLED` (403)

#### 3.1.8 Change Password
- **Method**: `PATCH`
- **Path**: `/api/v1/auth/change-password`
- **Auth**: Bearer JWT
- **Request Body**:
```json
{
  "current_password": "SecurePassword123!",
  "new_password": "UpdatedSecurePassword789!"
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Password changed successfully.",
  "data": {
    "password_changed": true
  }
}
```
- **Error Codes**: `AUTH_INVALID_CREDENTIALS` (401), `VALIDATION_ERROR` (422)

---

### 3.2 Organization, Workspace & Hierarchy Management (Phase 1.5)

#### 3.2.1 Create Organization
- **Method**: `POST`
- **Path**: `/api/v1/organizations`
- **Auth**: SuperAdmin or Initial Onboarding
- **Request Body**:
```json
{
  "name": "Acme Global Enterprise",
  "domain": "acme.com",
  "industry": "Software & Technology",
  "company_size": "250-1000",
  "time_zone": "America/New_York",
  "default_language": "en-US",
  "logo_url": "https://assets.acme.com/logo.png",
  "description": "Enterprise cloud platform and AI intelligence."
}
```
- **Response (201 Created)**:
```json
{
  "success": true,
  "message": "Organization created successfully.",
  "data": {
    "id": "8bc92d11-3456-4211-89ab-1234567890ab",
    "name": "Acme Global Enterprise",
    "domain": "acme.com",
    "industry": "Software & Technology",
    "company_size": "250-1000",
    "time_zone": "America/New_York",
    "default_language": "en-US",
    "is_active": true,
    "created_at": "2026-10-10T10:00:00Z"
  }
}
```
- **Error Codes**: `ORG_NAME_EXISTS` (409), `ORG_DOMAIN_EXISTS` (409), `VALIDATION_ERROR` (422)

#### 3.2.2 Get Current Organization Details
- **Method**: `GET`
- **Path**: `/api/v1/organizations/current`
- **Auth**: Bearer JWT
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Organization details retrieved.",
  "data": {
    "id": "8bc92d11-3456-4211-89ab-1234567890ab",
    "name": "Acme Global Enterprise",
    "domain": "acme.com",
    "industry": "Software & Technology",
    "company_size": "250-1000",
    "time_zone": "America/New_York",
    "default_language": "en-US",
    "is_active": true,
    "created_at": "2026-08-17T10:00:00Z"
  }
}
```

#### 3.2.3 Get Organization by ID
- **Method**: `GET`
- **Path**: `/api/v1/organizations/{id}`
- **Auth**: Bearer JWT (`OrgAdmin` or matching `organization_id`)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Organization retrieved.",
  "data": {
    "id": "8bc92d11-3456-4211-89ab-1234567890ab",
    "name": "Acme Global Enterprise",
    "domain": "acme.com",
    "is_active": true
  }
}
```
- **Error Codes**: `ORG_NOT_FOUND` (404), `TENANT_ACCESS_DENIED` (403)

#### 3.2.4 Update Organization Settings
- **Method**: `PATCH`
- **Path**: `/api/v1/organizations/{id}`
- **Auth**: Bearer JWT (`OrgAdmin`)
- **Request Body**:
```json
{
  "name": "Acme International Enterprises",
  "time_zone": "UTC",
  "theme": "dark",
  "default_language": "en-US",
  "settings": {
    "max_upload_size_mb": 50,
    "default_llm": "gpt-4o",
    "embedding_model": "text-embedding-3-small",
    "citation_preferences": "in-text-brackets"
  }
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Organization updated successfully.",
  "data": {
    "id": "8bc92d11-3456-4211-89ab-1234567890ab",
    "name": "Acme International Enterprises",
    "updated_at": "2026-10-10T12:00:00Z"
  }
}
```
- **Error Codes**: `ORG_NOT_FOUND` (404), `AUTH_FORBIDDEN` (403)

#### 3.2.5 Archive / Delete Organization
- **Method**: `DELETE`
- **Path**: `/api/v1/organizations/{id}`
- **Auth**: Bearer JWT (`SuperAdmin` or Root `OrgAdmin`)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Organization archived successfully.",
  "data": {
    "id": "8bc92d11-3456-4211-89ab-1234567890ab",
    "is_deleted": true
  }
}
```

#### 3.2.6 Department Management (`/api/v1/departments`)
- **Create Department**: `POST /api/v1/departments` (Body: `{"name": "Engineering", "description": "Core product engineering", "manager_id": "<uuid>"}`)
- **List Departments**: `GET /api/v1/departments` (Returns array of department cards with member and team counts)
- **Get Department**: `GET /api/v1/departments/{id}`
- **Update Department**: `PATCH /api/v1/departments/{id}`
- **Delete Department**: `DELETE /api/v1/departments/{id}`

#### 3.2.7 Team Management (`/api/v1/teams`)
- **Create Team**: `POST /api/v1/teams` (Body: `{"name": "AI & RAG Team", "department_id": "<uuid>", "lead_user_id": "<uuid>", "description": "Machine learning engineering"}`)
- **List Teams**: `GET /api/v1/teams?department_id=<uuid>`
- **Get Team**: `GET /api/v1/teams/{id}`
- **Update Team**: `PATCH /api/v1/teams/{id}`
- **Delete Team**: `DELETE /api/v1/teams/{id}`

#### 3.2.8 Project Workspace Management (`/api/v1/projects`)
- **Create Project**: `POST /api/v1/projects` (Body: `{"name": "Project Helios", "team_id": "<uuid>", "description": "Enterprise AI search rollout", "priority": "HIGH"}`)
- **List Projects**: `GET /api/v1/projects?team_id=<uuid>&status=ACTIVE`
- **Get Project**: `GET /api/v1/projects/{id}`
- **Update Project**: `PATCH /api/v1/projects/{id}`
- **Archive Project**: `DELETE /api/v1/projects/{id}`

#### 3.2.9 User Invitation System (`/api/v1/invitations`)
- **Send Invitation**: `POST /api/v1/invitations`
  - Body: `{"email": "engineer@acme.com", "role": "Member", "department_id": "<uuid>", "team_id": "<uuid>"}`
- **List Pending Invitations**: `GET /api/v1/invitations`
- **Revoke Invitation**: `DELETE /api/v1/invitations/{id}`
- **Accept Invitation**: `POST /api/v1/invitations/accept`
  - Body: `{"token": "inv_token_99...", "full_name": "Alex Mercer", "password": "SecurePassword123!"}`

#### 3.2.10 Member Management (`/api/v1/members`)
- **List Members**: `GET /api/v1/members?department_id=<uuid>&role=Member&page=1&page_size=20`
- **Update Member**: `PATCH /api/v1/members/{user_id}` (Body: `{"role": "ProjectManager", "department_id": "<uuid>", "is_active": true}`)
- **Remove Member**: `DELETE /api/v1/members/{user_id}`

---

### 3.3 Document Management (`/api/v1/documents`)

#### 3.3.1 Upload Document for Ingestion
- **Method**: `POST`
- **Path**: `/api/v1/documents/upload`
- **Auth**: Bearer JWT (`OrgAdmin`, `Manager`, `Member`)
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: Binary file (PDF, DOCX, TXT, PNG, JPG)
  - `title`: string (optional)
  - `tags`: string (comma-separated, optional)
- **Response (202 Accepted)**:
```json
{
  "success": true,
  "message": "Document accepted for asynchronous processing.",
  "data": {
    "document_id": "99a85f64-5717-4562-b3fc-2c963f66af11",
    "filename": "Q3_Strategic_Plan.pdf",
    "status": "PROCESSING",
    "file_size": 2458120,
    "created_at": "2026-09-30T10:00:00Z"
  }
}
```
- **Error Codes**: `UNSUPPORTED_FILE_TYPE` (400), `FILE_SIZE_EXCEEDED` (400), `AUTH_FORBIDDEN` (403)

#### 3.3.2 List Documents (Paginated)
- **Method**: `GET`
- **Path**: `/api/v1/documents?page=1&page_size=20&status=PROCESSED`
- **Auth**: Bearer JWT
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Documents retrieved.",
  "data": {
    "items": [
      {
        "id": "99a85f64-5717-4562-b3fc-2c963f66af11",
        "filename": "Q3_Strategic_Plan.pdf",
        "file_type": "application/pdf",
        "file_size": 2458120,
        "status": "PROCESSED",
        "chunk_count": 42,
        "created_at": "2026-09-30T10:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

#### 3.3.3 Delete Document (Soft Delete with Authorization Gating)
- **Method**: `DELETE`
- **Path**: `/api/v1/documents/{id}`
- **Auth**: Bearer JWT (`document.delete` permission or ownership override for document author/uploader)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Document deleted successfully.",
  "data": {
    "id": "99a85f64-5717-4562-b3fc-2c963f66af11"
  }
}
```
- **Error Codes**: `NOT_FOUND` (404), `AUTH_PERMISSION_DENIED` (403), `AUTH_ORGANIZATION_MISMATCH` (403)

---

### 3.4 AI Search & RAG Chat Engine (`/api/v1/search` & `/api/v1/chat`)

#### 3.4.1 Hybrid Search
- **Method**: `POST`
- **Path**: `/api/v1/search/hybrid`
- **Auth**: Bearer JWT
- **Request Body**:
```json
{
  "query": "enterprise remote work guidelines and stipend",
  "top_k": 10,
  "filters": {
    "document_types": ["pdf", "docx"]
  }
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Search executed successfully.",
  "data": {
    "query": "enterprise remote work guidelines and stipend",
    "total_results": 2,
    "results": [
      {
        "chunk_id": "77a85f64-5717-4562-b3fc-2c963f66af77",
        "document_id": "99a85f64-5717-4562-b3fc-2c963f66af11",
        "filename": "Employee_Handbook_2026.pdf",
        "page_number": 14,
        "content": "Eligible employees may expense up to $500 annually for remote work home office equipment...",
        "relevance_score": 0.94
      }
    ]
  }
}
```

#### 3.4.2 RAG Chat Query (Synchronous Q&A)
- **Method**: `POST`
- **Path**: `/api/v1/chat/query`
- **Auth**: Bearer JWT
- **Request Body**:
```json
{
  "query": "What is the annual home office stipend?",
  "conversation_id": "55a85f64-5717-4562-b3fc-2c963f66af55",
  "top_k": 5,
  "include_citations": true
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Answer generated successfully.",
  "data": {
    "query": "What is the annual home office stipend?",
    "answer": "According to the 2026 Employee Handbook, eligible employees receive an annual home office equipment stipend of up to $500 [Doc 1, Page 14].",
    "conversation_id": "55a85f64-5717-4562-b3fc-2c963f66af55",
    "confidence_score": 0.96,
    "model_name": "gpt-4o",
    "tokens_used": 145,
    "citations": [
      {
        "document_id": "99a85f64-5717-4562-b3fc-2c963f66af11",
        "filename": "Employee_Handbook_2026.pdf",
        "page_number": 14,
        "chunk_index": 3,
        "snippet": "Eligible employees may expense up to $500 annually for remote work home office equipment...",
        "relevance_score": 0.94
      }
    ]
  }
}
```

#### 3.4.3 RAG Chat Stream (Server-Sent Events)
- **Method**: `POST`
- **Path**: `/api/v1/chat/stream`
- **Auth**: Bearer JWT
- **Accept**: `text/event-stream`
- **Request Body**:
```json
{
  "query": "Summarize our quarterly security review policies.",
  "conversation_id": "55a85f64-5717-4562-b3fc-2c963f66af55"
}
```
- **SSE Event Stream Protocol**:
```
event: citation
data: {"document_id": "99a85f64-5717-4562-b3fc-2c963f66af11", "filename": "Security_Policy.pdf", "page_number": 4}

event: token
data: {"token": "Quarterly "}

event: token
data: {"token": "security "}

event: token
data: {"token": "reviews "}

event: done
data: {"finish_reason": "stop", "total_tokens": 85}
```

---

### 3.5 Authorization Error Responses & Policy Enforcement (Phase 1.6)

Authorization evaluation occurs after JWT validation and tenant extraction. When access is denied by policy evaluation, endpoints return a standardized `ApiErrorResponse` envelope with HTTP 403 Forbidden.

#### 3.5.1 Standard Authorization Error Envelope
```json
{
  "success": false,
  "error": {
    "code": "AUTH_PERMISSION_DENIED",
    "message": "You do not have permission to perform this action.",
    "details": {
      "required_permission": "document.delete",
      "user_role": "Member",
      "resource_type": "document"
    }
  }
}
```

#### 3.5.2 Authorization Error Code Registry
| Error Code | HTTP Status | Description | Trigger |
| :--- | :---: | :--- | :--- |
| `AUTH_PERMISSION_DENIED` | 403 | Caller lacks required action permission | Missing permission in caller role and no ownership override |
| `AUTH_ROLE_REQUIRED` | 403 | Minimum organizational role not held | Endpoint guarded by specific minimum role tier |
| `AUTH_RESOURCE_FORBIDDEN` | 403 | Target resource inaccessible | Non-member attempting access to project-scoped resource |
| `AUTH_ORGANIZATION_MISMATCH` | 403 | Cross-tenant access attempted | Caller `organization_id` does not match resource `organization_id` |
| `AUTH_POLICY_FAILED` | 403 | Central policy engine evaluation failed | Composite policy evaluation yielded DENY verdict |

---

### 3.6 Security Audit Logs (`/api/v1/audit`)

#### 3.6.1 List Audit Logs (Paginated)
- **Method**: `GET`
- **Path**: `/api/v1/audit/logs?page=1&page_size=20&user_id=<uuid>&action=<action>&resource_type=<type>`
- **Auth**: Bearer JWT (`audit.read` permission — SuperAdmin, OrgAdmin)
- **Query Parameters**:
  - `page`: integer (default: 1)
  - `page_size`: integer (default: 20, max: 100)
  - `user_id`: UUID (optional filter)
  - `action`: string (optional filter, e.g. `PERMISSION_DENIED`, `DOCUMENT_DELETED`)
  - `resource_type`: string (optional filter, e.g. `document`, `project`)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Audit logs retrieved.",
  "data": {
    "items": [
      {
        "id": "11a85f64-5717-4562-b3fc-2c963f66af11",
        "organization_id": "8bc92d11-3456-4211-89ab-1234567890ab",
        "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "action": "DOCUMENT_DELETED",
        "resource_type": "document",
        "resource_id": "99a85f64-5717-4562-b3fc-2c963f66af11",
        "metadata_json": {
          "required_permission": "document.delete",
          "is_owner": true
        },
        "ip_address": "127.0.0.1",
        "user_agent": "Mozilla/5.0",
        "created_at": "2026-10-12T10:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```
- **Error Codes**: `AUTH_PERMISSION_DENIED` (403), `VALIDATION_ERROR` (422)

---

## 4. API Endpoints Registry, Ownership & Authorization Controls

| Path | Method | Purpose | Required Permission | Owner | Phase |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/api/v1/auth/login` | POST | Authenticate user & issue tokens | Public (None) | Member 2 | Phase 1.4 |
| `/api/v1/auth/refresh` | POST | Refresh expired access token | Authenticated | Member 2 | Phase 1.4 |
| `/api/v1/auth/me` | GET | Retrieve authenticated profile | Authenticated | Member 2 | Phase 1.4 |
| `/api/v1/users` | GET / POST | Manage enterprise users | `user.view` / `user.manage` | Member 2 | Phase 1.4 |
| `/api/v1/organizations` | POST | Create enterprise organization | `org:create` (SuperAdmin) | Member 2 | Phase 1.5 |
| `/api/v1/organizations/current` | GET | Retrieve tenant details | `organization.manage` | Member 2 | Phase 1.5 |
| `/api/v1/organizations/{id}` | GET / PATCH / DELETE | Manage enterprise tenant | `organization.manage` | Member 2 | Phase 1.5 |
| `/api/v1/departments` | GET / POST | Manage departments | `dept:read` / `dept:create` | Member 2 | Phase 1.5 |
| `/api/v1/departments/{id}` | GET / PATCH / DELETE | Department details & operations | `dept:read` / `dept:update` / `dept:delete` | Member 2 | Phase 1.5 |
| `/api/v1/teams` | GET / POST | Manage department teams | `team:read` / `team:create` | Member 2 | Phase 1.5 |
| `/api/v1/teams/{id}` | GET / PATCH / DELETE | Team details & operations | `team:read` / `team:update` / `team:delete` | Member 2 | Phase 1.5 |
| `/api/v1/projects` | GET / POST | Manage collaborative projects | `project.create` | Member 2 | Phase 1.5 |
| `/api/v1/projects/{id}` | GET / PATCH / DELETE | Project details & operations | `project.manage` | Member 2 | Phase 1.5 |
| `/api/v1/invitations` | GET / POST | Manage user invitations | `user.invite` | Member 2 | Phase 1.5 |
| `/api/v1/invitations/accept` | POST | Accept invitation & activate user | Public (Token-backed) | Member 2 | Phase 1.5 |
| `/api/v1/members` | GET | List enterprise members | `user.view` | Member 2 | Phase 1.5 |
| `/api/v1/members/{user_id}` | PATCH / DELETE | Member role & status updates | `user.manage` | Member 2 | Phase 1.5 |
| `/api/v1/documents/upload` | POST | Multipart file ingestion | `document.create` | Member 2 & Member 1 | Phase 1.8 |
| `/api/v1/documents` | GET | List tenant documents | `document.read` | Member 2 | Phase 1.8 |
| `/api/v1/documents/{id}` | DELETE | Delete document (owner/admin) | `document.delete` | Member 2 | Phase 1.8 |
| `/api/v1/search/hybrid` | POST | Hybrid semantic + BM25 search | `ai.search` | Member 1 & Member 2 | Phase 2.2 |
| `/api/v1/chat/query` | POST | Citation-backed RAG Q&A | `ai.chat` | Member 1 & Member 2 | Phase 2.2 |
| `/api/v1/chat/stream` | POST (SSE) | Real-time token streaming Q&A | `ai.chat` | Member 1 & Member 2 | Phase 2.2 |
| `/api/v1/graph/query` | POST | Knowledge Graph entity traversal | `ai.search` | Member 1 & Member 2 | Phase 2.4 |
| `/api/v1/analytics` | GET | Platform & project analytics | `analytics.view` | Member 2 | Phase 1.6 |
| `/api/v1/audit/logs` | GET | Security audit log trail | `audit.read` (OrgAdmin) | Member 2 | Phase 1.6 |

---

## 5. Frontend Review & UI Integration Feedback (Phase 1.2 — Member 3)

### 5.1 Contract Conformance Review
The Frontend Lead (Member 3) completed a comprehensive contract conformance review of all Phase 1.2 endpoints and OpenAPI schemas:
1. **Standardized Response Envelope (`ApiResponse<T>`)**:
   - Every success response adheres to `{ success: true, message: string, data: T }`.
   - The frontend centralized Axios client (`frontend/src/services/api.ts`) and domain service modules have been fully typed with TypeScript generics matching all Pydantic DTOs.
2. **Standardized Error Envelope (`ApiErrorResponse`)**:
   - Error responses uniformly follow `{ success: false, error: { code: string, message: string, details?: any } }`.
   - The frontend response interceptor unwraps this into a strongly-typed `ApiError` class with `ErrorCode` enum mappings.
3. **Paginated Collections (`PaginatedData<T>`)**:
   - Collections use 1-indexed `page`, `page_size`, `total`, `total_pages`, and `items: T[]`.
   - Verified on `GET /api/v1/users` and `GET /api/v1/documents`.
4. **SSE Real-Time Streaming (`/api/v1/chat/stream`)**:
   - Protocol verified: `event: citation`, `event: token`, `event: done`.
   - Frontend implementation utilizes standard `fetch` with `ReadableStream` and UTF-8 line decoding, bypassing `EventSource` limitations for POST bodies and Bearer authorization.

### 5.2 UI Feedback & Recommendations for Backend Leads
- **Citation Format in Streaming**: The `citation` event currently emits a single citation object or a list of citations. Frontend parser supports both formats seamlessly. Recommendation: ensure chunk text snippets are truncated to < 300 characters to keep SSE stream packet size light.
- **Upload File Size Limits**: Ensure 413 / `FILE_SIZE_EXCEEDED` returns clear `max_bytes` in `details` for client-side toast notifications.
- **Token Refresh Expiration Window**: The `expires_in` field is utilized by the frontend to trigger proactive silent token refreshes before expiration.


---

## Section 5 — Dashboard & AI Widget API Contracts (Phase 1.7)

> **Approved by**: Member 1 (Project Lead & AI Architect)
> **Implementer**: Member 2 (Backend Lead)
> **Consumer**: Member 3 (Frontend Lead)
> **Reference**: `docs/Architecture/dashboard-architecture.md` Section 3, ADR-020, ADR-022

---

### 5.1 GET /api/v1/dashboard

**Purpose**: Returns the authenticated user's personalized dashboard summary including user profile, organization metadata, and all KPI counters.

**Authorization**: Any authenticated user (role-specific fields controlled per role).

**Response Shape**:
```json
{
  "success": true,
  "message": "Dashboard summary retrieved successfully.",
  "data": {
    "user": {
      "id": "uuid",
      "full_name": "Siddhant Gupta",
      "email": "siddhant@acme.com",
      "role": "ORG_ADMIN",
      "avatar_url": null
    },
    "organization": {
      "id": "uuid",
      "name": "Acme Corp",
      "logo_url": null,
      "plan": "enterprise"
    },
    "kpi": {
      "total_projects": 12,
      "total_documents": 340,
      "total_members": 48,
      "upcoming_meetings": 3,
      "storage_used_bytes": 5368709120,
      "storage_quota_bytes": 107374182400,
      "ai_queries_today": 87
    },
    "greeting_time_of_day": "morning"
  }
}
```

**Notes**:
- `kpi.ai_queries_today` is `0` for roles below ORG_ADMIN.
- `greeting_time_of_day` is derived from user's timezone stored in organization metadata.
- Backend Redis cache key: `dashboard:{user_id}:{org_id}`, TTL 60s.

---

### 5.2 GET /api/v1/activity

**Purpose**: Returns a paginated, chronological feed of organizational activity events visible to the authenticated user.

**Authorization**: Any authenticated user (events are tenant-scoped; project-scoped events filtered to visible projects only).

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number (1-indexed) |
| page_size | int | 20 | Items per page (max 50) |
| filter | string | "all" | Filter by resource type: `all`, `document`, `project`, `meeting`, `user`, `ai_summary` |

**Response Shape**:
```json
{
  "success": true,
  "message": "Activity feed retrieved successfully.",
  "data": {
    "items": [
      {
        "id": "uuid",
        "actor": {
          "id": "uuid",
          "full_name": "John Smith",
          "avatar_url": null
        },
        "action": "uploaded",
        "resource_type": "document",
        "resource_id": "uuid",
        "resource_name": "Project Proposal.pdf",
        "metadata": {},
        "occurred_at": "2026-10-13T09:30:00Z"
      }
    ],
    "total": 245,
    "page": 1,
    "page_size": 20,
    "total_pages": 13
  }
}
```

---

### 5.3 GET /api/v1/projects/recent

**Purpose**: Returns recently updated projects accessible to the authenticated user.

**Authorization**: Any authenticated user (projects scoped to user's membership; ADMINs see all org projects).

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | int | 6 | Maximum number of projects (max 12) |

**Response Shape**:
```json
{
  "success": true,
  "message": "Recent projects retrieved successfully.",
  "data": [
    {
      "id": "uuid",
      "name": "AI Platform",
      "description": "Internal AI tooling project",
      "status": "active",
      "priority": "high",
      "progress_percent": 78,
      "deadline": "2026-08-15",
      "team_members": [
        { "id": "uuid", "full_name": "Alice Chen", "avatar_url": null }
      ],
      "document_count": 24,
      "updated_at": "2026-10-13T08:00:00Z"
    }
  ]
}
```

---

### 5.4 GET /api/v1/documents/recent

**Purpose**: Returns recently accessed or uploaded documents visible to the authenticated user.

**Authorization**: Any authenticated user (documents scoped to user's project memberships; ADMINs see all org documents).

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | int | 8 | Maximum number of documents (max 20) |

**Response Shape**:
```json
{
  "success": true,
  "message": "Recent documents retrieved successfully.",
  "data": [
    {
      "id": "uuid",
      "title": "Q3 Strategy.pdf",
      "file_type": "pdf",
      "file_size_bytes": 2048000,
      "project_id": "uuid",
      "project_name": "Strategy 2026",
      "uploaded_by": { "id": "uuid", "full_name": "Sarah Lee" },
      "uploaded_at": "2026-10-12T14:00:00Z",
      "last_accessed_at": "2026-10-13T09:00:00Z",
      "ai_summary_available": false
    }
  ]
}
```

---

### 5.5 GET /api/v1/notifications

**Purpose**: Returns the authenticated user's notifications, ordered by created_at descending.

**Authorization**: Any authenticated user (notifications are user-scoped — no cross-user leakage).

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| page_size | int | 20 | Items per page (max 50) |
| unread_only | bool | false | When true, returns only unread notifications |

**Response Shape**:
```json
{
  "success": true,
  "message": "Notifications retrieved successfully.",
  "data": {
    "items": [
      {
        "id": "uuid",
        "type": "info",
        "title": "New document uploaded",
        "body": "John uploaded Project Proposal.pdf to AI Platform.",
        "action_url": "/documents/uuid",
        "is_read": false,
        "created_at": "2026-10-13T09:30:00Z"
      }
    ],
    "total": 12,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

**Related Endpoints**:
- `PATCH /api/v1/notifications/{id}/read` — Mark single notification as read.
- `POST /api/v1/notifications/read-all` — Mark all notifications as read.

---

### 5.6 GET /api/v1/analytics/summary

**Purpose**: Returns time-series analytics aggregated at the organization level for the selected period.

**Authorization**: ADMIN and ORG_ADMIN roles only. Returns `403 AUTHZ_INSUFFICIENT_ROLE` for all other roles.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| period | string | "week" | Aggregation period: `week`, `month`, `quarter`, `year` |

**Response Shape**:
```json
{
  "success": true,
  "message": "Analytics summary retrieved successfully.",
  "data": {
    "period": "week",
    "documents_uploaded": [
      { "label": "Mon", "value": 12 },
      { "label": "Tue", "value": 8 }
    ],
    "active_users": [
      { "label": "Mon", "value": 34 }
    ],
    "new_members": [
      { "label": "Mon", "value": 2 }
    ],
    "project_distribution": [
      { "status": "active", "count": 9 },
      { "status": "on_hold", "count": 2 },
      { "status": "completed", "count": 5 }
    ],
    "ai_usage_trend": [],
    "search_trend": []
  }
}
```

**Notes**:
- `ai_usage_trend` and `search_trend` are returned as empty arrays in Phase 1.7 and will be populated in Phase 2.
- Backend Redis cache key: `analytics:{org_id}:{period}`, TTL 300s.

---

### 5.7 POST /api/v1/ai/query (Phase 1.7 Stub)

**Purpose**: Accepts an AI query and returns a streamed SSE response. In Phase 1.7, returns a canned stub response. In Phase 2.2, this endpoint is replaced with the full RAG pipeline — no frontend changes required.

**Authorization**: Any authenticated user. Rate-limited to 60 requests/hour per user (Redis token bucket).

**Request Body**:
```json
{
  "query": "Summarize this week's activity",
  "context": {
    "project_id": null,
    "document_ids": []
  },
  "stream": true
}
```

**Response**: `Content-Type: text/event-stream`
```
event: token
data: {"token": "Here is a summary of this week"}

event: token
data: {"token": " activity: [stub response — AI engine activates in Phase 2.2]."}

event: done
data: {"sources": [], "query_id": "uuid"}
```

**Error Codes**:
| Code | HTTP | Description |
|------|------|-------------|
| `AI_RATE_LIMIT_EXCEEDED` | 429 | User has exceeded 60 queries/hour |
| `AI_QUERY_TOO_LONG` | 422 | Query exceeds 4096 characters |
| `AI_UNAVAILABLE` | 503 | AI service temporarily unavailable |

---

### 5.8 GET /api/v1/search

**Purpose**: Full-text search across projects, documents, users, and teams within the authenticated user's organization.

**Authorization**: Any authenticated user (results scoped to accessible resources per role).

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| q | string | required | Search query string |
| type | string | "all" | Filter by type: `all`, `project`, `document`, `user`, `team` |
| page | int | 1 | Page number |
| page_size | int | 10 | Results per page (max 20) |

**Response Shape**:
```json
{
  "success": true,
  "message": "Search completed successfully.",
  "data": {
    "query": "AI Platform",
    "total": 5,
    "items": [
      {
        "type": "project",
        "id": "uuid",
        "title": "AI Platform",
        "subtitle": "Internal AI tooling project — Active",
        "url": "/projects/uuid",
        "icon": "project",
        "relevance_score": 0.95
      }
    ]
  }
}
```
