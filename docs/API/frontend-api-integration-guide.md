# Frontend API Integration & Architecture Guide (Phase 1.2)

> **Official Frontend API Client Documentation for KEEP Enterprise Platform**  
> *Authored by Member 3 (Frontend Engineering Lead) for Phase 1.2.*

---

## 1. Executive Summary

In Phase 1.2, the Frontend subsystem was aligned with the FastAPI backend architecture, OpenAPI 3.1 specifications, and the standardized JSON response envelopes. 

All 8 feature modules are backed by fully-typed domain service clients, centralized Axios interceptors, custom error handling, and a high-performance Server-Sent Events (SSE) streaming engine.

---

## 2. Type System Alignment (`frontend/src/types/`)

The TypeScript type definitions mirror the backend Pydantic models from `backend/app/schemas/` with 100% type fidelity:

| Frontend Type Interface | Backend Pydantic Model | Domain / Route |
| :--- | :--- | :--- |
| `ApiResponse<T>` | `ApiResponse[T]` | Global Success Envelope |
| `ApiErrorResponse`, `ApiErrorDetail` | `ApiErrorResponse`, `ErrorDetail` | Global Error Envelope |
| `PaginatedData<T>` | `PaginatedData[T]` | Generic Paginated Container |
| `ErrorCode` (enum) | `ErrorCode` (StrEnum) | Core Machine-Readable Error Codes |
| `LoginRequest`, `TokenResponse` | `LoginRequest`, `TokenResponse` | `/api/v1/auth/login` |
| `RefreshTokenRequest`, `RefreshTokenResponse` | `RefreshTokenRequest`, `RefreshTokenResponse` | `/api/v1/auth/refresh` |
| `UserProfileResponse` | `UserProfileResponse` | `/api/v1/auth/me`, `/api/v1/users/{id}` |
| `OrganizationResponse` | `OrganizationResponse` | `/api/v1/organizations/current` |
| `DocumentUploadResponse`, `DocumentResponse` | `DocumentUploadResponse`, `DocumentResponse` | `/api/v1/documents/*` |
| `HybridSearchRequest`, `SearchResponse` | `HybridSearchRequest`, `SearchResponse` | `/api/v1/search/hybrid` |
| `ChatQueryRequest`, `ChatQueryResponse` | `ChatQueryRequest`, `ChatQueryResponse` | `/api/v1/chat/query` |
| `ChatStreamRequest`, `StreamEvent` | SSE Stream generator | `/api/v1/chat/stream` |
| `AnalyticsSummaryResponse`, `UsageMetricsResponse` | `AnalyticsSummaryResponse`, `UsageMetricsResponse`| `/api/v1/analytics/*` |
| `HealthCheckResponse`, `DetailedHealthResponse` | `HealthCheckResponse`, `DetailedHealthResponse` | `/api/v1/health/*` |

---

## 3. Centralized API Client Architecture (`frontend/src/services/api.ts`)

### 3.1 Request Interceptor
- **Authentication**: Automatically extracts JWT token from `localStorage.getItem('keep_auth_token')` and attaches `Authorization: Bearer <token>`.
- **Distributed Tracing**: Automatically attaches an `X-Request-ID` header (`req_<timestamp>_<random>`) to correlate frontend actions with backend request logs.

### 3.2 Response Interceptor & Error Normalization
- **401 Unauthorized**: Automatically clears `keep_auth_token` to prevent persistent unauthorized retry loops.
- **Typed `ApiError` Class**: Translates backend `ApiErrorResponse` into a strongly-typed `ApiError` instance with:
  - `code`: `ErrorCode` (e.g. `AUTH_INVALID_CREDENTIALS`, `NOT_FOUND`, `VALIDATION_ERROR`)
  - `status`: HTTP status code (e.g. 400, 401, 404, 500)
  - `details`: Contextual validation array or metadata dictionary
  - `message`: Human-readable error explanation

---

## 4. Domain Service Modules (`frontend/src/services/`)

Each domain router has a corresponding service client:

1. **`authService`**: `login`, `refreshToken`, `getCurrentUser`, `logout`
2. **`userService`**: `listUsers`, `getUserById`
3. **`orgService`**: `getCurrentOrganization`
4. **`documentService`**: `uploadDocument` (multipart), `listDocuments`
5. **`searchService`**: `hybridSearch`
6. **`chatService`**: `queryChat` (synchronous), `streamChat` (SSE streaming)
7. **`analyticsService`**: `getSummary`, `getUsage`
8. **`healthService`**: `checkHealth`, `getDetailedHealth`, `getRootDiscovery`

---

## 5. Streaming Architecture (`useChatStream`)

For real-time RAG inference (`/api/v1/chat/stream`):
- Uses native `fetch` with `ReadableStream` and `TextDecoder` to handle HTTP POST SSE streams.
- Supported events:
  - `event: citation`: Emitted before tokens start streaming, containing grounding source files and snippets.
  - `event: token`: Emitted token-by-token for responsive generative text display.
  - `event: done`: Emitted when inference terminates with `total_tokens` consumed.
  - `event: error`: Emitted if pipeline encounters an exception.
- Provided React Hook: `useChatStream` with `answer`, `citations`, `isStreaming`, `error`, `sendStreamQuery`, and `abortStream`.

---

## 6. Verification & Test Evidence

- **TypeScript Strict Compilation**: `npx tsc --noEmit` -> 0 errors.
- **ESLint Quality Check**: `npm run lint` -> 0 errors, 0 warnings.
- **Unit Test Matrix**: `npm test` -> 34/34 tests passing across 6 test suites (100% pass rate).
- **Production Build**: `npm run build` -> 1,668 modules transformed, 0 errors.
