# KEEP — Backend Architecture & API Foundation Specification (docs/Architecture/backend-architecture.md)

> **Phase 1.2 Master Architectural Blueprint & Service Interface Specification**  
> *Owner: Member 1 (Project Lead & AI Architect)*  
> *Target Implementer: Member 2 (Backend Lead) | Consumers: Member 3 (Frontend Lead), Member 4 (DevOps Lead)*  
> *Derived from: devdocs/p1/p1.2.txt*

---

## 1. Executive Summary & Architectural Goals

The KEEP backend is the central orchestration and cognitive computing engine of the enterprise platform. Built upon **FastAPI (Python 3.12)**, **SQLAlchemy 2.0 (Async)**, **Pydantic v2**, and **PostgreSQL 16 with pgvector**, the backend architecture must satisfy high concurrency, strict multi-tenant data boundaries, seamless streaming AI generation, and modular extensibility.

### Core Architectural Directives:
1. **Layered Separation of Concerns**: Strict boundary isolation across Router -> Service -> Repository -> ORM.
2. **Standardized Response Envelope**: Uniform JSON envelope structure across all success and error responses.
3. **Multi-Tenant Row-Level Security (RLS)**: Enforced isolation at both the service and repository tiers via tenant context injection.
4. **Decoupled AI & Cognitive Processing**: Abstract interfaces for LLMs, Embedding providers, RAG pipelines, and Vector search, shielding core business domains from vendor lock-in.
5. **Interactive API Discovery**: OpenAPI 3.1 / Swagger UI compliant documentation generated automatically with complete schema definitions.

---

## 2. Layered Architecture & Request Lifecycle

Every HTTP and WebSocket request follows a deterministic, unidirectional lifecycle:

```
+-------------------------------------------------------------------------------+
|                                INCOMING HTTP REQUEST                          |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼
+-------------------------------------------------------------------------------+
|                              MIDDLEWARE PIPELINE                              |
|  1. Request ID Middleware (X-Request-ID propagation)                          |
|  2. CORS Middleware (Origin, Header, Method whitelisting)                     |
|  3. Global Logging & Timing Middleware (Structured JSON logs)                 |
|  4. Global Exception Interceptor Middleware (RFC 7807 / Standard Envelope)   |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼
+-------------------------------------------------------------------------------+
|                               ROUTER LAYER (v1)                               |
|  - URL Routing & Path Matching (/api/v1/...)                                  |
|  - Dependency Injection (get_db, get_current_user, get_tenant_context)        |
|  - Pydantic v2 Request Validation & Type Coercion                             |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼
+-------------------------------------------------------------------------------+
|                                SERVICE LAYER                                  |
|  - Domain Business Logic & Validation Rules                                   |
|  - Multi-Tenant Permission Enforcement (RBAC)                                 |
|  - AI Orchestration & Async Task Dispatching (Redis / Celery)                |
|  - Transaction Management Coordination                                        |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼
+-------------------------------------------------------------------------------+
|                              REPOSITORY LAYER                                 |
|  - Database Access Abstraction (CRUD, Filter, Pagination)                     |
|  - SQL / pgvector Query Construction                                          |
|  - Tenant Boundary Injection (WHERE organization_id = :org_id)                |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼
+-------------------------------------------------------------------------------+
|                            DATABASE & STORAGE LAYER                           |
|  - PostgreSQL 16 (Tables, Foreign Keys, Indexes, pgvector HNSW)               |
|  - Redis Cache & Task Broker                                                  |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼
+-------------------------------------------------------------------------------+
|                          STANDARDIZED API RESPONSE                            |
|  - Success: {"success": true, "message": "...", "data": {...}}                |
|  - Error:   {"success": false, "error": {"code": "...", "message": "..."}}    |
+-------------------------------------------------------------------------------+
```

---

## 3. Directory Layout & Module Responsibilities

The `/backend/app` directory follows a modular layout designed for multi-agent development:

```
backend/
├── app/
│   ├── api/
│   │   ├── dependencies/        # FastAPI Depends providers (Auth, Tenant, DB, AI)
│   │   ├── middleware/          # Request ID, Logging, Error, CORS middlewares
│   │   └── v1/                  # Versioned API Routers
│   │       ├── auth.py          # Authentication & Token Refresh endpoints
│   │       ├── users.py         # User management endpoints
│   │       ├── organizations.py # Tenant management endpoints
│   │       ├── documents.py     # File upload & document metadata endpoints
│   │       ├── search.py        # Hybrid & Vector Search endpoints
│   │       ├── chat.py          # AI Assistant & RAG Q&A endpoints
│   │       └── analytics.py     # Usage & Audit metrics endpoints
│   │
│   ├── core/
│   │   ├── config.py            # Pydantic BaseSettings centralized configuration
│   │   ├── logging.py           # Structured logging configuration
│   │   ├── security.py          # JWT, Passlib Bcrypt, Password hashing
│   │   └── constants.py         # System-wide enums and error codes
│   │
│   ├── database/
│   │   ├── session.py           # Async SQLAlchemy engine & session factory
│   │   ├── base.py              # DeclarativeBase with common timestamp/UUID mixins
│   │   └── migrations/          # Alembic migrations environment
│   │
│   ├── models/                  # SQLAlchemy ORM database models
│   ├── schemas/                 # Pydantic v2 Request/Response DTO models
│   ├── repositories/            # Database query abstractions & CRUD
│   ├── services/                # Business domain logic
│   │   ├── ai/                  # AI LLM, Embedding & Assistant services (Member 1)
│   │   ├── rag/                 # RAG, Hybrid Retriever, Context builder (Member 1)
│   │   ├── auth_service.py      # User authentication & token service (Member 2)
│   │   └── document_service.py  # File ingestion & storage service (Member 2)
│   │
│   ├── workers/                 # Celery async ingestion tasks
│   ├── utils/                   # Common helper functions
│   └── main.py                  # Application entrypoint & middleware mounting
└── tests/
    ├── unit/                    # Fast isolated component unit tests
    ├── integration/             # Database & Router integration tests
    └── e2e/                     # End-to-end user journey tests
```

---

## 4. API Standardization & Response Envelope

In accordance with Chapters 14 and 15 of `devdocs/p1/p1.2.txt`, all KEEP endpoints return a standard response envelope.

### 4.1 Success Response Schema (`ApiResponse[T]`)
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": { ... }
}
```

### 4.2 Error Response Schema (`ApiErrorResponse`)
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

### 4.3 Standard Error Code Taxonomy
| Category | Error Code | HTTP Status | Description |
| :--- | :--- | :--- | :--- |
| **Authentication** | `AUTH_INVALID_CREDENTIALS` | 401 | Email or password incorrect |
| **Authentication** | `AUTH_TOKEN_EXPIRED` | 401 | JWT access token has expired |
| **Authentication** | `AUTH_TOKEN_INVALID` | 401 | JWT signature or payload invalid |
| **Authorization** | `AUTH_FORBIDDEN` | 403 | Insufficient RBAC role permissions |
| **Multi-Tenancy** | `TENANT_NOT_FOUND` | 404 | Organization ID does not exist |
| **Multi-Tenancy** | `TENANT_ACCESS_DENIED` | 403 | User cannot access requested organization |
| **Validation** | `VALIDATION_ERROR` | 422 | Pydantic schema validation failure |
| **Resource** | `RESOURCE_NOT_FOUND` | 404 | Requested entity (doc, user, task) not found |
| **Resource** | `RESOURCE_CONFLICT` | 409 | Duplicate entity (e.g. email already exists) |
| **AI / RAG** | `AI_SERVICE_UNAVAILABLE` | 503 | Upstream LLM/Embedding provider unreachable |
| **AI / RAG** | `AI_TOKEN_LIMIT_EXCEEDED` | 400 | Prompt exceeded context window limit |
| **System** | `INTERNAL_SERVER_ERROR` | 500 | Unhandled server error |

---

## 5. Dependency Injection Architecture

FastAPI dependencies (`app/api/dependencies/`) ensure loose coupling and testability:

```python
# Database Session Dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

# Current User Dependency
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserModel:
    payload = verify_jwt_token(token)
    user = await user_repo.get_by_id(db, payload.user_id)
    if not user:
        raise AuthenticationException("AUTH_TOKEN_INVALID", "User not found")
    return user

# Tenant Context Dependency
async def get_tenant_context(
    user: UserModel = Depends(get_current_user)
) -> TenantContext:
    return TenantContext(
        organization_id=user.organization_id,
        user_id=user.id,
        role=user.role
    )
```

---

## 6. AI & RAG Subsystem Integration Points

As defined by Member 1 (AI Architect), the AI/RAG engine connects cleanly into the backend service architecture without polluting database entities or HTTP routers:

1. **RAG Service Adapter (`BaseRAGEngine`)**: Injected into `/api/v1/chat` and `/api/v1/search` endpoints via dependency injection.
2. **Streaming Protocol**: Real-time token streaming is exposed via Server-Sent Events (SSE) `/api/v1/chat/stream` yielding typed JSON events (`token`, `citation`, `done`).
3. **Execution Context (`AIExecutionContext`)**: Captures query latency, prompt tokens, completion tokens, model name, and tenant ID for auditability.
4. **Semantic Caching (`BaseSemanticCacheService`)**: Evaluates query similarity against Redis vector cache before invoking upstream LLM APIs, cutting latency and API costs.

---

## 7. Approval & Alignment Matrix

- **Architecture Approved by**: Member 1 (Project Lead & AI Architect)
- **Implementation Assigned to**: Member 2 (Backend Lead)
- **Frontend Consumer**: Member 3 (Frontend Lead)
- **DevOps/Infrastructure**: Member 4 (DevOps Lead)
