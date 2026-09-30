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

### 3.1 Authentication (`/api/v1/auth`)

#### 3.1.1 User Login
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
    "expires_in": 3600,
    "user": {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "email": "user@enterprise.com",
      "full_name": "Jane Doe",
      "role": "OrgAdmin",
      "organization_id": "8bc92d11-3456-4211-89ab-1234567890ab"
    }
  }
}
```
- **Error Codes**: `AUTH_INVALID_CREDENTIALS` (401), `VALIDATION_ERROR` (422)

#### 3.1.2 Refresh Token
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
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```
- **Error Codes**: `AUTH_TOKEN_EXPIRED` (401), `AUTH_TOKEN_INVALID` (401)

#### 3.1.3 Get Current User Profile
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
- **Error Codes**: `AUTH_TOKEN_INVALID` (401)

---

### 3.2 Organizations & Tenants (`/api/v1/organizations`)

#### 3.2.1 Get Current Organization Details
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
    "is_active": true,
    "created_at": "2026-08-17T10:00:00Z"
  }
}
```

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

## 4. API Endpoints Registry & Ownership

| Path | Method | Purpose | Owner | Phase |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/auth/login` | POST | Authenticate user & issue tokens | Member 2 | Phase 1.4 |
| `/api/v1/auth/refresh` | POST | Refresh expired access token | Member 2 | Phase 1.4 |
| `/api/v1/auth/me` | GET | Retrieve authenticated profile | Member 2 | Phase 1.4 |
| `/api/v1/users` | GET / POST | Manage enterprise users | Member 2 | Phase 1.4 |
| `/api/v1/organizations/current` | GET | Retrieve tenant details | Member 2 | Phase 1.5 |
| `/api/v1/documents/upload` | POST | Multipart file ingestion | Member 2 & Member 1 | Phase 1.8 |
| `/api/v1/documents` | GET | List tenant documents | Member 2 | Phase 1.8 |
| `/api/v1/search/hybrid` | POST | Hybrid semantic + BM25 search | Member 1 & Member 2 | Phase 2.2 |
| `/api/v1/chat/query` | POST | Citation-backed RAG Q&A | Member 1 & Member 2 | Phase 2.2 |
| `/api/v1/chat/stream` | POST (SSE) | Real-time token streaming Q&A | Member 1 & Member 2 | Phase 2.2 |
| `/api/v1/graph/query` | POST | Knowledge Graph entity traversal | Member 1 & Member 2 | Phase 2.4 |
