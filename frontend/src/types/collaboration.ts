/**
 * Phase 3.2 Real-Time Collaboration, Team Workspaces & Knowledge Sharing TypeScript Definitions.
 * Aligned with docs/api/api-contract.md Section 14 and devdocs/p3/p3.2.txt.
 * Author: Member 3 (Frontend & UI Lead)
 */

export const WorkspaceRole = {
  ADMIN: 'ADMIN',
  MEMBER: 'MEMBER',
  VIEWER: 'VIEWER',
  GUEST: 'GUEST',
} as const;
export type WorkspaceRole = (typeof WorkspaceRole)[keyof typeof WorkspaceRole];

export const PresenceStatus = {
  ONLINE: 'ONLINE',
  OFFLINE: 'OFFLINE',
  AWAY: 'AWAY',
  EDITING: 'EDITING',
  VIEWING: 'VIEWING',
} as const;
export type PresenceStatus = (typeof PresenceStatus)[keyof typeof PresenceStatus];

export const CommentStatus = {
  OPEN: 'OPEN',
  RESOLVED: 'RESOLVED',
  ARCHIVED: 'ARCHIVED',
} as const;
export type CommentStatus = (typeof CommentStatus)[keyof typeof CommentStatus];

export const ActivityType = {
  DOCUMENT_UPLOAD: 'DOCUMENT_UPLOAD',
  DOCUMENT_UPDATE: 'DOCUMENT_UPDATE',
  COMMENT_ADDED: 'COMMENT_ADDED',
  REPLY_ADDED: 'REPLY_ADDED',
  USER_MENTION: 'USER_MENTION',
  PROJECT_CREATED: 'PROJECT_CREATED',
  MEMBER_JOINED: 'MEMBER_JOINED',
  AI_SUMMARY_GENERATED: 'AI_SUMMARY_GENERATED',
  DISCUSSION_RESOLVED: 'DISCUSSION_RESOLVED',
  VERSION_CHECKPOINT: 'VERSION_CHECKPOINT',
} as const;
export type ActivityType = (typeof ActivityType)[keyof typeof ActivityType];

export const ApprovalStatus = {
  DRAFT: 'DRAFT',
  PENDING_REVIEW: 'PENDING_REVIEW',
  APPROVED: 'APPROVED',
  REJECTED: 'REJECTED',
} as const;
export type ApprovalStatus = (typeof ApprovalStatus)[keyof typeof ApprovalStatus];

// ============================================================================
// Workspace Interfaces
// ============================================================================

export interface WorkspaceMember {
  id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: WorkspaceRole;
  joined_at: string;
}

export interface WorkspaceDetail {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  avatar_color: string;
  is_private: boolean;
  is_archived: boolean;
  member_count: number;
  current_user_role: WorkspaceRole;
  members: WorkspaceMember[];
  created_at: string;
}

export interface WorkspaceSummary {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  avatar_color: string;
  is_private: boolean;
  member_count: number;
  current_user_role: WorkspaceRole;
  created_at: string;
}

export interface WorkspaceCreatePayload {
  name: string;
  slug: string;
  description?: string;
  avatar_color?: string;
  is_private?: boolean;
}

export interface WorkspaceAddMemberPayload {
  user_id: string;
  role: WorkspaceRole;
}

export interface WorkspaceDashboardData {
  workspace_id: string;
  active_members_count: number;
  active_projects_count: number;
  recent_documents_count: number;
  open_discussions_count: number;
  pending_approvals_count: number;
  recent_activities: Array<{
    id: string;
    activity_type: string;
    actor_id: string;
    description: string;
    created_at: string;
  }>;
  recent_discussions: Array<{
    id: string;
    document_id: string;
    content: string;
    status: string;
    created_at: string;
  }>;
}

// ============================================================================
// Shared Project Interfaces
// ============================================================================

export interface SharedProject {
  id: string;
  workspace_id: string;
  name: string;
  description?: string | null;
  created_at: string;
}

export interface SharedProjectCreatePayload {
  workspace_id: string;
  name: string;
  description?: string;
}

// ============================================================================
// Discussion & Comment Interfaces
// ============================================================================

export interface DocumentComment {
  id: string;
  document_id: string;
  workspace_id?: string | null;
  parent_comment_id?: string | null;
  author_id: string;
  author_name: string;
  content: string;
  page_number?: number | null;
  highlight_text?: string | null;
  status: CommentStatus;
  resolved_by_id?: string | null;
  resolved_at?: string | null;
  mentions: string[];
  replies: DocumentComment[];
  created_at: string;
}

export interface CommentCreatePayload {
  document_id: string;
  workspace_id?: string;
  content: string;
  page_number?: number;
  highlight_text?: string;
}

export interface CommentReplyPayload {
  parent_comment_id: string;
  content: string;
}

export interface MentionSendPayload {
  mentioned_user_id: string;
  document_id: string;
  workspace_id?: string;
  context_text: string;
}

// ============================================================================
// Presence & Activity Interfaces
// ============================================================================

export interface PresenceCollaborator {
  user_id: string;
  full_name: string;
  email: string;
  status: PresenceStatus;
  document_id?: string | null;
  last_seen_at: string;
}

export interface PresenceHeartbeatPayload {
  workspace_id: string;
  status: PresenceStatus;
  document_id?: string;
}

export interface ActivityItem {
  id: string;
  activity_type: ActivityType;
  actor_id: string;
  actor_name: string;
  entity_id: string;
  entity_type: string;
  entity_title?: string | null;
  description: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

// ============================================================================
// Version History Interfaces
// ============================================================================

export interface CollaborationVersionItem {
  version_id: string;
  version_number: number;
  editor_id: string;
  editor_name: string;
  change_summary: string;
  file_size_bytes?: number | null;
  checksum?: string | null;
  approval_status: ApprovalStatus;
  created_at: string;
}

export interface VersionCreatePayload {
  document_id: string;
  change_summary: string;
  file_path?: string;
  file_size_bytes?: number;
  checksum?: string;
  approval_status?: ApprovalStatus;
}

export interface VersionRollbackPayload {
  document_id: string;
  target_version_number: number;
}

// ============================================================================
// AI Collaboration Interfaces
// ============================================================================

export interface KeyDecision {
  decision: string;
  agreed_by: string[];
  timestamp: string;
}

export interface ActionItem {
  action: string;
  assignee?: string | null;
  deadline?: string | null;
  confidence: number;
}

export interface SuggestedDocument {
  document_id: string;
  title: string;
  department: string;
  relevance_score: number;
  reason: string;
}

export interface AIDiscussionSummary {
  document_id: string;
  executive_summary: string;
  key_decisions: KeyDecision[];
  action_items: ActionItem[];
  unresolved_questions: string[];
  suggested_documents: SuggestedDocument[];
  processing_time_ms: number;
}
