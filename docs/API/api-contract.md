# API Contracts Specification (docs/api/api-contract.md)

> **Evolving Engineering API Documentation for KEEP**  
> *Derived from Phase 1.2, 1.4, 1.8, 2.2, and 2.3 of `devdocs/` specifications.*

---

## 1. Overview

This document specifies the RESTful API endpoints for KEEP. All endpoints are prefixed with `/api/v1` and return JSON responses adhering to standard HTTP status codes.

---

## 2. Authentication & Identity Management

### 2.1 User Login

#### Method
`POST`

#### Path
`/api/v1/auth/login`

#### Purpose
Authenticates user credentials and returns JWT access and refresh tokens.

#### Authentication
None (Public endpoint)

#### Request Body
```json
{
  "email": "user@organization.com",
  "password": "SecurePassword123!"
}
```

#### Response (200 OK)
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "dGhpcyBpcy...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Errors
- `400 Bad Request`: Invalid request format.
- `401 Unauthorized`: Invalid email or password.

#### Owner
Agent 1 (Backend)

#### Consumers
Agent 2 (Frontend)

#### Status
PLANNED (Phase 1.4)

---

## 3. Document Management & Upload

### 3.1 Document Upload

#### Method
`POST`

#### Path
`/api/v1/documents/upload`

#### Purpose
Uploads a document (PDF, DOCX, TXT, Image) for processing and AI ingestion.

#### Authentication
Bearer JWT Token (`OrgAdmin`, `Manager`, `Member`)

#### Request (Multipart Form-Data)
- `file`: Binary file stream
- `title`: string (optional)
- `description`: string (optional)
- `tags`: string array (optional)

#### Response (202 Accepted)
```json
{
  "document_id": "doc_987654321",
  "filename": "annual_report_2026.pdf",
  "status": "PROCESSING",
  "created_at": "2026-08-17T13:00:00Z"
}
```

#### Errors
- `400 Bad Request`: Unsupported file type or file size exceeds limit.
- `401 Unauthorized`: Missing or invalid token.
- `403 Forbidden`: Insufficient organization permissions.

#### Owner
Agent 1 (Backend API) / Agent 3 (Ingestion Worker)

#### Consumers
Agent 2 (Frontend Upload Feature)

#### Status
PLANNED (Phase 1.8 / Phase 2.1)

---

## 4. Search & RAG Engine

### 4.1 RAG Chat Query

#### Method
`POST`

#### Path
`/api/v1/chat/query`

#### Purpose
Submits a natural language query to the RAG Engine and retrieves citation-backed AI answers.

#### Authentication
Bearer JWT Token

#### Request Body
```json
{
  "query": "What is our policy regarding remote work?",
  "conversation_id": "conv_12345",
  "top_k": 5,
  "include_citations": true
}
```

#### Response (200 OK)
```json
{
  "answer": "According to the employee handbook, employees are eligible for remote work up to 2 days per week with manager approval.",
  "conversation_id": "conv_12345",
  "citations": [
    {
      "document_id": "doc_987654321",
      "title": "Employee_Handbook_2026.pdf",
      "page_number": 14,
      "snippet": "Remote work is permitted up to 2 days per week..."
    }
  ]
}
```

#### Errors
- `401 Unauthorized`: Invalid authentication.
- `500 Internal Server Error`: AI inference or vector retrieval error.

#### Owner
Agent 1 (Backend / RAG Engine)

#### Consumers
Agent 2 (Frontend AI Assistant Chat Feature)

#### Status
PLANNED (Phase 2.2)

---

## 5. API Status Summary

| Path | Method | Phase | Status | Owner |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/auth/login` | POST | Phase 1.4 | PLANNED | Agent 1 |
| `/api/v1/auth/me` | GET | Phase 1.4 | PLANNED | Agent 1 |
| `/api/v1/users` | GET / POST | Phase 1.4 | PLANNED | Agent 1 |
| `/api/v1/organizations` | GET / POST | Phase 1.5 | PLANNED | Agent 1 |
| `/api/v1/documents/upload` | POST | Phase 1.8 | PLANNED | Agent 1 / Agent 3 |
| `/api/v1/documents` | GET | Phase 1.8 | PLANNED | Agent 1 |
| `/api/v1/chat/query` | POST | Phase 2.2 | PLANNED | Agent 1 |
| `/api/v1/graph/nodes` | GET | Phase 2.4 | PLANNED | Agent 1 / Agent 3 |
