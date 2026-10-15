/**
 * KEEP Enterprise Platform — Dashboard & User Experience Types.
 * Aligned with backend schemas (backend/app/schemas/dashboard.py)
 * and architecture specs (docs/Architecture/dashboard-architecture.md).
 */

import type { UserRole } from './auth';

// =============================================================================
// 1. Dashboard Summary Types
// =============================================================================

export interface DashboardUser {
  id: string;
  full_name: string;
  email: string;
  role: UserRole | string;
  avatar_url?: string | null;
}

export interface DashboardOrg {
  id: string;
  name: string;
  logo_url?: string | null;
  plan: 'starter' | 'professional' | 'enterprise' | string;
}

export interface DashboardKPI {
  total_projects: number;
  total_documents: number;
  total_members: number;
  upcoming_meetings: number;
  storage_used_bytes: number;
  storage_quota_bytes: number;
  ai_queries_today: number;
}

export interface DashboardSummary {
  user: DashboardUser;
  organization: DashboardOrg;
  kpi: DashboardKPI;
  greeting_time_of_day: 'morning' | 'afternoon' | 'evening';
}

// =============================================================================
// 2. Activity Feed Types
// =============================================================================

export interface ActivityActor {
  id: string;
  full_name: string;
  avatar_url?: string | null;
}

export interface ActivityEvent {
  id: string;
  actor: ActivityActor;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  resource_name: string;
  metadata?: Record<string, unknown>;
  occurred_at: string; // ISO 8601 UTC
}

export interface ActivityFeedFilterParams {
  page?: number;
  page_size?: number;
  filter?: 'all' | 'document' | 'project' | 'meeting' | 'user' | 'ai_summary' | string;
}

// =============================================================================
// 3. Recent Projects Types
// =============================================================================

export interface ProjectMemberSummary {
  id: string;
  full_name: string;
  avatar_url?: string | null;
}

export interface ProjectSummary {
  id: string;
  name: string;
  description?: string | null;
  status: 'active' | 'on_hold' | 'completed' | 'archived' | string;
  priority: 'low' | 'medium' | 'high' | 'critical' | string;
  progress_percent: number;
  deadline?: string | null;
  team_members: ProjectMemberSummary[];
  document_count: number;
  updated_at: string;
}

// =============================================================================
// 4. Recent Documents Types
// =============================================================================

export interface DocumentUploaderSummary {
  id: string;
  full_name: string;
}

export interface DocumentSummary {
  id: string;
  title: string;
  file_type: 'pdf' | 'docx' | 'txt' | 'md' | 'pptx' | 'xlsx' | 'other' | string;
  file_size_bytes: number;
  project_id?: string | null;
  project_name?: string | null;
  uploaded_by: DocumentUploaderSummary;
  uploaded_at: string;
  last_accessed_at: string;
  ai_summary_available: boolean;
}

// =============================================================================
// 5. Notifications Types
// =============================================================================

export interface NotificationItem {
  id: string;
  type: 'info' | 'warning' | 'success' | 'reminder' | 'security' | string;
  category?: 'info' | 'warning' | 'success' | 'reminder' | 'security' | string;
  title: string;
  body: string;
  message?: string;
  action_url?: string | null;
  link_url?: string | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationQueryParams {
  page?: number;
  page_size?: number;
  unread_only?: boolean;
}

export interface NotificationReadAllResponse {
  updated_count: number;
}

// =============================================================================
// 6. Analytics Overview Types
// =============================================================================

export interface TimeSeriesPoint {
  label: string;
  value: number;
}

export interface ProjectDistributionItem {
  status: string;
  count: number;
}

export interface DashboardAnalyticsSummary {
  period: 'week' | 'month' | 'quarter' | 'year' | string;
  documents_uploaded: TimeSeriesPoint[];
  active_users: TimeSeriesPoint[];
  new_members: TimeSeriesPoint[];
  project_distribution: ProjectDistributionItem[];
  ai_usage_trend: TimeSeriesPoint[];
  search_trend: TimeSeriesPoint[];
}

// =============================================================================
// 7. AI Query Assistant Types (Phase 1.7 Stub + Phase 2.2 RAG)
// =============================================================================

export interface AIQueryContext {
  project_id?: string | null;
  document_ids?: string[];
}

export interface AIQueryRequest {
  query: string;
  context?: AIQueryContext | null;
  stream?: boolean;
}

export interface DocumentReference {
  document_id: string;
  title: string;
  relevance_score: number;
  excerpt: string;
}

export interface AIStreamToken {
  token: string;
}

export interface AIStreamDone {
  sources: DocumentReference[];
  query_id?: string;
}

export interface AIStreamError {
  code: string;
  message: string;
}

// =============================================================================
// 8. Global Search Types
// =============================================================================

export interface GlobalSearchResultItem {
  type: 'project' | 'document' | 'user' | 'team' | string;
  id: string;
  title: string;
  subtitle: string;
  url: string;
  icon: string;
  relevance_score: number;
}

export interface GlobalSearchResponse {
  query: string;
  total: number;
  items: GlobalSearchResultItem[];
}

export interface GlobalSearchParams {
  q: string;
  type?: 'all' | 'project' | 'document' | 'user' | 'team';
  page?: number;
  page_size?: number;
}
