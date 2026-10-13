# Master Dashboard Architecture Specification

> **Phase 1.7 Architectural Blueprint: Dashboard Development & User Experience**
> **Author**: Member 1 (Project Lead & AI Architect)
> **Target Audience**: Member 2 (Backend Lead), Member 3 (Frontend Lead), Member 4 (DevOps Lead)
> **Specification Reference**: `devdocs/p1/p1.7.txt` (Chapters 1-24)
> **Status**: APPROVED & LOCKED FOR PHASE 1.7 IMPLEMENTATION

---

## 1. Executive Summary & Architectural Goals

The KEEP Dashboard is the primary command-center interface through which every authenticated user interacts with the platform. Rather than a collection of isolated pages, the dashboard must function as a unified, real-time workspace that surfaces organizational knowledge, project status, AI capabilities, and communication — all personalized by the user's role and organizational context.

Phase 1.7 establishes the **complete structural and behavioral blueprint** for this workspace. It defines the component hierarchy, widget data contracts, frontend state architecture, AI assistant integration surface, responsive layout system, theme management, accessibility rules, and performance targets. All four team members implement against these contracts.

### Core Objectives for Phase 1.7

1. **Role-Aware Personalization**: Every widget, navigation item, and KPI card adapts at render time to the authenticated user's role and permission set (established in Phase 1.6).
2. **Widget-Level Data Independence**: Each dashboard widget sources data from its own dedicated API endpoint, enabling independent caching, lazy loading, and incremental refresh.
3. **AI Assistant Integration Surface**: The AI Assistant widget provides the UI shell for future RAG query capabilities (Phases 2.x), fully integrated into the dashboard component tree today.
4. **Performance-First Architecture**: Dashboard skeleton renders in under 2 seconds; individual widget refreshes complete in under 500 ms.
5. **Accessibility Compliance**: Full WCAG 2.1 AA compliance — keyboard navigation, ARIA labels, focus management, and sufficient color contrast ratios.
6. **Theming Foundation**: Light, Dark, and System themes with a single CSS custom-properties token layer, enabling future organization-specific branding without component-level changes.

---

## 2. Dashboard Architecture Overview

### 2.1 Request Lifecycle

Every dashboard render follows this sequential loading architecture:

```
Browser Request
      |
      v
JWT Authentication Middleware (Phase 1.4)
      |
      v
Authorization Gate (Phase 1.6 - role + permissions loaded)
      |
      v
Dashboard Controller
      |
      v
[Parallel Widget API Calls]
  +-- GET /api/v1/dashboard          (user summary)
  +-- GET /api/v1/activity           (activity feed)
  +-- GET /api/v1/projects/recent    (projects widget)
  +-- GET /api/v1/documents/recent   (documents widget)
  +-- GET /api/v1/notifications      (notifications)
  +-- GET /api/v1/analytics/summary  (analytics cards)
      |
      v
Widget-Level Skeleton Render
      |
      v
Progressive Data Hydration (widgets fill as APIs resolve)
      |
      v
Fully Rendered, Role-Filtered Dashboard
```

Key architectural principle: Widget API calls are dispatched in parallel from the frontend immediately after the dashboard route mounts. No widget blocks another's render. Each widget independently transitions from skeleton to loaded to error state.

### 2.2 Frontend Application Layer Architecture

```
App
+-- Router
    +-- ProtectedRoute (Phase 1.4 auth guard)
        +-- DashboardLayout
            +-- TopNavBar
            |   +-- OrganizationLogo
            |   +-- GlobalSearchBar
            |   +-- NotificationBell
            |   +-- AIQuickAccessButton
            |   +-- ThemeSwitcher
            |   +-- UserProfileMenu
            |
            +-- Sidebar
            |   +-- NavItem: Dashboard
            |   +-- NavItem: Search
            |   +-- NavItem: AI Assistant
            |   +-- NavItem: Documents
            |   +-- NavItem: Projects
            |   +-- NavItem: Meetings
            |   +-- NavItem: Teams
            |   +-- NavItem: Analytics        [ADMIN / ORG_ADMIN only]
            |   +-- NavItem: Organization     [ADMIN / ORG_ADMIN only]
            |   +-- NavItem: Settings
            |   +-- NavItem: Profile
            |
            +-- MainWorkspace
                +-- WelcomeSection
                +-- KPICardGrid
                |   +-- KPICard: Total Projects
                |   +-- KPICard: Documents
                |   +-- KPICard: Team Members
                |   +-- KPICard: Meetings
                |   +-- KPICard: Storage Usage
                |   +-- KPICard: AI Queries      [ADMIN / ORG_ADMIN only]
                +-- ActivityFeedWidget
                +-- ProjectsWidget
                +-- DocumentsWidget
                +-- AIAssistantWidget
                +-- NotificationsWidget
                +-- AnalyticsWidget              [ADMIN / ORG_ADMIN only]
```

---

## 3. Component Contracts & Data Shapes

All frontend components consume backend data through the standard ApiResponse[T] envelope defined in `docs/API/api-contract.md`. The following are the authoritative TypeScript interface contracts for each dashboard widget. Member 3 (Frontend Lead) MUST implement against these interfaces. Member 2 (Backend Lead) MUST guarantee JSON responses match these shapes.

### 3.1 Dashboard Summary (GET /api/v1/dashboard)

```typescript
// Response: ApiResponse<DashboardSummary>
interface DashboardSummary {
  user: {
    id: string;
    full_name: string;
    email: string;
    role: UserRole;             // from Phase 1.6 RoleType enum
    avatar_url: string | null;
  };
  organization: {
    id: string;
    name: string;
    logo_url: string | null;
    plan: "starter" | "professional" | "enterprise";
  };
  kpi: {
    total_projects: number;
    total_documents: number;
    total_members: number;
    upcoming_meetings: number;
    storage_used_bytes: number;
    storage_quota_bytes: number;
    ai_queries_today: number;   // only populated for ADMIN / ORG_ADMIN roles
  };
  greeting_time_of_day: "morning" | "afternoon" | "evening";
}
```

### 3.2 Activity Feed (GET /api/v1/activity)

```typescript
// Query params: ?page=1&page_size=20&filter=all
// Response: ApiResponse<PaginatedData<ActivityEvent>>
interface ActivityEvent {
  id: string;
  actor: {
    id: string;
    full_name: string;
    avatar_url: string | null;
  };
  action: ActivityAction;
  resource_type: ResourceType;
  resource_id: string;
  resource_name: string;
  metadata: Record<string, unknown>;
  occurred_at: string;          // ISO 8601 UTC
}
```

### 3.3 Recent Projects (GET /api/v1/projects/recent)

```typescript
// Query params: ?limit=6
// Response: ApiResponse<ProjectSummary[]>
interface ProjectSummary {
  id: string;
  name: string;
  description: string | null;
  status: "active" | "on_hold" | "completed" | "archived";
  priority: "low" | "medium" | "high" | "critical";
  progress_percent: number;     // 0-100
  deadline: string | null;      // ISO 8601 date
  team_members: {
    id: string;
    full_name: string;
    avatar_url: string | null;
  }[];
  document_count: number;
  updated_at: string;           // ISO 8601 UTC
}
```

### 3.4 Recent Documents (GET /api/v1/documents/recent)

```typescript
// Query params: ?limit=8
// Response: ApiResponse<DocumentSummary[]>
interface DocumentSummary {
  id: string;
  title: string;
  file_type: "pdf" | "docx" | "txt" | "md" | "pptx" | "xlsx" | "other";
  file_size_bytes: number;
  project_id: string | null;
  project_name: string | null;
  uploaded_by: {
    id: string;
    full_name: string;
  };
  uploaded_at: string;          // ISO 8601 UTC
  last_accessed_at: string;     // ISO 8601 UTC
  ai_summary_available: boolean;
}
```

### 3.5 Notifications (GET /api/v1/notifications)

```typescript
// Query params: ?page=1&page_size=20&unread_only=false
// Response: ApiResponse<PaginatedData<Notification>>
interface Notification {
  id: string;
  type: "info" | "warning" | "success" | "reminder" | "security";
  title: string;
  body: string;
  action_url: string | null;
  is_read: boolean;
  created_at: string;           // ISO 8601 UTC
}
```

### 3.6 Analytics Summary (GET /api/v1/analytics/summary)

```typescript
// Query params: ?period=week  (week | month | quarter | year)
// Response: ApiResponse<AnalyticsSummary>
// Authorization: ADMIN / ORG_ADMIN only - other roles receive 403
interface AnalyticsSummary {
  period: "week" | "month" | "quarter" | "year";
  documents_uploaded: TimeSeriesPoint[];
  active_users: TimeSeriesPoint[];
  new_members: TimeSeriesPoint[];
  project_distribution: {
    status: string;
    count: number;
  }[];
  ai_usage_trend: TimeSeriesPoint[];
  search_trend: TimeSeriesPoint[];
}

interface TimeSeriesPoint {
  label: string;               // e.g., "Mon", "Jan", "Q1"
  value: number;
}
```

---

## 4. Frontend State Management Architecture

The dashboard uses a Context + custom hooks pattern (consistent with Phase 1.5 UI patterns). No global state library is introduced for Phase 1.7 — component-level state and custom hooks are sufficient.

### 4.1 Dashboard Context

```typescript
// frontend/src/contexts/DashboardContext.tsx
interface DashboardContextValue {
  summary: DashboardSummary | null;
  isLoading: boolean;
  refreshDashboard: () => void;
  unreadNotificationCount: number;
  theme: "light" | "dark" | "system";
  setTheme: (t: "light" | "dark" | "system") => void;
}
```

### 4.2 Widget Data Hooks

Each widget uses a dedicated hook that encapsulates fetch logic, loading/error states, and optional polling:

```typescript
useDashboardSummary()         // -> { summary, isLoading, error, refresh }
useActivityFeed(filters)      // -> { events, isLoading, error, loadMore, hasMore }
useRecentProjects()           // -> { projects, isLoading, error }
useRecentDocuments()          // -> { documents, isLoading, error }
useNotifications(opts)        // -> { notifications, unreadCount, markRead, isLoading }
useAnalyticsSummary(period)   // -> { analytics, isLoading, error, changePeriod }
```

### 4.3 Permission-Gated Widget Rendering

Widgets that require elevated roles are wrapped in a PermissionGate component (established in Phase 1.6). This prevents rendering the widget and its API calls for unauthorized users:

```tsx
<PermissionGate requires="ORG_ANALYTICS_READ">
  <AnalyticsWidget />
</PermissionGate>

<PermissionGate requires="ORG_ANALYTICS_READ">
  <KPICard title="AI Queries" value={kpi.ai_queries_today} />
</PermissionGate>
```

---

## 5. AI Assistant Widget Architecture

The AI Assistant widget is the highest-priority integration point in Phase 1.7. It establishes the UI shell and interaction contract that Phase 2 RAG pipelines will fulfill.

### 5.1 Widget States

```
IDLE      -> User has not interacted. Shows suggested prompts.
TYPING    -> User is entering a query.
LOADING   -> Query submitted; awaiting backend response.
STREAMING -> Server-Sent Event stream active; tokens arriving incrementally.
COMPLETE  -> Full response received and rendered.
ERROR     -> Backend returned error or stream timed out.
```

### 5.2 Interaction Contract (Phase 1.7 Stub + Phase 2 Target)

```typescript
// Phase 1.7: stub endpoint returns a canned response
// Phase 2.x: same endpoint returns streamed RAG output

// POST /api/v1/ai/query  (streamed via SSE)
interface AIQueryRequest {
  query: string;
  context?: {
    project_id?: string;
    document_ids?: string[];
  };
  stream: boolean;             // always true for dashboard widget
}

// SSE event stream:
// event: token     data: { "token": "..." }
// event: done      data: { "sources": DocumentReference[], "query_id": string }
// event: error     data: { "code": "AI_UNAVAILABLE", "message": "..." }

interface DocumentReference {
  document_id: string;
  title: string;
  relevance_score: number;
  excerpt: string;
}
```

### 5.3 AI Widget Suggested Prompts (Phase 1.7 Stub)

The widget pre-populates contextual suggested prompts based on user role:

| Role | Suggested Prompts |
|------|-------------------|
| ADMIN / ORG_ADMIN | "Summarize this week's activity", "Which projects are behind schedule?", "What knowledge is most accessed?" |
| PROJECT_MANAGER | "Summarize open tasks for my projects", "Which documents were uploaded this week?" |
| MEMBER | "Find documents related to [project]", "Summarize the last meeting notes" |
| VIEWER | "What projects can I access?", "Find documents in [project]" |

### 5.4 AI Widget Future Roadmap (Phase 2.x Integration Points)

1. **Phase 2.1 (Knowledge Ingestion)**: Uploaded documents are indexed and become retrievable by the AI widget query endpoint.
2. **Phase 2.2 (RAG Engine)**: `POST /api/v1/ai/query` transitions from stub to full RAG pipeline. The DocumentReference sources list is populated from the vector search.
3. **Phase 2.3 (Meeting Intelligence)**: "Summarize meeting notes" prompt routes to the Meeting Intelligence module.
4. **Phase 2.5 (Knowledge Graph)**: Query responses include entity-linked context from the KG traversal results.
5. **Phase 3.1 (Enterprise Search)**: Global search bar integrates semantic similarity ranking from the enterprise search engine.

---

## 6. Navigation & Permission Filtering

The Sidebar navigation is driven by the user's permission set resolved during authentication (Phase 1.6).

| Nav Item | ADMIN | ORG_ADMIN | PROJECT_MANAGER | MEMBER | VIEWER |
|----------|:-----:|:---------:|:---------------:|:------:|:------:|
| Dashboard | Y | Y | Y | Y | Y |
| Search | Y | Y | Y | Y | Y |
| AI Assistant | Y | Y | Y | Y | Y |
| Documents | Y | Y | Y | Y | Y |
| Projects | Y | Y | Y | Y | Y |
| Meetings | Y | Y | Y | Y | Y |
| Teams | Y | Y | Y | Y | N |
| Analytics | Y | Y | N | N | N |
| Organization | Y | Y | N | N | N |
| Settings | Y | Y | Y | Y | N |
| Profile | Y | Y | Y | Y | Y |

Navigation filtering MUST be enforced via PermissionGate wrappers, not by CSS display:none. This prevents role escalation through DOM inspection.

---

## 7. Theme Management Architecture

Themes are implemented as a single CSS custom-properties token layer on :root. No component ever references hardcoded color values — only token names.

### 7.1 Token Layer (Design System Foundation)

```css
/* frontend/src/styles/tokens.css */
:root[data-theme="light"] {
  --color-background-primary: #F8F9FA;
  --color-background-secondary: #FFFFFF;
  --color-background-card: #FFFFFF;
  --color-text-primary: #1A1A2E;
  --color-text-secondary: #6B7280;
  --color-border: #E5E7EB;
  --color-accent-primary: #6366F1;
  --color-accent-secondary: #8B5CF6;
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-danger: #EF4444;
  --color-info: #3B82F6;
  --shadow-card: 0 1px 3px rgba(0,0,0,0.08);
  --shadow-elevated: 0 4px 16px rgba(0,0,0,0.12);
}

:root[data-theme="dark"] {
  --color-background-primary: #0F0F1A;
  --color-background-secondary: #1A1A2E;
  --color-background-card: #1E1E30;
  --color-text-primary: #F1F5F9;
  --color-text-secondary: #94A3B8;
  --color-border: #2D2D44;
  --color-accent-primary: #818CF8;
  --color-accent-secondary: #A78BFA;
  --color-success: #34D399;
  --color-warning: #FBBF24;
  --color-danger: #F87171;
  --color-info: #60A5FA;
  --shadow-card: 0 1px 3px rgba(0,0,0,0.4);
  --shadow-elevated: 0 4px 24px rgba(0,0,0,0.6);
}
```

### 7.2 Theme Persistence

- Theme preference is persisted in localStorage under key `keep_theme`.
- On app mount, the stored preference is applied before first render to prevent flash of unstyled content (FOUC).
- `system` theme reads `window.matchMedia('(prefers-color-scheme: dark)')` and subscribes to changes.

---

## 8. Responsive Layout Specification

| Breakpoint | Width | Sidebar | Widget Grid | Columns |
|------------|-------|---------|-------------|---------|
| Desktop | >= 1280px | Expanded (240px) | 3-col | Full layout |
| Tablet | 768px - 1279px | Collapsed (icon-only, 64px) | 2-col | Stacked pairs |
| Mobile | < 768px | Hidden (bottom nav) | 1-col | Full width stacked |

---

## 9. Performance Architecture

### 9.1 Loading Strategy

| Phase | Technique | Target |
|-------|-----------|--------|
| Route mount | Skeleton screens for all widgets | < 100ms |
| Critical path (welcome + KPIs) | Priority fetch | < 500ms |
| Secondary widgets | Parallel async fetch | < 1000ms |
| Charts & analytics | Deferred / lazy loaded | < 2000ms |
| Full dashboard ready | All widgets hydrated | < 2000ms |

### 9.2 Client-Side Caching Strategy

- DashboardSummary: stale-while-revalidate, TTL 60s
- ActivityFeed: stale-while-revalidate, TTL 30s, auto-refresh on focus
- RecentProjects: stale-while-revalidate, TTL 60s
- RecentDocuments: stale-while-revalidate, TTL 60s
- Notifications: stale-while-revalidate, TTL 15s, badge count live-polled every 30s
- AnalyticsSummary: stale-while-revalidate, TTL 300s

### 9.3 Backend Caching Layer (Member 2)

Backend responses for dashboard endpoints MUST be cached in Redis:
- GET /api/v1/dashboard: Redis key `dashboard:{user_id}:{org_id}`, TTL 60s
- GET /api/v1/analytics/summary: Redis key `analytics:{org_id}:{period}`, TTL 300s
- Cache invalidated on relevant write operations (document upload, project update, member join).

---

## 10. Accessibility Specification (WCAG 2.1 AA)

| Requirement | Implementation |
|-------------|----------------|
| Keyboard navigation | All interactive elements reachable via Tab; logical focus order |
| Focus indicators | Visible ring using --color-accent-primary at 2px offset |
| Screen reader | All widgets have role, aria-label, aria-live |
| Color contrast | Text contrast ratio >= 4.5:1 (AA); large text >= 3:1 |
| Skip links | Skip to content link at page top |
| Notifications | Activity feed updates announced via aria-live="polite" |
| Icons | All icon-only buttons have aria-label and title |
| Loading states | Skeleton elements have aria-busy="true" |

---

## 11. Global Search Architecture

### 11.1 Search Scope (Phase 1.7)

Phase 1.7 establishes the search UI infrastructure; full semantic engine integration is Phase 3.1.

```
Search Query
     |
     v
Frontend Debounce (300ms)
     |
     v
GET /api/v1/search?q={query}&type={all|project|document|user|team}&page=1
     |
     +-- Projects  -> full-text match on name + description
     +-- Documents -> full-text match on title
     +-- Users     -> match on full_name + email (org-scoped)
     +-- Teams     -> match on name + description
```

### 11.2 Search Result Shape

```typescript
interface SearchResultItem {
  type: "project" | "document" | "user" | "team";
  id: string;
  title: string;
  subtitle: string;
  url: string;
  icon: string;
  relevance_score: number;
}
```

---

## 12. Security Considerations

1. **Authorization Enforcement**: All dashboard API endpoints enforce the Phase 1.6 authorization pipeline. Frontend filtering is UI convenience only — backend is source of truth.
2. **Notification Content Safety**: Notification bodies are sanitized server-side. Frontend renders via textContent, not innerHTML.
3. **AI Query Sanitization**: User-typed AI queries are sanitized before submission (strip control characters, limit 4096 chars).
4. **CSRF**: All non-GET requests include the X-CSRF-Token header (Phase 1.4 contract).
5. **Rate Limiting**: POST /api/v1/ai/query is rate-limited to 60 requests/hour per user via Redis.

---

## 13. Testing Contracts

### 13.1 Member 3 — Frontend Unit Tests (Vitest)

Each widget component MUST have tests for:
- Skeleton loading state
- Successful data render
- Empty state (no data)
- Error state (API failure)
- Role-gated visibility (renders vs. null for unauthorized role)

### 13.2 Member 2 — Backend Unit Tests (Pytest)

Each dashboard endpoint MUST have tests for:
- Successful response with correct data shape
- Tenant isolation (no cross-org data leakage)
- Role authorization (403 for insufficient permissions)
- Pagination boundary conditions

### 13.3 Member 4 — E2E Tests (Playwright)

E2E scenarios:
- Full dashboard load for each role type
- Theme switching persisted across page reload
- Notification mark-as-read interaction
- AI widget query submission (stub response)
- Responsive layout at 375px, 768px, 1440px viewports

---

## 14. Summary of Member Responsibilities

| Member | Phase 1.7 Deliverables |
|--------|------------------------|
| Member 1 (AI Lead) | This document; ADR-020, ADR-021, ADR-022; API contract Section 5; AI widget integration roadmap |
| Member 2 (Backend Lead) | Dashboard summary, activity, projects, documents, notifications, analytics endpoints; stub AI query endpoint; Redis caching; notification service |
| Member 3 (Frontend Lead) | DashboardLayout, TopNavBar, Sidebar, WelcomeSection, KPICardGrid, all widgets; DashboardContext; custom hooks; theme system; responsive CSS; GlobalSearchBar |
| Member 4 (DevOps Lead) | E2E Playwright tests; performance benchmarks; Redis cache validation; cross-browser compatibility; dashboard API load testing |
