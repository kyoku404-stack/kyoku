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

### 3.3 Document Management & Storage System (`/api/v1/documents`)

#### 3.3.1 Upload Document for Ingestion
- **Method**: `POST`
- **Path**: `/api/v1/documents/upload`
- **Auth**: Bearer JWT (`document.create` permission)
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: Binary file (PDF, DOCX, TXT, MD, RTF, PPTX, XLSX, CSV, PNG, JPG, WEBP)
  - `title`: string (optional, defaults to filename without extension)
  - `category`: string (optional, one of: `POLICIES`, `REPORTS`, `MEETING_MINUTES`, `RESEARCH`, `LEGAL`, `FINANCE`, `HR`, `TECHNICAL_DOCUMENTATION`, `PRESENTATIONS`, `TRAINING_MATERIALS`)
  - `tags`: string (optional, comma-separated tags)
  - `project_id`: UUID (optional, associated project container)
  - `description`: string (optional)
- **Response (202 Accepted)**:
```json
{
  "success": true,
  "message": "Document uploaded successfully and queued for AI ingestion.",
  "data": {
    "document_id": "99a85f64-5717-4562-b3fc-2c963f66af11",
    "filename": "Q3_Strategic_Plan.pdf",
    "original_filename": "Q3 Strategic Plan Final.pdf",
    "file_type": "application/pdf",
    "file_size": 2458120,
    "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "category": "REPORTS",
    "tags": ["strategy", "q3", "planning"],
    "version_number": 1,
    "status": "AWAITING_PROCESSING",
    "ai_ready": false,
    "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "uploader_id": "1fa85f64-5717-4562-b3fc-2c963f66afa1",
    "created_at": "2026-10-15T10:00:00Z"
  }
}
```
- **Error Codes**: `UNSUPPORTED_FILE_TYPE` (400), `FILE_SIZE_EXCEEDED` (400), `STORAGE_QUOTA_EXCEEDED` (400), `DUPLICATE_FILE_DETECTED` (409), `AUTH_PERMISSION_DENIED` (403)

#### 3.3.2 List Documents (Paginated & Filtered)
- **Method**: `GET`
- **Path**: `/api/v1/documents`
- **Auth**: Bearer JWT (`document.read` permission)
- **Query Parameters**:
  - `page`: integer (default: 1, min: 1)
  - `page_size`: integer (default: 20, max: 100)
  - `status`: string (optional: `PENDING`, `VALIDATED`, `AWAITING_PROCESSING`, `QUEUED`, `EXTRACTING`, `CHUNKING`, `EMBEDDING`, `READY_FOR_AI`, `FAILED`, `ARCHIVED`)
  - `category`: string (optional, e.g. `REPORTS`, `POLICIES`)
  - `file_type`: string (optional, e.g. `pdf`, `docx`, `png`)
  - `project_id`: UUID (optional filter by project)
  - `uploader_id`: UUID (optional filter by uploader)
  - `search`: string (optional search in filename, title, tags)
  - `sort_by`: string (optional: `created_at`, `filename`, `file_size`, default: `created_at`)
  - `sort_order`: string (optional: `asc`, `desc`, default: `desc`)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Documents retrieved successfully.",
  "data": {
    "items": [
      {
        "id": "99a85f64-5717-4562-b3fc-2c963f66af11",
        "filename": "Q3_Strategic_Plan.pdf",
        "title": "Q3 Strategic Plan",
        "file_type": "application/pdf",
        "file_size": 2458120,
        "category": "REPORTS",
        "tags": ["strategy", "q3"],
        "version_number": 1,
        "status": "READY_FOR_AI",
        "ai_ready": true,
        "chunk_count": 42,
        "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "uploader_id": "1fa85f64-5717-4562-b3fc-2c963f66afa1",
        "uploader_name": "Jane Doe",
        "created_at": "2026-10-15T10:00:00Z",
        "updated_at": "2026-10-15T10:05:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

#### 3.3.3 Retrieve Document Details & Version History
- **Method**: `GET`
- **Path**: `/api/v1/documents/{id}`
- **Auth**: Bearer JWT (`document.read` permission)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Document metadata retrieved successfully.",
  "data": {
    "id": "99a85f64-5717-4562-b3fc-2c963f66af11",
    "organization_id": "8bc92d11-3456-4211-89ab-1234567890ab",
    "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "uploader_id": "1fa85f64-5717-4562-b3fc-2c963f66afa1",
    "filename": "Q3_Strategic_Plan.pdf",
    "original_filename": "Q3 Strategic Plan Final.pdf",
    "title": "Q3 Strategic Plan",
    "description": "Executive strategic overview for Q3 initiatives.",
    "file_type": "application/pdf",
    "file_size": 2458120,
    "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "category": "REPORTS",
    "tags": ["strategy", "q3", "planning"],
    "current_version_number": 2,
    "status": "READY_FOR_AI",
    "ai_ready": true,
    "chunk_count": 42,
    "metadata_json": {
      "page_count": 14,
      "author": "Jane Doe",
      "word_count": 4200,
      "language": "en",
      "ocr_applied": false
    },
    "versions": [
      {
        "version_number": 2,
        "file_size": 2458120,
        "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "uploader_id": "1fa85f64-5717-4562-b3fc-2c963f66afa1",
        "change_notes": "Updated financial forecasts in Section 4.",
        "created_at": "2026-10-15T12:00:00Z"
      },
      {
        "version_number": 1,
        "file_size": 2341000,
        "checksum_sha256": "a1b2c3d4e5f6...",
        "uploader_id": "1fa85f64-5717-4562-b3fc-2c963f66afa1",
        "change_notes": "Initial upload.",
        "created_at": "2026-10-15T10:00:00Z"
      }
    ],
    "created_at": "2026-10-15T10:00:00Z",
    "updated_at": "2026-10-15T12:00:00Z"
  }
}
```
- **Error Codes**: `NOT_FOUND` (404), `AUTH_PERMISSION_DENIED` (403), `AUTH_ORGANIZATION_MISMATCH` (403)

#### 3.3.4 Download Document Binary Stream
- **Method**: `GET`
- **Path**: `/api/v1/documents/{id}/download`
- **Auth**: Bearer JWT (`document.download` permission)
- **Query Parameters**:
  - `version`: integer (optional, defaults to current active version)
- **Response Headers**:
  - `Content-Type`: MIME type of document (e.g. `application/pdf`)
  - `Content-Disposition`: `attachment; filename="Q3_Strategic_Plan.pdf"`
  - `Content-Length`: Size in bytes
- **Response**: Binary byte stream (200 OK)
- **Error Codes**: `NOT_FOUND` (404), `AUTH_PERMISSION_DENIED` (403), `AUTH_ORGANIZATION_MISMATCH` (403)

#### 3.3.5 Preview Document
- **Method**: `GET`
- **Path**: `/api/v1/documents/{id}/preview`
- **Auth**: Bearer JWT (`document.preview` permission)
- **Query Parameters**:
  - `version`: integer (optional, defaults to current active version)
  - `format`: string (optional: `html`, `text`, `thumbnail`, default depends on MIME type)
- **Response Headers**:
  - `Content-Type`: `application/pdf`, `text/html; charset=utf-8`, `text/plain; charset=utf-8`, or `image/webp`
- **Response**: Rendered preview stream (200 OK)
- **Error Codes**: `NOT_FOUND` (404), `AUTH_PERMISSION_DENIED` (403), `PREVIEW_UNAVAILABLE` (422)

#### 3.3.6 Update Document Metadata
- **Method**: `PATCH`
- **Path**: `/api/v1/documents/{id}`
- **Auth**: Bearer JWT (`document.update` permission or uploader ownership bypass)
- **Request Body**:
```json
{
  "title": "Q3 Enterprise Strategy Plan (Revised)",
  "description": "Updated corporate objectives and revenue targets.",
  "category": "REPORTS",
  "tags": ["strategy", "q3", "executive"],
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Document metadata updated successfully.",
  "data": {
    "id": "99a85f64-5717-4562-b3fc-2c963f66af11",
    "title": "Q3 Enterprise Strategy Plan (Revised)",
    "category": "REPORTS",
    "tags": ["strategy", "q3", "executive"],
    "updated_at": "2026-10-15T14:00:00Z"
  }
}
```
- **Error Codes**: `NOT_FOUND` (404), `AUTH_PERMISSION_DENIED` (403), `AUTH_ORGANIZATION_MISMATCH` (403)

#### 3.3.7 Upload New Version
- **Method**: `POST`
- **Path**: `/api/v1/documents/{id}/version`
- **Auth**: Bearer JWT (`document.version` permission or uploader ownership bypass)
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: Binary file (must match supported MIME formats)
  - `change_notes`: string (required summary of changes)
- **Response (201 Created)**:
```json
{
  "success": true,
  "message": "New document version uploaded successfully and queued for AI re-indexing.",
  "data": {
    "document_id": "99a85f64-5717-4562-b3fc-2c963f66af11",
    "version_number": 2,
    "filename": "Q3_Strategic_Plan.pdf",
    "file_size": 2458120,
    "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "change_notes": "Updated financial forecasts in Section 4.",
    "status": "AWAITING_PROCESSING",
    "created_at": "2026-10-15T12:00:00Z"
  }
}
```
- **Error Codes**: `NOT_FOUND` (404), `UNSUPPORTED_FILE_TYPE` (400), `FILE_SIZE_EXCEEDED` (400), `STORAGE_QUOTA_EXCEEDED` (400), `AUTH_PERMISSION_DENIED` (403)

#### 3.3.8 Archive or Soft-Delete Document
- **Method**: `DELETE`
- **Path**: `/api/v1/documents/{id}`
- **Auth**: Bearer JWT (`document.delete` permission or uploader ownership bypass)
- **Query Parameters**:
  - `action`: string (optional: `archive` or `delete`, default: `delete`)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Document deleted successfully.",
  "data": {
    "id": "99a85f64-5717-4562-b3fc-2c963f66af11",
    "is_deleted": true,
    "deleted_at": "2026-10-15T15:00:00Z"
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
| `/api/v1/documents/{id}` | GET | Retrieve document metadata & versions | `document.read` | Member 2 | Phase 1.8 |
| `/api/v1/documents/{id}/download` | GET | Download binary file stream | `document.download` | Member 2 | Phase 1.8 |
| `/api/v1/documents/{id}/preview` | GET | Rendered preview stream | `document.preview` | Member 2 | Phase 1.8 |
| `/api/v1/documents/{id}` | PATCH | Update metadata (title/category/tags) | `document.update` (owner bypass) | Member 2 | Phase 1.8 |
| `/api/v1/documents/{id}/version` | POST | Upload new revision | `document.version` (owner bypass) | Member 2 | Phase 1.8 |
| `/api/v1/documents/{id}` | DELETE | Soft-delete / archive document | `document.delete` (owner bypass) | Member 2 | Phase 1.8 |
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

---

## 6. Observability, Health Check & System Monitoring API Contracts

### 6.1 Overview & Architecture
`devdocs/p1/p1.9.txt` mandates a comprehensive observability framework exposing multi-tier health probes, standard Prometheus metrics exposition, and an aggregated JSON metrics summary for enterprise UI dashboards.

---

### 6.2 GET /health

**Purpose**: Composite health probe evaluating overall platform operational readiness across all subsystem dependencies.

**Authorization**: Public (accessible to load balancers, container orchestrators, and uptime monitors).

**Headers**:
- Response includes `X-Request-ID` correlation identifier.

**Response Status Codes**:
- `200 OK`: All critical dependencies are operational (`"healthy"` or `"degraded"`).
- `503 Service Unavailable`: One or more critical subsystems (e.g., Database) are offline (`"unhealthy"`).

**Response Shape (200 OK)**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-10-21T21:45:00Z",
  "uptime_seconds": 86400,
  "environment": "production",
  "dependencies": {
    "database": {
      "status": "healthy",
      "latency_ms": 1.25,
      "connection_pool": {
        "size": 20,
        "checked_out": 2,
        "overflow": 0
      },
      "vector_extension_enabled": true
    },
    "storage": {
      "status": "healthy",
      "latency_ms": 0.82,
      "writable": true,
      "free_space_bytes": 107374182400,
      "used_percent": 14.5
    },
    "api": {
      "status": "healthy",
      "memory_rss_mb": 145.2,
      "active_requests": 3
    },
    "auth": {
      "status": "healthy",
      "jwt_secret_configured": true,
      "algorithm": "HS256"
    }
  }
}
```

---

### 6.3 GET /health/database

**Purpose**: Isolated database health probe verifying PostgreSQL connection pool responsiveness and pgvector extension readiness.

**Authorization**: Public / Orchestrator probe.

**Response Status Codes**:
- `200 OK`: Database connected and ping query succeeded.
- `503 Service Unavailable`: Connection failed or timeout.

**Response Shape (200 OK)**:
```json
{
  "status": "healthy",
  "latency_ms": 1.15,
  "database": "postgresql",
  "version": "PostgreSQL 16.4",
  "vector_extension": true,
  "pool": {
    "size": 20,
    "checked_out": 1,
    "overflow": 0
  }
}
```

---

### 6.4 GET /health/storage

**Purpose**: Isolated storage filesystem health probe validating write/read accessibility and capacity thresholds.

**Authorization**: Public / Orchestrator probe.

**Response Status Codes**:
- `200 OK`: Storage root directory writable and disk usage below critical threshold (< 95%).
- `503 Service Unavailable`: Storage unmounted, read-only filesystem, or disk full.

**Response Shape (200 OK)**:
```json
{
  "status": "healthy",
  "storage_root": "/app/storage",
  "writable": true,
  "latency_ms": 0.90,
  "total_bytes": 1073741824000,
  "used_bytes": 155692564480,
  "free_bytes": 918049259520,
  "used_percent": 14.5
}
```

---

### 6.5 GET /health/api

**Purpose**: Process-level runtime probe inspecting API gateway uptime, event loop latency, and memory footprint.

**Authorization**: Public / Orchestrator probe.

**Response Shape (200 OK)**:
```json
{
  "status": "healthy",
  "uptime_seconds": 86400,
  "python_version": "3.12.3",
  "memory_rss_mb": 145.2,
  "cpu_percent": 2.4,
  "active_requests": 2
}
```

---

### 6.6 GET /health/auth

**Purpose**: Authentication readiness probe validating JWT secret keys, cryptographic providers, and token revocation infrastructure.

**Authorization**: Public / Orchestrator probe.

**Response Shape (200 OK)**:
```json
{
  "status": "healthy",
  "jwt_secret_configured": true,
  "algorithm": "HS256",
  "access_token_expire_minutes": 60,
  "refresh_token_expire_days": 7
}
```

---

### 6.7 GET /metrics

**Purpose**: Standard Prometheus text exposition endpoint scraping operational counters, gauges, and latency histograms.

**Authorization**: Internal / Prometheus scraper (or protected via basic auth/Bearer in production).

**Content-Type**: `text/plain; version=0.0.4; charset=utf-8`

**Sample Output**:
```text
# HELP http_requests_total Total number of HTTP requests processed.
# TYPE http_requests_total counter
http_requests_total{handler="/api/v1/documents",method="GET",status="200"} 412.0
http_requests_total{handler="/api/v1/auth/login",method="POST",status="200"} 89.0
http_requests_total{handler="/api/v1/auth/login",method="POST",status="401"} 3.0

# HELP http_request_duration_seconds HTTP request latency histogram.
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{handler="/api/v1/documents",le="0.01"} 120.0
http_request_duration_seconds_bucket{handler="/api/v1/documents",le="0.05"} 390.0
http_request_duration_seconds_bucket{handler="/api/v1/documents",le="+Inf"} 412.0
http_request_duration_seconds_sum{handler="/api/v1/documents"} 8.42
http_request_duration_seconds_count{handler="/api/v1/documents"} 412.0

# HELP db_pool_active_connections Current active database connections.
# TYPE db_pool_active_connections gauge
db_pool_active_connections 2.0

# HELP storage_used_bytes Total storage bytes used.
# TYPE storage_used_bytes gauge
storage_used_bytes 155692564480.0
```

---

### 6.8 GET /api/v1/metrics/summary

**Purpose**: Aggregated JSON metrics endpoint powering the frontend System Status, Monitoring Dashboard, and Admin Telemetry cards.

**Authorization**: Authenticated User (`audit.read` or `system.metrics` permission).

**Response Shape (200 OK)**:
```json
{
  "success": true,
  "message": "System telemetry summary retrieved successfully.",
  "data": {
    "system_status": "healthy",
    "uptime_seconds": 86400,
    "timestamp": "2026-10-21T21:45:00Z",
    "kpis": {
      "requests_per_second": 14.2,
      "p95_latency_ms": 38.5,
      "error_rate_percent": 0.05,
      "active_users": 18,
      "total_documents": 240,
      "storage_used_bytes": 155692564480,
      "storage_capacity_bytes": 1073741824000,
      "storage_percent": 14.5,
      "database_pool_usage_percent": 10.0
    },
    "alerts": [
      {
        "id": "alt-001",
        "severity": "INFO",
        "title": "Scheduled Storage Backup",
        "message": "Automated snapshot completed with SHA-256 verification.",
        "timestamp": "2026-10-21T21:00:00Z"
      }
    ],
    "subsystem_health": {
      "database": "healthy",
      "storage": "healthy",
      "api": "healthy",
      "auth": "healthy"
    }
  }
}
```

---

## 7. Production Gateway, Deployment Routing & Security Specifications

### 7.1 Reverse Proxy Routing Matrix

In production environments, all traffic ingresses via the Nginx Reverse Proxy gateway on ports 80 (HTTP redirect) and 443 (HTTPS TLS 1.3/1.2).

| Incoming Path Pattern | Target Container Service | Target Port | Access Policy | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `GET /health` | `keep-backend` | `8000` | Public / Load Balancer | Fast composite probe (< 50ms) |
| `GET /health/*` | `keep-backend` | `8000` | Internal / Admin | Subsystem diagnostic probes |
| `/api/v1/*` | `keep-backend` | `8000` | Public / Authenticated | Core REST & SSE API endpoints |
| `/*` | `keep-frontend` | `3000` | Public | Next.js / React SPA with HTML5 fallback |
| `/metrics` | `keep-backend` | `8000` | Internal Network Only | Prometheus scraping (blocked at ingress) |
| `/_next/static/*` | `keep-frontend` | `3000` | Public | Immutable static asset cache (1 year) |

### 7.2 Standard Ingress Headers Injected by Reverse Proxy

The reverse proxy normalizes incoming client requests by injecting the following standard correlation and proxy headers before forwarding to backend services:
- `X-Forwarded-For: $remote_addr`
- `X-Forwarded-Proto: https`
- `X-Forwarded-Host: $host`
- `X-Forwarded-Port: 443`
- `X-Request-ID: $request_id` (generated by proxy if absent from incoming client request)

### 7.3 Mandatory Production Response Security Headers

All responses transmitted through the public gateway must contain the following enterprise security headers:
```http
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), camera=(), microphone=()
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https: wss:; frame-ancestors 'none';
```

### 7.4 Ingress Health Check SLA & Deployment Rollback Protocol

- **Liveness Polling Frequency**: Every 10 seconds.
- **Health Gate Response SLA**: Composite probe `GET /health` must return `HTTP 200 OK` with `"system_status": "healthy"` in `< 500ms`.
- **Automatic Rollback Trigger**: In CI/CD rolling deployments, if `GET /health` fails 3 consecutive attempts (or exceeds 60s timeout post-startup), traffic remains bound to the previous healthy container version and an automated rollback is executed.

---

## 8. Ingestion Pipeline & AI Processing Endpoints (Phase 2.1)

### 8.1 Ingestion Endpoints Summary Table

| Method | Path | Required Permission | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/ingestion/start` | `document.ingest` | Initiates asynchronous ingestion pipeline for an uploaded document |
| `GET` | `/api/v1/ingestion/status/{id}` | `document.read` | Retrieves real-time pipeline status, active stage, and chunk progress |
| `GET` | `/api/v1/ingestion/jobs` | `document.read` | Returns a paginated list of ingestion jobs for the tenant |
| `POST` | `/api/v1/ingestion/retry/{id}` | `document.ingest` | Retries a previously failed or dead-lettered ingestion job |
| `GET` | `/api/v1/ingestion/statistics` | `analytics.read` | Returns tenant-wide ingestion throughput, chunk counts, and error rates |

---

### 8.2 Ingestion Endpoint Specifications

#### 8.2.1 Start Document Ingestion
- **Method**: `POST`
- **Path**: `/api/v1/ingestion/start`
- **Auth**: Bearer JWT (`document.ingest` permission)
- **Request Body**:
```json
{
  "document_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "document_version_id": "4fa85f64-5717-4562-b3fc-2c963f66afa7",
  "force_ocr": false,
  "chunking_strategy": "SEMANTIC_HEADING_AWARE",
  "target_chunk_size": 512,
  "chunk_overlap": 50,
  "embedding_provider": "OPENAI",
  "embedding_model": "text-embedding-3-small"
}
```
- **Response (202 Accepted)**:
```json
{
  "success": true,
  "message": "Document ingestion job enqueued successfully.",
  "data": {
    "job_id": "7fa85f64-5717-4562-b3fc-2c963f66afb1",
    "document_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "status": "PENDING",
    "queue_name": "ai_ingestion_queue",
    "enqueued_at": "2026-10-25T01:30:00Z"
  }
}
```
- **Error Codes**: `NOT_FOUND` (404), `DOCUMENT_ALREADY_PROCESSING` (409), `UNSUPPORTED_MEDIA_TYPE` (415)

#### 8.2.2 Get Ingestion Job Status
- **Method**: `GET`
- **Path**: `/api/v1/ingestion/status/{id}`
- **Auth**: Bearer JWT (`document.read` permission)
- **Path Parameters**:
  - `id`: UUID (Ingestion job ID or Document ID)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "job_id": "7fa85f64-5717-4562-b3fc-2c963f66afb1",
    "document_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "status": "CHUNKING",
    "progress_percent": 65.0,
    "current_stage": "semantic_chunking",
    "total_pages": 14,
    "processed_pages": 14,
    "chunks_generated": 48,
    "embeddings_generated": 0,
    "ocr_applied": false,
    "retry_count": 0,
    "error_message": null,
    "started_at": "2026-10-25T01:30:02Z",
    "completed_at": null,
    "duration_seconds": 3.8
  }
}
```
- **Error Codes**: `NOT_FOUND` (404), `AUTH_FORBIDDEN` (403)

#### 8.2.3 List Ingestion Jobs
- **Method**: `GET`
- **Path**: `/api/v1/ingestion/jobs`
- **Auth**: Bearer JWT (`document.read` permission)
- **Query Parameters**:
  - `page`: integer (default 1)
  - `page_size`: integer (default 20, max 100)
  - `status`: string (optional filter: `PENDING`, `EXTRACTING`, `NORMALIZING`, `CHUNKING`, `EMBEDDING`, `INDEXING`, `COMPLETED`, `FAILED`, `RETRYING`)
  - `document_id`: UUID (optional filter)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "job_id": "7fa85f64-5717-4562-b3fc-2c963f66afb1",
        "document_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "document_title": "Quarterly_Security_Report.pdf",
        "status": "COMPLETED",
        "chunks_generated": 48,
        "duration_seconds": 12.4,
        "created_at": "2026-10-25T01:30:00Z",
        "completed_at": "2026-10-25T01:30:12Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

#### 8.2.4 Retry Failed Ingestion Job
- **Method**: `POST`
- **Path**: `/api/v1/ingestion/retry/{id}`
- **Auth**: Bearer JWT (`document.ingest` permission)
- **Path Parameters**:
  - `id`: UUID (Ingestion job ID)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Ingestion job re-enqueued for retry.",
  "data": {
    "job_id": "7fa85f64-5717-4562-b3fc-2c963f66afb1",
    "status": "RETRYING",
    "retry_count": 1,
    "enqueued_at": "2026-10-25T01:35:00Z"
  }
}
```
- **Error Codes**: `NOT_FOUND` (404), `INVALID_JOB_STATE` (400 - only FAILED jobs can be retried)

#### 8.2.5 Get Ingestion Pipeline Statistics
- **Method**: `GET`
- **Path**: `/api/v1/ingestion/statistics`
- **Auth**: Bearer JWT (`analytics.read` permission)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "organization_id": "00000000-0000-0000-0000-000000000001",
    "total_jobs": 150,
    "completed_jobs": 142,
    "failed_jobs": 3,
    "pending_jobs": 5,
    "total_chunks_indexed": 4820,
    "average_duration_seconds": 8.6,
    "average_throughput_pages_per_minute": 95.4,
    "ocr_utilization_percent": 12.0,
    "retry_success_rate_percent": 88.5
  }
}
```

---

## 9. Phase 2.2 — RAG Engine & Semantic Search APIs (`/api/v1/rag`)

### 9.1 Overview & Security Model
- **Auth Requirement**: All endpoints require a valid JWT Bearer Token.
- **Tenant Isolation**: Mandatory `organization_id` isolation extracted from JWT claims.
- **Permission Scope**:
  - `rag.query`: Execute queries and read conversational answers.
  - `rag.history`: Read conversation history.
  - `rag.feedback`: Submit answer satisfaction feedback.
  - `rag.analytics`: View aggregate RAG engine metrics.

### 9.2 Endpoints

#### 9.2.1 Submit AI Question (RAG Query)
- **Method**: `POST`
- **Path**: `/api/v1/rag/query`
- **Auth**: Bearer JWT (`rag.query` permission)
- **Request Body**:
```json
{
  "query": "What is our employee leave policy?",
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "department_id": "7fa85f64-5717-4562-b3fc-2c963f66afb2",
  "project_id": null,
  "hybrid_dense_weight": 0.65,
  "hybrid_sparse_weight": 0.35,
  "top_k": 5,
  "stream": false
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Query processed successfully.",
  "data": {
    "query_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "query": "What is our employee leave policy?",
    "answer": "All full-time employees are entitled to 20 days of paid annual leave per year, requiring approval from their immediate supervisor [Doc 1, Page 18]. Medical leave is granted up to 10 days with a medical certificate [Doc 1, Page 20].",
    "confidence_score": 0.885,
    "is_grounded": true,
    "processing_time_ms": 420.5,
    "citations": [
      {
        "citation_id": "cit_1",
        "document_id": "d3b07384-d113-46fb-a0b4-eb40a3f7ff95",
        "document_title": "Employee Handbook.pdf",
        "document_version_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "page_number": 18,
        "section": "Section 4.2: Paid Annual Leave",
        "chunk_id": "c1a2b3c4-d5e6-7890-abcd-ef1234567890",
        "similarity_score": 0.892,
        "excerpt": "All full-time employees are entitled to 20 days of paid annual leave..."
      }
    ],
    "retrieval_metrics": {
      "dense_candidates": 30,
      "sparse_candidates": 30,
      "reranked_candidates": 5,
      "latency_retrieval_ms": 115.2,
      "latency_generation_ms": 305.3,
      "tokens_prompt": 850,
      "tokens_completion": 92
    }
  }
}
```
- **Error Codes**: `VALIDATION_ERROR` (422), `UNAUTHORIZED` (401), `CIRCUIT_BREAKER_LOW_CONFIDENCE` (200 with fallback refusal message)

#### 9.2.2 Get Conversation History
- **Method**: `GET`
- **Path**: `/api/v1/rag/history`
- **Auth**: Bearer JWT (`rag.history` permission)
- **Query Parameters**:
  - `session_id` (optional, UUID): Specific chat session. If omitted, returns all sessions for the user.
  - `page` (optional, int, default 1)
  - `page_size` (optional, int, default 20)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "title": "Employee Leave Policy Q&A",
        "created_at": "2026-10-26T02:00:00Z",
        "updated_at": "2026-10-26T02:15:00Z",
        "message_count": 4,
        "messages": [
          {
            "message_id": "m1",
            "role": "user",
            "content": "What is our leave policy?",
            "created_at": "2026-10-26T02:00:00Z"
          },
          {
            "message_id": "m2",
            "role": "assistant",
            "content": "All full-time employees are entitled to 20 days...",
            "citations_json": "[...]",
            "created_at": "2026-10-26T02:00:02Z"
          }
        ]
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

#### 9.2.3 Retrieve Citations Detail
- **Method**: `GET`
- **Path**: `/api/v1/rag/citations/{id}`
- **Auth**: Bearer JWT (`rag.query` permission)
- **Path Parameters**:
  - `id`: UUID (Chunk ID or Citation ID)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "citation_id": "cit_1",
    "chunk_id": "c1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "document_id": "d3b07384-d113-46fb-a0b4-eb40a3f7ff95",
    "document_title": "Employee Handbook.pdf",
    "document_version_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "chunk_index": 12,
    "page_number": 18,
    "section": "Section 4.2: Paid Annual Leave",
    "full_content": "All full-time employees are entitled to 20 days of paid annual leave...",
    "metadata": {
      "author": "People Operations",
      "department": "Human Resources",
      "upload_date": "2026-09-01T10:00:00Z"
    }
  }
}
```
- **Error Codes**: `NOT_FOUND` (404)

#### 9.2.4 Submit User Feedback
- **Method**: `POST`
- **Path**: `/api/v1/rag/feedback`
- **Auth**: Bearer JWT (`rag.feedback` permission)
- **Request Body**:
```json
{
  "query_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "rating": 5,
  "is_helpful": true,
  "comment": "Accurate response with direct citation to policy handbook."
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Feedback submitted successfully.",
  "data": {
    "feedback_id": "fb_123",
    "recorded_at": "2026-10-26T02:20:00Z"
  }
}
```

#### 9.2.5 Get RAG Engine Statistics
- **Method**: `GET`
- **Path**: `/api/v1/rag/statistics`
- **Auth**: Bearer JWT (`rag.analytics` permission)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "organization_id": "00000000-0000-0000-0000-000000000001",
    "total_queries": 1250,
    "total_sessions": 310,
    "average_latency_ms": 485.2,
    "average_confidence_score": 0.862,
    "hallucination_refusal_count": 14,
    "positive_feedback_percentage": 94.2,
    "total_citations_rendered": 3820,
    "cache_hit_ratio": 0.32
  }
}
```

---

## 10. Phase 2.3 — Enterprise AI Assistant & Agentic Workflow APIs (`/api/v1/assistant`)

### 10.1 Overview & Security Model
- **Auth Requirement**: All endpoints require a valid JWT Bearer Token.
- **Tenant Isolation**: Strict `organization_id` boundary enforced across all assistant tasks, tools, and history.
- **Permission Scope**:
  - `assistant.chat`: Interact with conversational assistant and execute read-only tools.
  - `assistant.task`: Submit multi-step automated task execution plans.
  - `assistant.report`: Generate organizational summaries and analytical reports.
  - `assistant.approve`: Review, approve, or reject pending human-in-the-loop actions.

### 10.2 Endpoints

#### 10.2.1 Chat with Enterprise AI Assistant
- **Method**: `POST`
- **Path**: `/api/v1/assistant/chat`
- **Auth**: Bearer JWT (`assistant.chat` permission)
- **Request Body**:
```json
{
  "message": "Summarize all HR documents from last month and email me the summary.",
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "department_id": null,
  "project_id": null
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Assistant message processed successfully.",
  "data": {
    "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "message_id": "m_1029384756",
    "reply": "I retrieved 4 HR policy documents and generated a summary. Sending the email requires your confirmation.",
    "detected_intent": "DOCUMENT_SUMMARIZATION",
    "workflow_id": "wf_49a85f64-5717-4562-b3fc-2c963f66af01",
    "tools_executed": ["DocumentTool", "ReportTool"],
    "requires_approval": true,
    "approval_id": "appr_7fa85f64-5717-4562-b3fc-2c963f66afb2",
    "created_at": "2026-10-27T10:00:00Z"
  }
}
```

#### 10.2.2 Execute Multi-Step AI Task
- **Method**: `POST`
- **Path**: `/api/v1/assistant/task`
- **Auth**: Bearer JWT (`assistant.task` permission)
- **Request Body**:
```json
{
  "title": "Quarterly Policy Audit",
  "instructions": "Extract key compliance policies from all PDF reports and generate an audit checklist.",
  "session_id": null,
  "context": {
    "category": "COMPLIANCE",
    "max_documents": 10
  }
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Task plan formulated and execution initiated.",
  "data": {
    "workflow_id": "wf_11a85f64-5717-4562-b3fc-2c963f66af99",
    "title": "Quarterly Policy Audit",
    "status": "COMPLETED",
    "total_steps": 3,
    "completed_steps": 3,
    "steps": [
      {
        "step_number": 1,
        "tool_name": "DocumentTool",
        "description": "Fetch compliance documents",
        "status": "COMPLETED",
        "latency_ms": 120.5
      },
      {
        "step_number": 2,
        "tool_name": "SearchTool",
        "description": "Retrieve audit sections via semantic RAG",
        "status": "COMPLETED",
        "latency_ms": 280.1
      },
      {
        "step_number": 3,
        "tool_name": "ReportTool",
        "description": "Synthesize compliance checklist",
        "status": "COMPLETED",
        "latency_ms": 310.4
      }
    ],
    "result_summary": "Successfully formulated audit checklist from 3 compliance documents."
  }
}
```

#### 10.2.3 Retrieve Conversation History
- **Method**: `GET`
- **Path**: `/api/v1/assistant/history`
- **Auth**: Bearer JWT (`assistant.chat` permission)
- **Query Parameters**:
  - `session_id` (optional, UUID): Specific chat session. If omitted, returns all sessions.
  - `page` (optional, int, default 1)
  - `page_size` (optional, int, default 20)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "title": "HR Documents & Policy Summary",
        "created_at": "2026-10-27T09:30:00Z",
        "updated_at": "2026-10-27T10:00:00Z",
        "message_count": 2,
        "messages": [
          {
            "id": "m1",
            "role": "user",
            "content": "Summarize HR documents from last month.",
            "created_at": "2026-10-27T09:30:00Z"
          },
          {
            "id": "m2",
            "role": "assistant",
            "content": "Here is the summary of HR documents...",
            "created_at": "2026-10-27T09:30:04Z"
          }
        ]
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

#### 10.2.4 Generate Structured Enterprise Report
- **Method**: `POST`
- **Path**: `/api/v1/assistant/report`
- **Auth**: Bearer JWT (`assistant.report` permission)
- **Request Body**:
```json
{
  "report_type": "WEEKLY_ROLLUP",
  "title": "Engineering Knowledge Base Weekly Rollup",
  "format": "MARKDOWN",
  "filters": {
    "department_id": "7fa85f64-5717-4562-b3fc-2c963f66afb2",
    "days_back": 7
  }
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Report generated successfully.",
  "data": {
    "report_id": "rep_9fa85f64-5717-4562-b3fc-2c963f66afe1",
    "report_type": "WEEKLY_ROLLUP",
    "title": "Engineering Knowledge Base Weekly Rollup",
    "format": "MARKDOWN",
    "content": "# Weekly Knowledge Rollup\n\n## Overview\nDuring the past 7 days, 14 new documents were ingested...",
    "created_at": "2026-10-27T10:15:00Z"
  }
}
```

#### 10.2.5 List & Inspect Workflows
- **Method**: `GET`
- **Path**: `/api/v1/assistant/workflows`
- **Auth**: Bearer JWT (`assistant.task` permission)
- **Query Parameters**:
  - `status` (optional, string): Filter by status (`RUNNING`, `WAITING_APPROVAL`, `COMPLETED`, `FAILED`)
  - `page` (optional, int, default 1)
  - `page_size` (optional, int, default 20)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "workflows": [
      {
        "id": "wf_11a85f64-5717-4562-b3fc-2c963f66af99",
        "title": "Quarterly Policy Audit",
        "trigger_type": "TASK",
        "status": "COMPLETED",
        "total_steps": 3,
        "completed_steps": 3,
        "created_at": "2026-10-27T08:00:00Z",
        "completed_at": "2026-10-27T08:00:02Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

#### 10.2.6 Human-in-the-Loop Action Approval
- **Method**: `POST`
- **Path**: `/api/v1/assistant/approve`
- **Auth**: Bearer JWT (`assistant.approve` permission)
- **Request Body**:
```json
{
  "approval_id": "appr_7fa85f64-5717-4562-b3fc-2c963f66afb2",
  "decision": "APPROVED",
  "reason": "Verified document archival meets compliance policy."
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Approval processed and action executed successfully.",
  "data": {
    "approval_id": "appr_7fa85f64-5717-4562-b3fc-2c963f66afb2",
    "workflow_id": "wf_49a85f64-5717-4562-b3fc-2c963f66af01",
    "decision": "APPROVED",
    "status": "COMPLETED",
    "executed_at": "2026-10-27T10:05:00Z"
  }
}
```

#### 10.2.7 Get Proactive Recommendations
- **Method**: `GET`
- **Path**: `/api/v1/assistant/recommendations`
- **Auth**: Bearer JWT (`assistant.chat` permission)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "id": "rec_1",
        "category": "FREQUENT_DOCUMENTS",
        "title": "Employee Handbook 2026",
        "description": "High query traffic detected this week (42 inquiries).",
        "suggested_action": "Pin to workspace quick access"
      },
      {
        "id": "rec_2",
        "category": "MISSING_DOCUMENTATION",
        "title": "Remote Work Expenses",
        "description": "8 ungrounded queries identified regarding remote equipment stipend.",
        "suggested_action": "Upload policy guideline"
      }
    ]
  }
}
```

---

## 11. Phase 2.4 — Knowledge Graph & Enterprise Intelligence APIs (`/api/v1/graph`)

### 11.1 Overview & Security Model
- **Auth Requirement**: All endpoints require a valid JWT Bearer Token.
- **Tenant Isolation**: Mandatory `organization_id` boundary enforced at every graph traversal step. Cross-tenant traversal is strictly prohibited.
- **Permission Scope**:
  - `graph.read`: Query entities, inspect relationships, and view the Knowledge Explorer.
  - `graph.build`: Trigger full or incremental knowledge graph reconstruction.
  - `graph.intelligence`: Access impact analysis and subject-matter expertise discovery.

### 11.2 Endpoints

#### 11.2.1 Build Knowledge Graph
- **Method**: `POST`
- **Path**: `/api/v1/graph/build`
- **Auth**: Bearer JWT (`graph.build` permission)
- **Request Body**:
```json
{
  "rebuild_all": false,
  "confidence_threshold": 0.70,
  "include_documents": true,
  "include_organizational": true
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Knowledge graph build completed successfully.",
  "data": {
    "organization_id": "00000000-0000-0000-0000-000000000001",
    "entities_created": 45,
    "entities_updated": 12,
    "relationships_created": 88,
    "duration_seconds": 1.45,
    "total_entities": 120,
    "total_relationships": 260
  }
}
```

#### 11.2.2 Incrementally Update Graph
- **Method**: `POST`
- **Path**: `/api/v1/graph/update`
- **Auth**: Bearer JWT (`graph.build` permission)
- **Request Body**:
```json
{
  "document_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "text_content": "The AI Migration Project is led by Alice and applies to the Engineering department.",
  "metadata": {"category": "ARCHITECTURE"}
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Incremental graph update completed.",
  "data": {
    "entities_extracted": 3,
    "relationships_extracted": 2,
    "extracted_entities": [
      {"id": "e_1", "name": "AI Migration Project", "entity_type": "PROJECT"},
      {"id": "e_2", "name": "Alice", "entity_type": "EMPLOYEE"},
      {"id": "e_3", "name": "Engineering", "entity_type": "DEPARTMENT"}
    ],
    "extracted_relationships": [
      {"source": "Alice", "relation": "LEADS", "target": "AI Migration Project"},
      {"source": "AI Migration Project", "relation": "APPLIES_TO", "target": "Engineering"}
    ]
  }
}
```

#### 11.2.3 Retrieve Entity Details
- **Method**: `GET`
- **Path**: `/api/v1/graph/entity/{id}`
- **Auth**: Bearer JWT (`graph.read` permission)
- **Path Parameters**:
  - `id`: UUID (Entity ID)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": "e_1",
    "organization_id": "00000000-0000-0000-0000-000000000001",
    "name": "AI Migration Project",
    "entity_type": "PROJECT",
    "properties": {
      "status": "ACTIVE",
      "source_document_ids": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
      "confidence": 0.95
    },
    "in_degree": 2,
    "out_degree": 3,
    "created_at": "2026-10-27T12:00:00Z"
  }
}
```

#### 11.2.4 View Entity Relationships
- **Method**: `GET`
- **Path**: `/api/v1/graph/relationships/{id}`
- **Auth**: Bearer JWT (`graph.read` permission)
- **Path Parameters**:
  - `id`: UUID (Entity ID)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "entity_id": "e_1",
    "outgoing_relationships": [
      {
        "relationship_id": "r_1",
        "target_entity_id": "e_3",
        "target_entity_name": "Engineering",
        "target_entity_type": "DEPARTMENT",
        "relation_type": "APPLIES_TO",
        "weight": 1.0
      }
    ],
    "incoming_relationships": [
      {
        "relationship_id": "r_2",
        "source_entity_id": "e_2",
        "source_entity_name": "Alice",
        "source_entity_type": "EMPLOYEE",
        "relation_type": "LEADS",
        "weight": 0.95
      }
    ]
  }
}
```

#### 11.2.5 Execute Multi-Hop Graph Query
- **Method**: `POST`
- **Path**: `/api/v1/graph/query`
- **Auth**: Bearer JWT (`graph.read` permission)
- **Request Body**:
```json
{
  "start_entity_id": "e_1",
  "max_depth": 2,
  "allowed_relation_types": ["APPLIES_TO", "LEADS", "WORKS_IN"],
  "allowed_entity_types": ["EMPLOYEE", "DEPARTMENT", "PROJECT"]
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "nodes": [
      {"id": "e_1", "name": "AI Migration Project", "entity_type": "PROJECT", "depth": 0},
      {"id": "e_3", "name": "Engineering", "entity_type": "DEPARTMENT", "depth": 1},
      {"id": "e_2", "name": "Alice", "entity_type": "EMPLOYEE", "depth": 1}
    ],
    "edges": [
      {"source": "e_1", "target": "e_3", "relation_type": "APPLIES_TO", "weight": 1.0},
      {"source": "e_2", "target": "e_1", "relation_type": "LEADS", "weight": 0.95}
    ],
    "total_paths": 2,
    "max_depth_reached": 1
  }
}
```

#### 11.2.6 Knowledge Explorer Visualization Data
- **Method**: `GET`
- **Path**: `/api/v1/graph/explorer`
- **Auth**: Bearer JWT (`graph.read` permission)
- **Query Parameters**:
  - `entity_type` (optional, string): Filter nodes by type
  - `limit` (optional, int, default 100)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "nodes": [
      {"id": "e_1", "label": "AI Migration Project", "type": "PROJECT", "val": 15},
      {"id": "e_2", "label": "Alice", "type": "EMPLOYEE", "val": 25},
      {"id": "e_3", "label": "Engineering", "type": "DEPARTMENT", "val": 40}
    ],
    "links": [
      {"source": "e_1", "target": "e_3", "label": "APPLIES_TO", "weight": 1.0},
      {"source": "e_2", "target": "e_1", "label": "LEADS", "weight": 0.95}
    ],
    "metrics": {
      "total_entities": 45,
      "total_relationships": 72,
      "density": 0.036,
      "top_hub": "Engineering"
    }
  }
}
```

#### 11.2.7 Subject-Matter Expertise Discovery
- **Method**: `GET`
- **Path**: `/api/v1/graph/expertise`
- **Auth**: Bearer JWT (`graph.intelligence` permission)
- **Query Parameters**:
  - `topic`: string (e.g. "Cybersecurity", "Cloud Architecture")
  - `limit`: int (optional, default 5)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "topic": "Cybersecurity",
    "experts": [
      {
        "user_id": "u_1",
        "full_name": "Alice Alpha",
        "department": "Engineering",
        "score": 8.5,
        "authored_documents_count": 3,
        "contributed_projects": ["Security Audit", "Key Rotation"],
        "evidence_citations": ["Information Security Guidelines v2.0"]
      }
    ]
  }
}
```

#### 11.2.8 Recursive Impact Analysis
- **Method**: `GET`
- **Path**: `/api/v1/graph/impact/{entity_id}`
- **Auth**: Bearer JWT (`graph.intelligence` permission)
- **Path Parameters**:
  - `entity_id`: UUID
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "root_entity": {
      "id": "e_policy_1",
      "name": "Access Control Standard 2026",
      "entity_type": "POLICY"
    },
    "affected_departments": ["Engineering", "Operations"],
    "dependent_projects": ["AI Migration Project"],
    "impacted_tasks_count": 8,
    "severity_score": 0.85,
    "dependency_tree": [
      {
        "id": "e_proj_1",
        "name": "AI Migration Project",
        "entity_type": "PROJECT",
        "depth": 1,
        "relation": "GOVERNED_BY"
      }
    ]
  }
}
```

---

## 12. Enterprise Intelligence & Predictive Analytics Endpoints (Phase 2.5)

### 12.1 Overview & Base URI
All intelligence and predictive analytics endpoints are mounted at `/api/v1/analytics` with organization-scoped multi-tenant isolation and role-based access control.

### 12.2 Endpoints Specification

#### 12.2.1 Executive Intelligence Dashboard
- **Method**: `GET`
- **Path**: `/api/v1/analytics/dashboard`
- **Auth**: Bearer JWT (`analytics.view` permission)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Executive dashboard retrieved successfully.",
  "data": {
    "health_score": {
      "overall_score": 88,
      "rating": "EXCELLENT",
      "coverage_score": 92.0,
      "freshness_score": 84.0,
      "quality_score": 86.0,
      "retrieval_score": 90.0,
      "duplicate_penalty": 4.0
    },
    "kpis": {
      "active_users": 42,
      "documents_uploaded": 128,
      "ai_queries": 450,
      "search_success_rate": 0.94,
      "avg_response_time_ms": 185.0,
      "storage_used_bytes": 1073741824,
      "storage_capacity_bytes": 10737418240
    },
    "active_anomalies_count": 1,
    "top_recommendations_count": 3,
    "executive_summary": "Knowledge contributions increased by 18% this month with strong AI adoption (26% growth). Storage runway is projected at 142 days."
  }
}
```

#### 12.2.2 Core Operational KPIs
- **Method**: `GET`
- **Path**: `/api/v1/analytics/kpis`
- **Auth**: Bearer JWT (`analytics.view` permission)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "KPI metrics retrieved successfully.",
  "data": {
    "active_users": 42,
    "documents_uploaded": 128,
    "ai_queries": 450,
    "search_success_rate": 0.94,
    "avg_response_time_ms": 185.0,
    "storage_used_bytes": 1073741824,
    "storage_capacity_bytes": 10737418240,
    "knowledge_health_score": 88
  }
}
```

#### 12.2.3 Trend Analysis
- **Method**: `GET`
- **Path**: `/api/v1/analytics/trends`
- **Auth**: Bearer JWT (`analytics.view` permission)
- **Query Parameters**:
  - `metric`: string (e.g. `documents`, `ai_usage`, `storage`, `collaboration`, default: `all`)
  - `days`: int (e.g. 30, 60, 90, default: 30)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Trend analysis retrieved successfully.",
  "data": {
    "period_days": 30,
    "document_growth": [
      { "date": "2026-10-01", "value": 110 },
      { "date": "2026-10-15", "value": 120 },
      { "date": "2026-10-28", "value": 128 }
    ],
    "ai_query_volume": [
      { "date": "2026-10-01", "value": 310 },
      { "date": "2026-10-15", "value": 390 },
      { "date": "2026-10-28", "value": 450 }
    ],
    "department_activity": [
      { "department": "Platform Engineering", "document_count": 64, "query_count": 210 },
      { "department": "Product Management", "document_count": 32, "query_count": 140 }
    ]
  }
}
```

#### 12.2.4 Predictive Analytics & Forecasting
- **Method**: `GET`
- **Path**: `/api/v1/analytics/predictions`
- **Auth**: Bearer JWT (`analytics.view` permission)
- **Query Parameters**:
  - `horizon_days`: int (default: 30)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Predictions generated successfully.",
  "data": {
    "horizon_days": 30,
    "document_forecast": {
      "current_value": 128,
      "projected_value": 164,
      "growth_rate_pct": 28.1,
      "confidence_lower": 152,
      "confidence_upper": 176
    },
    "storage_runway": {
      "current_usage_bytes": 1073741824,
      "capacity_bytes": 10737418240,
      "days_to_85_pct": 142,
      "days_to_full": 185,
      "is_critical": false
    },
    "query_volume_forecast": {
      "current_daily_avg": 45.0,
      "projected_daily_avg": 58.5,
      "monthly_tokens_projected": 2400000
    }
  }
}
```

#### 12.2.5 Operational Anomaly Detection
- **Method**: `GET`
- **Path**: `/api/v1/analytics/anomalies`
- **Auth**: Bearer JWT (`analytics.view` permission)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Anomalies retrieved successfully.",
  "data": {
    "total_detected": 1,
    "anomalies": [
      {
        "id": "anom-001",
        "metric_name": "cross_department_collaboration",
        "anomaly_type": "ACTIVITY_DROP",
        "severity": "MEDIUM",
        "description": "Cross-team document sharing dropped 42% below 30-day baseline.",
        "deviation_score": 2.35,
        "detected_at": "2026-10-27T14:00:00Z"
      }
    ]
  }
}
```

#### 12.2.6 Strategic Recommendations
- **Method**: `GET`
- **Path**: `/api/v1/analytics/recommendations`
- **Auth**: Bearer JWT (`analytics.view` permission)
- **Query Parameters**:
  - `status`: string (`ACTIVE`, `APPLIED`, `DISMISSED`, default: `ACTIVE`)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Recommendations retrieved successfully.",
  "data": {
    "total_recommendations": 2,
    "recommendations": [
      {
        "id": "rec-001",
        "category": "ARCHIVE",
        "title": "Archive 14 Stale Operational Manuals",
        "description": "Documents have not been viewed, cited, or updated in >180 days.",
        "impact_score": 7.5,
        "effort_score": 1.5,
        "priority_index": 7.5,
        "status": "ACTIVE",
        "action_payload": { "doc_ids": ["doc-1", "doc-2"] }
      },
      {
        "id": "rec-002",
        "category": "COVERAGE",
        "title": "Document Human Resources SOPs",
        "description": "HR department has 0 indexed operational documents in knowledge base.",
        "impact_score": 8.0,
        "effort_score": 3.0,
        "priority_index": 4.0,
        "status": "ACTIVE",
        "action_payload": { "department": "Human Resources" }
      }
    ]
  }
}
```

#### 12.2.7 Multi-Dimensional Knowledge Health Score
- **Method**: `GET`
- **Path**: `/api/v1/analytics/knowledge-health`
- **Auth**: Bearer JWT (`analytics.view` permission)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Knowledge health score computed successfully.",
  "data": {
    "overall_score": 88,
    "rating": "EXCELLENT",
    "coverage_score": 92.0,
    "freshness_score": 84.0,
    "quality_score": 86.0,
    "retrieval_score": 90.0,
    "duplicate_penalty": 4.0,
    "department_breakdown": [
      { "department": "Platform Engineering", "score": 94, "rating": "EXCELLENT" },
      { "department": "Operations", "score": 72, "rating": "GOOD" }
    ],
    "identified_gaps": [
      "Human Resources has no active policy documentation.",
      "Legal contracts require freshness review (>120 days old)."
    ]
  }
}
```

---

## 13. Enterprise Integrations & Connector Framework (Phase 3.1)

### 13.1 Overview
The Connector Framework enables seamless, secure ingestion from external enterprise platforms into KEEP's unified RAG and Knowledge Graph pipelines.
All endpoints require Bearer JWT authentication and tenant isolation (`organization_id`).

### 13.2 Endpoints

#### 13.2.1 POST /api/v1/connectors/register
**Purpose**: Register a new enterprise connector configuration.  
**Permissions**: `connector.manage` or `admin.write` (SuperAdmin, OrgAdmin).  
**Request Body**:
```json
{
  "name": "Corporate Google Drive",
  "platform_type": "GOOGLE_DRIVE",
  "platform_category": "CLOUD_STORAGE",
  "auth_type": "OAUTH2",
  "config": {
    "sync_interval_minutes": 60,
    "sync_folders": ["root", "Engineering Docs"],
    "file_extensions": [".pdf", ".docx", ".gdoc", ".txt"]
  }
}
```
**Response (201 Created)**:
```json
{
  "success": true,
  "message": "Connector registered successfully.",
  "data": {
    "id": "c7a8b9c0-d1e2-3f4a-5b6c-7d8e9f0a1b2c",
    "name": "Corporate Google Drive",
    "platform_type": "GOOGLE_DRIVE",
    "platform_category": "CLOUD_STORAGE",
    "auth_type": "OAUTH2",
    "status": "CONFIGURED",
    "config": {
      "sync_interval_minutes": 60,
      "sync_folders": ["root", "Engineering Docs"],
      "file_extensions": [".pdf", ".docx", ".gdoc", ".txt"]
    },
    "total_documents_synced": 0,
    "created_at": "2026-10-28T02:00:00Z"
  }
}
```

#### 13.2.2 POST /api/v1/connectors/authenticate
**Purpose**: Provide credentials or initiate OAuth authentication handshake for a registered connector.  
**Permissions**: `connector.manage` or `admin.write`.  
**Request Body**:
```json
{
  "connector_id": "c7a8b9c0-d1e2-3f4a-5b6c-7d8e9f0a1b2c",
  "auth_type": "OAUTH2",
  "credentials": {
    "access_token": "ya29.a0AfH6SMB...",
    "refresh_token": "1//04...",
    "expires_in": 3600
  }
}
```
**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Connector authenticated successfully.",
  "data": {
    "connector_id": "c7a8b9c0-d1e2-3f4a-5b6c-7d8e9f0a1b2c",
    "status": "CONNECTED",
    "authenticated_at": "2026-10-28T02:00:00Z"
  }
}
```

#### 13.2.3 GET /api/v1/connectors/list
**Purpose**: List all configured connectors for the authenticated tenant.  
**Permissions**: `connector.view` or `admin.read`.  
**Query Parameters**:
- `platform_category`: (Optional) Filter by category.
- `status`: (Optional) Filter by connector status.
**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Connectors retrieved successfully.",
  "data": {
    "total_connectors": 3,
    "connectors": [
      {
        "id": "c7a8b9c0-d1e2-3f4a-5b6c-7d8e9f0a1b2c",
        "name": "Corporate Google Drive",
        "platform_type": "GOOGLE_DRIVE",
        "platform_category": "CLOUD_STORAGE",
        "auth_type": "OAUTH2",
        "status": "HEALTHY",
        "total_documents_synced": 342,
        "last_sync_at": "2026-10-28T01:30:00Z",
        "last_sync_status": "COMPLETED",
        "created_at": "2026-10-28T00:00:00Z"
      }
    ]
  }
}
```

#### 13.2.4 POST /api/v1/connectors/sync
**Purpose**: Trigger a manual or scheduled synchronization run.  
**Permissions**: `connector.manage` or `admin.write`.  
**Request Body**:
```json
{
  "connector_id": "c7a8b9c0-d1e2-3f4a-5b6c-7d8e9f0a1b2c",
  "sync_mode": "INCREMENTAL"
}
```
**Response (202 Accepted)**:
```json
{
  "success": true,
  "message": "Synchronization job started successfully.",
  "data": {
    "sync_job_id": "j1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "connector_id": "c7a8b9c0-d1e2-3f4a-5b6c-7d8e9f0a1b2c",
    "sync_mode": "INCREMENTAL",
    "status": "RUNNING",
    "started_at": "2026-10-28T02:01:00Z"
  }
}
```

#### 13.2.5 GET /api/v1/connectors/status/{id}
**Purpose**: Retrieve real-time operational status, health indicators, and sync statistics for a specific connector.  
**Permissions**: `connector.view`.  
**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Connector status retrieved successfully.",
  "data": {
    "id": "c7a8b9c0-d1e2-3f4a-5b6c-7d8e9f0a1b2c",
    "name": "Corporate Google Drive",
    "platform_type": "GOOGLE_DRIVE",
    "status": "HEALTHY",
    "last_sync_at": "2026-10-28T01:30:00Z",
    "last_sync_status": "COMPLETED",
    "total_documents_synced": 342,
    "active_sync_job": null,
    "health_metrics": {
      "api_latency_ms": 142.5,
      "quota_used_pct": 28.4,
      "success_rate_pct": 98.7
    }
  }
}
```

#### 13.2.6 DELETE /api/v1/connectors/remove/{id}
**Purpose**: Safely deregister and remove a connector instance.  
**Permissions**: `connector.manage` or `admin.write`.  
**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Connector removed successfully.",
  "data": {
    "id": "c7a8b9c0-d1e2-3f4a-5b6c-7d8e9f0a1b2c",
    "name": "Corporate Google Drive",
    "status": "DISCONNECTED"
  }
}
```

#### 13.2.7 GET /api/v1/connectors/logs
**Purpose**: Query synchronization execution history, resource delta logs, and error traces.  
**Permissions**: `connector.view`.  
**Query Parameters**:
- `connector_id`: (Optional) Filter by connector.
- `limit`: (Optional, default: 50, max: 200).
- `status`: (Optional: SUCCESS, WARNING, FAILURE).
**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Connector logs retrieved successfully.",
  "data": {
    "total_logs": 2,
    "logs": [
      {
        "id": "l9a8b7c6-d5e4-3f2a-1b0c-9d8e7f6a5b4c",
        "connector_id": "c7a8b9c0-d1e2-3f4a-5b6c-7d8e9f0a1b2c",
        "sync_job_id": "j1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
        "external_document_id": "doc-991",
        "document_title": "Q3 Engineering Roadmap",
        "source_url": "https://docs.google.com/document/d/doc-991",
        "action_taken": "UPDATED",
        "status": "SUCCESS",
        "checksum": "a8f3b2c1d0e9f8a7...",
        "created_at": "2026-10-28T01:30:15Z"
      }
    ]
  }
}
```

---

## 14. Real-Time Collaboration, Team Workspaces & Knowledge Sharing (Phase 3.2)

### 14.1 Workspace Management

#### 14.1.1 Create Team Workspace
- **Method**: `POST`
- **Path**: `/api/v1/workspaces/create`
- **Auth**: Bearer JWT (`workspace.manage` or `workspace.create`)
- **Request Body**:
```json
{
  "name": "Engineering Core",
  "slug": "engineering-core",
  "description": "Core engineering workspace for architecture, RFCs, and guidelines",
  "avatar_color": "#4F46E5",
  "is_private": false
}
```
- **Response (201 Created)**:
```json
{
  "success": true,
  "message": "Workspace created successfully.",
  "data": {
    "id": "w1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "name": "Engineering Core",
    "slug": "engineering-core",
    "description": "Core engineering workspace for architecture, RFCs, and guidelines",
    "avatar_color": "#4F46E5",
    "is_private": false,
    "member_count": 1,
    "created_at": "2026-10-28T09:00:00Z"
  }
}
```

#### 14.1.2 Retrieve Workspace by ID
- **Method**: `GET`
- **Path**: `/api/v1/workspaces/{id}`
- **Auth**: Bearer JWT (`workspace.view`)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": "w1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "name": "Engineering Core",
    "slug": "engineering-core",
    "description": "Core engineering workspace for architecture, RFCs, and guidelines",
    "avatar_color": "#4F46E5",
    "is_private": false,
    "current_user_role": "ADMIN",
    "members": [
      {
        "user_id": "u1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
        "email": "lead@company.com",
        "full_name": "Tech Lead",
        "role": "ADMIN",
        "joined_at": "2026-10-28T09:00:00Z"
      }
    ],
    "created_at": "2026-10-28T09:00:00Z"
  }
}
```

#### 14.1.3 List Workspaces
- **Method**: `GET`
- **Path**: `/api/v1/workspaces/list`
- **Auth**: Bearer JWT
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "total": 3,
    "workspaces": [
      {
        "id": "w1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
        "name": "Engineering Core",
        "slug": "engineering-core",
        "description": "Core engineering workspace",
        "avatar_color": "#4F46E5",
        "member_count": 12,
        "current_user_role": "ADMIN",
        "created_at": "2026-10-28T09:00:00Z"
      }
    ]
  }
}
```

#### 14.1.4 Workspace Collaboration Dashboard
- **Method**: `GET`
- **Path**: `/api/v1/workspaces/{id}/dashboard`
- **Auth**: Bearer JWT (`workspace.view`)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "workspace_id": "w1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "active_members_count": 8,
    "active_projects_count": 4,
    "recent_documents_count": 15,
    "open_discussions_count": 6,
    "pending_approvals_count": 2,
    "recent_activities": [],
    "recent_discussions": []
  }
}
```

---

### 14.2 Shared Projects

#### 14.2.1 Create Shared Project
- **Method**: `POST`
- **Path**: `/api/v1/projects/create`
- **Auth**: Bearer JWT (`workspace.manage` or `workspace.create`)
- **Request Body**:
```json
{
  "workspace_id": "w1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
  "name": "API v2 Redesign",
  "description": "Cross-team project migrating public APIs to OpenAPI 3.1 specification"
}
```
- **Response (201 Created)**:
```json
{
  "success": true,
  "message": "Project created successfully.",
  "data": {
    "id": "p1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "workspace_id": "w1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "name": "API v2 Redesign",
    "description": "Cross-team project migrating public APIs to OpenAPI 3.1 specification",
    "created_at": "2026-10-28T09:10:00Z"
  }
}
```

---

### 14.3 Document Discussions, Comments & Mentions

#### 14.3.1 Add Comment
- **Method**: `POST`
- **Path**: `/api/v1/comments/create`
- **Auth**: Bearer JWT (`comment.create`)
- **Request Body**:
```json
{
  "document_id": "d1a2b3c4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "workspace_id": "w1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
  "content": "Please verify section 3.2 with @Sarah before the audit.",
  "page_number": 3,
  "highlight_text": "Retention period shall not exceed 90 days."
}
```
- **Response (201 Created)**:
```json
{
  "success": true,
  "message": "Comment posted successfully.",
  "data": {
    "id": "c1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "document_id": "d1a2b3c4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "author_id": "u1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "author_name": "John Doe",
    "content": "Please verify section 3.2 with @Sarah before the audit.",
    "page_number": 3,
    "highlight_text": "Retention period shall not exceed 90 days.",
    "parent_comment_id": null,
    "status": "OPEN",
    "mentions": ["Sarah"],
    "created_at": "2026-10-28T09:12:00Z"
  }
}
```

#### 14.3.2 Reply to Comment
- **Method**: `POST`
- **Path**: `/api/v1/comments/reply`
- **Auth**: Bearer JWT (`comment.create`)
- **Request Body**:
```json
{
  "parent_comment_id": "c1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
  "content": "Verified and approved per compliance standards."
}
```
- **Response (201 Created)**:
```json
{
  "success": true,
  "message": "Reply posted successfully.",
  "data": {
    "id": "c2b3c4d5-e6f7-8a9b-0c1d-2e3f4a5b6c7d",
    "parent_comment_id": "c1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "document_id": "d1a2b3c4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "author_name": "Sarah Connor",
    "content": "Verified and approved per compliance standards.",
    "status": "OPEN",
    "created_at": "2026-10-28T09:15:00Z"
  }
}
```

#### 14.3.3 Resolve Comment Thread
- **Method**: `POST`
- **Path**: `/api/v1/comments/{id}/resolve`
- **Auth**: Bearer JWT (`comment.resolve`)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Discussion thread resolved successfully.",
  "data": {
    "id": "c1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "status": "RESOLVED",
    "resolved_by_id": "u1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "resolved_at": "2026-10-28T09:20:00Z"
  }
}
```

#### 14.3.4 Send Explicit User Mention
- **Method**: `POST`
- **Path**: `/api/v1/mentions/send`
- **Auth**: Bearer JWT (`comment.create`)
- **Request Body**:
```json
{
  "mentioned_user_id": "u2b3c4d5-e6f7-8a9b-0c1d-2e3f4a5b6c7d",
  "document_id": "d1a2b3c4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "workspace_id": "w1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
  "context_text": "@Sarah Please review the updated HR policy."
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Mention notification dispatched successfully.",
  "data": {
    "notification_id": "n1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "delivered": true
  }
}
```

---

### 14.4 Activity Feed & Document Version History

#### 14.4.1 Workspace Activity Feed
- **Method**: `GET`
- **Path**: `/api/v1/activity/feed`
- **Auth**: Bearer JWT (`workspace.view`)
- **Query Parameters**:
  - `workspace_id`: (Required, UUID)
  - `activity_type`: (Optional, string)
  - `limit`: (Optional, default: 30)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "workspace_id": "w1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "activities": [
      {
        "id": "a1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
        "activity_type": "COMMENT_ADDED",
        "actor_name": "Bob Smith",
        "entity_id": "d1a2b3c4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
        "entity_type": "document",
        "entity_title": "Employee Handbook.pdf",
        "description": "Bob commented on Employee Handbook.pdf",
        "created_at": "2026-10-28T10:18:00Z"
      }
    ]
  }
}
```

#### 14.4.2 Document Version History
- **Method**: `GET`
- **Path**: `/api/v1/version/history/{id}`
- **Auth**: Bearer JWT (`document.view`)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "document_id": "d1a2b3c4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "total_versions": 2,
    "versions": [
      {
        "version_id": "v2a3b4c5-d6e7-8a9b-0c1d-2e3f4a5b6c7d",
        "version_number": 2,
        "editor_name": "Alice Green",
        "change_summary": "Updated annual leave allocation from 18 to 20 days",
        "approval_status": "APPROVED",
        "created_at": "2026-10-28T10:25:00Z"
      },
      {
        "version_id": "v1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
        "version_number": 1,
        "editor_name": "Alice Green",
        "change_summary": "Initial handbook draft",
        "approval_status": "APPROVED",
        "created_at": "2026-10-28T10:00:00Z"
      }
    ]
  }
}
```

---

### 14.5 AI Collaboration Assistant

#### 14.5.1 Summarize Discussion Thread
- **Method**: `POST`
- **Path**: `/api/v1/collaboration/discussions/{document_id}/summary`
- **Auth**: Bearer JWT (`workspace.view`)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "document_id": "d1a2b3c4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "executive_summary": "The discussion centered on HR leave policy harmonization. Sarah and John finalized that annual leave increases to 20 days with supervisor sign-off.",
    "key_decisions": [
      {
        "decision": "Annual leave allocation confirmed at 20 days per fiscal year",
        "agreed_by": ["Sarah Connor", "John Doe"],
        "timestamp": "2026-10-28T09:20:00Z"
      }
    ],
    "action_items": [
      {
        "assignee": "Sarah Connor",
        "action": "Publish revised employee handbook PDF to the HR portal",
        "deadline": "Friday"
      }
    ],
    "suggested_documents": [
      {
        "document_id": "d9e8f7a6-b5c4-3d2e-1f0a-9b8c7d6e5f4a",
        "title": "Corporate Compliance Handbook 2026",
        "relevance_score": 0.92
      }
    ]
  }
}
```

---

## 15. Phase 3.3 — Enterprise Security, Compliance, Governance & Data Protection API Contract

### 15.1 Enterprise Authentication & Session Management

#### 15.1.1 Enterprise User Login & SSO Handshake
- **Method**: `POST`
- **Path**: `/api/v1/security/login`
- **Auth**: None (Public)
- **Request Body**:
```json
{
  "email": "security_admin@enterprise.com",
  "password": "Password123!",
  "provider": "local",
  "sso_token": null
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Authentication successful.",
  "data": {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user_id": "u1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "organization_id": "o1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "role": "OrgAdmin",
    "mfa_required": false,
    "mfa_verified": true
  }
}
```

#### 15.1.2 Enterprise Session Logout
- **Method**: `POST`
- **Path**: `/api/v1/security/logout`
- **Auth**: Bearer JWT
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Session invalidated successfully."
}
```

---

### 15.2 Multi-Factor Authentication (MFA / TOTP)

#### 15.2.1 Setup MFA / Generate TOTP Secret
- **Method**: `POST`
- **Path**: `/api/v1/security/mfa/setup`
- **Auth**: Bearer JWT
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "secret_key": "JBSWY3DPEHPK3PXP",
    "otpauth_uri": "otpauth://totp/KEEP:user@company.com?secret=JBSWY3DPEHPK3PXP&issuer=KEEP",
    "backup_codes": ["a1b2c3d4", "e5f6g7h8", "i9j0k1l2", "m3n4o5p6"]
  }
}
```

#### 15.2.2 Verify MFA Code
- **Method**: `POST`
- **Path**: `/api/v1/security/mfa/verify`
- **Auth**: Bearer JWT
- **Request Body**:
```json
{
  "code": "123456"
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Multi-factor authentication verified.",
  "data": {
    "is_enabled": true,
    "mfa_verified": true
  }
}
```

#### 15.2.3 Disable MFA
- **Method**: `POST`
- **Path**: `/api/v1/security/mfa/disable`
- **Auth**: Bearer JWT
- **Request Body**:
```json
{
  "code": "123456"
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "MFA disabled successfully."
}
```

---

### 15.3 Enterprise Audit Trails

#### 15.3.1 Retrieve Security Audit Trail
- **Method**: `GET`
- **Path**: `/api/v1/security/audit`
- **Auth**: Bearer JWT (`audit.read` or `security.view`)
- **Query Parameters**:
  - `action`: string (optional filter)
  - `status`: string (optional filter: `SUCCESS`, `FAILURE`, `DENIED`)
  - `page`: int (default: 1)
  - `page_size`: int (default: 50)
- **Response (200 OK)**:
```json
{
  "success": true,
  "total": 120,
  "page": 1,
  "page_size": 50,
  "data": [
    {
      "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "organization_id": "o1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
      "user_id": "u1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
      "action": "DOCUMENT_ACCESS",
      "resource": "document",
      "resource_id": "d1a2b3c4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 ...",
      "status": "SUCCESS",
      "details": { "classification": "CONFIDENTIAL" },
      "created_at": "2026-10-28T10:15:00Z"
    }
  ]
}
```

---

### 15.4 Roles & Permissions Management

#### 15.4.1 List Defined Roles & Permission Matrix
- **Method**: `GET`
- **Path**: `/api/v1/security/roles`
- **Auth**: Bearer JWT
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "role": "Super Admin",
      "description": "Full platform administration across all tenants",
      "permissions": ["*"]
    },
    {
      "role": "Organization Admin",
      "description": "Tenant governance, policy enforcement and audit inspection",
      "permissions": ["audit.read", "security.manage", "user.manage", "workspace.manage"]
    },
    {
      "role": "Department Manager",
      "description": "Departmental asset administration",
      "permissions": ["workspace.manage", "document.read", "document.write"]
    },
    {
      "role": "Employee",
      "description": "Standard organization member access",
      "permissions": ["workspace.view", "document.read", "comment.create"]
    },
    {
      "role": "Viewer",
      "description": "Read-only access with export restrictions",
      "permissions": ["workspace.view", "document.read"]
    }
  ]
}
```

#### 15.4.2 Update Role Permissions
- **Method**: `POST`
- **Path**: `/api/v1/security/permissions`
- **Auth**: Bearer JWT (`security.manage`)
- **Request Body**:
```json
{
  "role": "Employee",
  "permissions": ["workspace.view", "document.read", "comment.create", "ai.chat"]
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Permissions updated successfully."
}
```

---

### 15.5 Sensitive Data Classification & PII Scanner

#### 15.5.1 Scan Text or Document for Sensitive Data / PII
- **Method**: `POST`
- **Path**: `/api/v1/security/data-classification/scan`
- **Auth**: Bearer JWT
- **Request Body**:
```json
{
  "document_id": "d1a2b3c4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "content": "Contact John Doe at john.doe@enterprise.com, SSN 000-12-3456, key sk-abc1234567890."
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "document_id": "d1a2b3c4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "classification_level": "RESTRICTED",
    "detected_pii_entities": [
      { "type": "EMAIL", "count": 1, "masked_sample": "j***e@enterprise.com" },
      { "type": "SSN", "count": 1, "masked_sample": "***-**-3456" },
      { "type": "API_KEY", "count": 1, "masked_sample": "sk-***" }
    ],
    "pii_count": 3,
    "confidence_score": 0.98,
    "redacted_preview": "Contact John Doe at [REDACTED_EMAIL], SSN [REDACTED_SSN], key [REDACTED_API_KEY]."
  }
}
```

#### 15.5.2 Get Document Classification Status
- **Method**: `GET`
- **Path**: `/api/v1/security/data-classification/{document_id}`
- **Auth**: Bearer JWT
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "document_id": "d1a2b3c4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "classification_level": "RESTRICTED",
    "pii_count": 3,
    "confidence_score": 0.98,
    "scanned_at": "2026-10-28T10:20:00Z"
  }
}
```

---

### 15.6 AI Governance & Safety Guardrails

#### 15.6.1 Query AI Governance Logs
- **Method**: `GET`
- **Path**: `/api/v1/security/ai-governance/logs`
- **Auth**: Bearer JWT (`security.view`)
- **Query Parameters**:
  - `page`: int (default: 1)
  - `page_size`: int (default: 20)
- **Response (200 OK)**:
```json
{
  "success": true,
  "total": 45,
  "data": [
    {
      "id": "g1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
      "user_id": "u1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
      "prompt_snippet": "Summarize Q3 financial revenue report",
      "model_name": "gpt-4o-mini",
      "guardrail_status": "PASSED",
      "token_usage": 320,
      "latency_ms": 142.5,
      "created_at": "2026-10-28T10:30:00Z"
    }
  ]
}
```

#### 15.6.2 AI Governance Safety Telemetry
- **Method**: `GET`
- **Path**: `/api/v1/security/ai-governance/stats`
- **Auth**: Bearer JWT
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "total_queries_audited": 1420,
    "guardrail_blocks": 3,
    "avg_latency_ms": 154.2,
    "prompt_injection_attempts": 2,
    "safety_score_percentage": 99.8
  }
}
```

---

### 15.7 Enterprise Compliance Framework

#### 15.7.1 Multi-Standard Compliance Status & Scores
- **Method**: `GET`
- **Path**: `/api/v1/security/compliance`
- **Auth**: Bearer JWT (`security.compliance` or `security.view`)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "overall_compliance_score": 94,
    "standards": [
      {
        "standard": "GDPR",
        "score": 96,
        "status": "COMPLIANT",
        "controls_passed": 12,
        "controls_total": 12
      },
      {
        "standard": "ISO_27001",
        "score": 92,
        "status": "COMPLIANT",
        "controls_passed": 18,
        "controls_total": 20
      },
      {
        "standard": "SOC_2",
        "score": 95,
        "status": "COMPLIANT",
        "controls_passed": 15,
        "controls_total": 16
      },
      {
        "standard": "HIPAA",
        "score": 93,
        "status": "COMPLIANT",
        "controls_passed": 14,
        "controls_total": 15
      }
    ]
  }
}
```

#### 15.7.2 Configure Data Retention Rules
- **Method**: `POST`
- **Path**: `/api/v1/security/compliance/retention-policies`
- **Auth**: Bearer JWT (`security.manage`)
- **Request Body**:
```json
{
  "resource_type": "audit_logs",
  "retention_days": 365,
  "action_on_expiry": "ARCHIVE"
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Data retention policy updated."
}
```

#### 15.7.3 Execute GDPR Article 17 Erasure Request
- **Method**: `POST`
- **Path**: `/api/v1/security/compliance/gdpr-erasure`
- **Auth**: Bearer JWT (`security.manage`)
- **Request Body**:
```json
{
  "target_user_id": "u1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
  "reason": "Employee departure right to erasure request"
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "User data anonymized and erased in accordance with GDPR Article 17.",
  "data": {
    "erasure_id": "e1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "completed_at": "2026-10-28T10:40:00Z"
  }
}
```

---

### 15.8 Security Monitoring & Anomaly Alerts

#### 15.8.1 Query Security Threat Alerts
- **Method**: `GET`
- **Path**: `/api/v1/security/monitoring/alerts`
- **Auth**: Bearer JWT
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "id": "t1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
      "alert_type": "FAILED_LOGIN_SPIKE",
      "severity": "HIGH",
      "description": "5 consecutive failed logins detected for user admin@enterprise.com",
      "source_ip": "203.0.113.195",
      "resolved": false,
      "triggered_at": "2026-10-28T10:35:00Z"
    }
  ]
}
```

---

## 16. Workflow Automation, Notifications & Event-Driven Intelligence (Phase 3.4)

### 16.1 Overview
The Phase 3.4 Workflow Automation API enables enterprise organizations to orchestrate multi-step autonomous workflows, manage human-in-the-loop approvals, dispatch contextual notifications across in-app/email/Slack/Teams channels, and analyze operational automation performance.

Base Path: `/api/v1`

---

### 16.2 Workflow Management

#### 16.2.1 Create Workflow
- **Method**: `POST`
- **Path**: `/api/v1/workflows/create`
- **Auth**: Bearer JWT (`workflow.manage` permission)
- **Request Body**:
```json
{
  "name": "Confidential Policy Ingestion & Review",
  "description": "Automatically summarize uploaded policies, scan for PII, and notify legal reviewer.",
  "trigger_type": "EVENT",
  "event_pattern": "document.uploaded",
  "condition_rules": {
    "field": "document_type",
    "operator": "equals",
    "value": "POLICY"
  },
  "is_active": true,
  "steps": [
    {
      "step_order": 1,
      "action_type": "AI_SUMMARIZE",
      "configuration": { "max_summary_length": 250 }
    },
    {
      "step_order": 2,
      "action_type": "AI_SUGGEST_REVIEWER",
      "configuration": { "target_role": "LegalReviewer" }
    },
    {
      "step_order": 3,
      "action_type": "REQUIRE_APPROVAL",
      "configuration": { "approver_role": "LegalManager" }
    },
    {
      "step_order": 4,
      "action_type": "NOTIFY",
      "configuration": { "channel": "IN_APP", "priority": "HIGH" }
    }
  ]
}
```
- **Response (201 Created)**:
```json
{
  "success": true,
  "message": "Workflow created successfully.",
  "data": {
    "id": "wf-1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "name": "Confidential Policy Ingestion & Review",
    "trigger_type": "EVENT",
    "event_pattern": "document.uploaded",
    "is_active": true,
    "step_count": 4,
    "created_at": "2026-10-29T10:00:00Z"
  }
}
```

#### 16.2.2 List Workflows
- **Method**: `GET`
- **Path**: `/api/v1/workflows/list`
- **Auth**: Bearer JWT (`workflow.view` permission)
- **Query Parameters**:
  - `is_active`: boolean (optional)
  - `trigger_type`: string (optional: `EVENT`, `SCHEDULE`, `MANUAL`)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "id": "wf-1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
      "name": "Confidential Policy Ingestion & Review",
      "description": "Automatically summarize uploaded policies, scan for PII, and notify legal reviewer.",
      "trigger_type": "EVENT",
      "event_pattern": "document.uploaded",
      "is_active": true,
      "step_count": 4,
      "created_at": "2026-10-29T10:00:00Z"
    }
  ]
}
```

#### 16.2.3 Get Workflow Status & Details
- **Method**: `GET`
- **Path**: `/api/v1/workflows/status/{id}`
- **Auth**: Bearer JWT (`workflow.view` permission)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "workflow": {
      "id": "wf-1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
      "name": "Confidential Policy Ingestion & Review",
      "trigger_type": "EVENT",
      "is_active": true
    },
    "recent_executions": [
      {
        "id": "exec-1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
        "status": "COMPLETED",
        "duration_ms": 420,
        "started_at": "2026-10-29T10:05:00Z",
        "completed_at": "2026-10-29T10:05:01Z"
      }
    ]
  }
}
```

#### 16.2.4 Execute Workflow
- **Method**: `POST`
- **Path**: `/api/v1/workflows/execute`
- **Auth**: Bearer JWT (`workflow.execute` permission)
- **Request Body**:
```json
{
  "workflow_id": "wf-1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
  "input_payload": {
    "document_id": "doc-123",
    "document_type": "POLICY",
    "title": "Corporate AI Usage Policy 2026"
  }
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Workflow execution triggered successfully.",
  "data": {
    "execution_id": "exec-1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "status": "RUNNING",
    "started_at": "2026-10-29T10:10:00Z"
  }
}
```

#### 16.2.5 Delete / Deactivate Workflow
- **Method**: `DELETE`
- **Path**: `/api/v1/workflows/{id}`
- **Auth**: Bearer JWT (`workflow.manage` permission)
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Workflow deleted successfully."
}
```

#### 16.2.6 List Workflow Executions
- **Method**: `GET`
- **Path**: `/api/v1/workflows/executions`
- **Auth**: Bearer JWT (`workflow.view` permission)
- **Query Parameters**:
  - `workflow_id`: UUID (optional)
  - `status`: string (optional: `RUNNING`, `WAITING_APPROVAL`, `COMPLETED`, `FAILED`, `CANCELLED`)
  - `page`: int (default: 1)
  - `page_size`: int (default: 20)
- **Response (200 OK)**:
```json
{
  "success": true,
  "total": 45,
  "page": 1,
  "page_size": 20,
  "data": [
    {
      "id": "exec-1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
      "workflow_id": "wf-1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
      "workflow_name": "Confidential Policy Ingestion & Review",
      "status": "COMPLETED",
      "duration_ms": 380,
      "started_at": "2026-10-29T10:10:00Z",
      "completed_at": "2026-10-29T10:10:01Z"
    }
  ]
}
```

#### 16.2.7 List Reusable Workflow Templates
- **Method**: `GET`
- **Path**: `/api/v1/workflows/templates`
- **Auth**: Bearer JWT (`workflow.view` permission)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "id": "tpl-doc-approval",
      "name": "Document Approval Pipeline",
      "description": "Multi-tier manager review and sign-off for newly uploaded documents.",
      "category": "GOVERNANCE",
      "trigger_type": "EVENT",
      "steps_preview": ["AI Summarize", "Suggest Reviewer", "Manager Approval", "Notify Team"]
    },
    {
      "id": "tpl-ai-summary",
      "name": "Autonomous AI Ingestion",
      "description": "Auto-summarize, keyword extraction, and vector index update.",
      "category": "AI",
      "trigger_type": "EVENT",
      "steps_preview": ["Extract Text", "Generate Summary", "Update Graph", "Notify Author"]
    },
    {
      "id": "tpl-scheduled-report",
      "name": "Weekly Executive Digest",
      "description": "Synthesizes organizational knowledge metrics and emails leadership.",
      "category": "REPORTING",
      "trigger_type": "SCHEDULE",
      "steps_preview": ["Aggregate Analytics", "Draft Briefing", "Send Email"]
    }
  ]
}
```

---

### 16.3 Approval Workflows

#### 16.3.1 Submit Workflow Approval Decision
- **Method**: `POST`
- **Path**: `/api/v1/workflows/approve`
- **Auth**: Bearer JWT (`workflow.approve` permission)
- **Request Body**:
```json
{
  "approval_id": "appr-1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
  "decision": "APPROVE",
  "comments": "Reviewed and approved for publication."
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Workflow step approved and execution resumed.",
  "data": {
    "approval_id": "appr-1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "status": "APPROVED",
    "execution_id": "exec-1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
    "responded_at": "2026-10-29T10:15:00Z"
  }
}
```

#### 16.3.2 List Pending Approvals
- **Method**: `GET`
- **Path**: `/api/v1/workflows/approvals/pending`
- **Auth**: Bearer JWT
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "id": "appr-1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
      "execution_id": "exec-1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
      "workflow_name": "Confidential Policy Ingestion & Review",
      "requester_name": "Alice Johnson",
      "step_description": "Manager approval required for document publication",
      "requested_at": "2026-10-29T10:10:00Z",
      "status": "PENDING"
    }
  ]
}
```

---

### 16.4 Notification Center

#### 16.4.1 List User Notifications
- **Method**: `GET`
- **Path**: `/api/v1/notifications`
- **Auth**: Bearer JWT
- **Query Parameters**:
  - `unread_only`: boolean (default: false)
  - `category`: string (optional: `WORKFLOW`, `APPROVAL`, `DOCUMENT`, `AI`, `SECURITY`, `SYSTEM`)
  - `page`: int (default: 1)
  - `page_size`: int (default: 20)
- **Response (200 OK)**:
```json
{
  "success": true,
  "unread_count": 3,
  "total": 18,
  "page": 1,
  "page_size": 20,
  "data": [
    {
      "id": "notif-1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
      "title": "Approval Required: Policy Ingestion",
      "message": "Corporate AI Usage Policy 2026 awaits your review and sign-off.",
      "channel": "IN_APP",
      "priority": "HIGH",
      "category": "APPROVAL",
      "is_read": false,
      "link_url": "/workflows/approvals",
      "created_at": "2026-10-29T10:10:00Z"
    }
  ]
}
```

#### 16.4.2 Mark Notification as Read
- **Method**: `POST`
- **Path**: `/api/v1/notifications/{id}/read`
- **Auth**: Bearer JWT
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Notification marked as read."
}
```

#### 16.4.3 Mark All Notifications as Read
- **Method**: `POST`
- **Path**: `/api/v1/notifications/read-all`
- **Auth**: Bearer JWT
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "All notifications marked as read."
}
```

#### 16.4.4 Get Notification Preferences
- **Method**: `GET`
- **Path**: `/api/v1/notifications/preferences`
- **Auth**: Bearer JWT
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "channel": "IN_APP",
      "category": "APPROVAL",
      "is_enabled": true
    },
    {
      "channel": "EMAIL",
      "category": "APPROVAL",
      "is_enabled": true
    },
    {
      "channel": "SLACK",
      "category": "SYSTEM",
      "is_enabled": false
    }
  ]
}
```

#### 16.4.5 Update Notification Preferences
- **Method**: `POST`
- **Path**: `/api/v1/notifications/preferences`
- **Auth**: Bearer JWT
- **Request Body**:
```json
{
  "preferences": [
    {
      "channel": "EMAIL",
      "category": "WORKFLOW",
      "is_enabled": true
    },
    {
      "channel": "SLACK",
      "category": "APPROVAL",
      "is_enabled": true
    }
  ]
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Notification preferences updated successfully."
}
```

---

### 16.5 Workflow Analytics

#### 16.5.1 Get Workflow Metrics & Analytics
- **Method**: `GET`
- **Path**: `/api/v1/workflows/analytics`
- **Auth**: Bearer JWT (`workflow.view` permission)
- **Query Parameters**:
  - `days`: int (default: 30)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "total_workflows_executed": 142,
    "success_rate": 97.2,
    "avg_execution_time_ms": 340.5,
    "failed_workflows": 4,
    "pending_approvals": 3,
    "notifications_delivered": 485,
    "ai_automation_usage_count": 96,
    "executions_by_day": [
      { "date": "2026-10-27", "count": 28 },
      { "date": "2026-10-28", "count": 34 },
      { "date": "2026-10-29", "count": 42 }
    ]
  }
}
```

---

## 17. Plugin SDK & Extension Framework

### 17.1 Plugin Lifecycle Management

#### 17.1.1 Install Plugin
- **Method**: `POST`
- **Path**: `/api/v1/plugins/install`
- **Auth**: Bearer JWT (`plugin.install` or `plugin.manage` permission)
- **Request Body**:
```json
{
  "plugin_id": "sap-s4hana-connector",
  "version": "1.2.0",
  "marketplace_package_url": "https://marketplace.keep.enterprise.io/packages/sap-s4hana-1.2.0.tar.gz",
  "configuration": {
    "endpoint_url": "https://sap.internal.acme.com",
    "client_id": "acme-sap-client"
  },
  "approved_permissions": [
    "Documents.Read",
    "Documents.Write",
    "Notifications.Send"
  ]
}
```
- **Response (201 Created)**:
```json
{
  "success": true,
  "message": "Plugin installed successfully.",
  "data": {
    "id": "plg-001-sap",
    "plugin_id": "sap-s4hana-connector",
    "name": "SAP S/4HANA Enterprise Connector",
    "version": "1.2.0",
    "category": "INTEGRATION",
    "status": "ACTIVE",
    "is_enabled": true,
    "installed_at": "2026-10-29T12:00:00Z"
  }
}
```

#### 17.1.2 List Installed Plugins
- **Method**: `GET`
- **Path**: `/api/v1/plugins/list`
- **Auth**: Bearer JWT (`plugin.view` permission)
- **Query Parameters**:
  - `category`: string (optional: `AI`, `INTEGRATION`, `WORKFLOW`, `UI`, `ANALYTICS`)
  - `status`: string (optional: `ACTIVE`, `INACTIVE`, `ERROR`, `PAUSED`)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "id": "plg-001-sap",
      "plugin_id": "sap-s4hana-connector",
      "name": "SAP S/4HANA Enterprise Connector",
      "version": "1.2.0",
      "category": "INTEGRATION",
      "status": "ACTIVE",
      "is_enabled": true,
      "developer": "Acme Integrations Inc.",
      "permissions": ["Documents.Read", "Documents.Write", "Notifications.Send"],
      "event_hooks": ["document.uploaded"],
      "installed_at": "2026-10-29T12:00:00Z"
    }
  ]
}
```

#### 17.1.3 Enable / Activate Plugin
- **Method**: `POST`
- **Path**: `/api/v1/plugins/enable`
- **Auth**: Bearer JWT (`plugin.manage` permission)
- **Request Body**:
```json
{
  "plugin_id": "sap-s4hana-connector"
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Plugin activated successfully.",
  "data": {
    "plugin_id": "sap-s4hana-connector",
    "status": "ACTIVE",
    "is_enabled": true
  }
}
```

#### 17.1.4 Disable / Deactivate Plugin
- **Method**: `POST`
- **Path**: `/api/v1/plugins/disable`
- **Auth**: Bearer JWT (`plugin.manage` permission)
- **Request Body**:
```json
{
  "plugin_id": "sap-s4hana-connector"
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Plugin deactivated successfully.",
  "data": {
    "plugin_id": "sap-s4hana-connector",
    "status": "INACTIVE",
    "is_enabled": false
  }
}
```

#### 17.1.5 Update Plugin Version
- **Method**: `POST`
- **Path**: `/api/v1/plugins/update`
- **Auth**: Bearer JWT (`plugin.manage` permission)
- **Request Body**:
```json
{
  "plugin_id": "sap-s4hana-connector",
  "target_version": "1.3.0"
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Plugin updated successfully.",
  "data": {
    "plugin_id": "sap-s4hana-connector",
    "previous_version": "1.2.0",
    "version": "1.3.0",
    "status": "ACTIVE"
  }
}
```

#### 17.1.6 Uninstall Plugin
- **Method**: `POST`
- **Path**: `/api/v1/plugins/uninstall`
- **Auth**: Bearer JWT (`plugin.manage` permission)
- **Request Body**:
```json
{
  "plugin_id": "sap-s4hana-connector",
  "purge_data": false
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "message": "Plugin uninstalled successfully.",
  "data": {
    "plugin_id": "sap-s4hana-connector",
    "uninstalled": true
  }
}
```

### 17.2 Configuration & Execution

#### 17.2.1 Execute Sandboxed Plugin Action
- **Method**: `POST`
- **Path**: `/api/v1/plugins/{id}/execute`
- **Auth**: Bearer JWT (`plugin.execute` permission)
- **Request Body**:
```json
{
  "action": "sync_invoices",
  "parameters": {
    "since": "2026-10-28T00:00:00Z",
    "limit": 50
  }
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "execution_id": "exec-plg-898",
    "status": "COMPLETED",
    "duration_ms": 84.5,
    "result": {
      "synced_count": 42,
      "skipped_count": 8
    }
  }
}
```

#### 17.2.2 Query Plugin Execution Logs
- **Method**: `GET`
- **Path**: `/api/v1/plugins/logs`
- **Auth**: Bearer JWT (`plugin.view` permission)
- **Query Parameters**:
  - `plugin_id`: string (optional)
  - `status`: string (optional: `SUCCESS`, `ERROR`, `TIMEOUT`)
  - `limit`: int (default: 50)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "id": "log-001",
      "plugin_id": "sap-s4hana-connector",
      "action": "document.uploaded",
      "status": "SUCCESS",
      "duration_ms": 48.2,
      "triggered_by": "event_hook",
      "timestamp": "2026-10-29T12:05:00Z"
    }
  ]
}
```

### 17.3 Plugin Marketplace

#### 17.3.1 Browse Marketplace Catalog
- **Method**: `GET`
- **Path**: `/api/v1/plugins/marketplace`
- **Auth**: Bearer JWT (`plugin.view` permission)
- **Query Parameters**:
  - `search`: string (optional)
  - `category`: string (optional)
  - `verified_only`: bool (default: false)
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "id": "tpl-ai-anthropic-claude",
      "plugin_id": "ai-anthropic-claude",
      "name": "Anthropic Claude 3.5 Sonnet Provider",
      "description": "Drop-in LLM adapter for Claude 3.5 Sonnet and Haiku inference.",
      "category": "AI",
      "developer": "Anthropic Community Partner",
      "version": "2.1.0",
      "verification_tier": "VERIFIED",
      "rating": 4.9,
      "installs_count": 1820,
      "min_keep_version": "3.0.0",
      "max_keep_version": "3.9.9",
      "permissions": ["AI.Query"],
      "event_hooks": ["ai.query.generated"]
    }
  ]
}
```






