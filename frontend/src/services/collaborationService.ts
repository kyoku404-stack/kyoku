/**
 * Phase 3.2 Real-Time Collaboration & Team Workspaces API Client Service.
 * Implements communication with all Phase 3.2 REST endpoints:
 * - Workspaces (/workspaces/create, /workspaces/list, /workspaces/{id}, etc.)
 * - Shared Projects (/projects/create)
 * - Document Comments (/comments/create, /comments/reply, /comments/document/{id}, /comments/{id}/resolve)
 * - Mentions & Presence (/mentions/send, /presence/heartbeat, /presence/{workspace_id})
 * - Activity Feed (/activity/feed)
 * - Version History (/version/history/{id}, /version/create, /version/rollback)
 * - AI Discussion Summarizer (/collaboration/discussions/{document_id}/summary)
 *
 * Specification: docs/api/api-contract.md Section 14 & devdocs/p3/p3.2.txt
 * Author: Member 3 (Frontend & UI Lead)
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  ActivityItem,
  AIDiscussionSummary,
  CommentCreatePayload,
  CommentReplyPayload,
  DocumentComment,
  CollaborationVersionItem,
  MentionSendPayload,
  PresenceCollaborator,
  PresenceHeartbeatPayload,
  SharedProject,
  SharedProjectCreatePayload,
  VersionCreatePayload,
  VersionRollbackPayload,
  WorkspaceAddMemberPayload,
  WorkspaceCreatePayload,
  WorkspaceDashboardData,
  WorkspaceDetail,
  WorkspaceMember,
  WorkspaceSummary,
} from '@/types/collaboration';

export const collaborationService = {
  // ==========================================================================
  // Workspace Operations
  // ==========================================================================

  async createWorkspace(
    payload: WorkspaceCreatePayload
  ): Promise<ApiResponse<WorkspaceDetail>> {
    const response = await apiClient.post<ApiResponse<WorkspaceDetail>>(
      '/workspaces/create',
      payload
    );
    return response.data;
  },

  async listWorkspaces(): Promise<
    ApiResponse<{ total: number; workspaces: WorkspaceSummary[] }>
  > {
    const response = await apiClient.get<
      ApiResponse<{ total: number; workspaces: WorkspaceSummary[] }>
    >('/workspaces/list');
    return response.data;
  },

  async getWorkspace(
    workspaceId: string
  ): Promise<ApiResponse<WorkspaceDetail>> {
    const response = await apiClient.get<ApiResponse<WorkspaceDetail>>(
      `/workspaces/${workspaceId}`
    );
    return response.data;
  },

  async addWorkspaceMember(
    workspaceId: string,
    payload: WorkspaceAddMemberPayload
  ): Promise<ApiResponse<WorkspaceMember>> {
    const response = await apiClient.post<ApiResponse<WorkspaceMember>>(
      `/workspaces/${workspaceId}/members`,
      payload
    );
    return response.data;
  },

  async getWorkspaceDashboard(
    workspaceId: string
  ): Promise<ApiResponse<WorkspaceDashboardData>> {
    const response = await apiClient.get<ApiResponse<WorkspaceDashboardData>>(
      `/workspaces/${workspaceId}/dashboard`
    );
    return response.data;
  },

  // ==========================================================================
  // Shared Projects
  // ==========================================================================

  async createSharedProject(
    payload: SharedProjectCreatePayload
  ): Promise<ApiResponse<SharedProject>> {
    const response = await apiClient.post<ApiResponse<SharedProject>>(
      '/projects/create',
      payload
    );
    return response.data;
  },

  // ==========================================================================
  // Document Discussions & Comments
  // ==========================================================================

  async createComment(
    payload: CommentCreatePayload
  ): Promise<ApiResponse<DocumentComment>> {
    const response = await apiClient.post<ApiResponse<DocumentComment>>(
      '/comments/create',
      payload
    );
    return response.data;
  },

  async replyComment(
    payload: CommentReplyPayload
  ): Promise<ApiResponse<DocumentComment>> {
    const response = await apiClient.post<ApiResponse<DocumentComment>>(
      '/comments/reply',
      payload
    );
    return response.data;
  },

  async getDocumentComments(
    documentId: string
  ): Promise<
    ApiResponse<{
      document_id: string;
      total_comments: number;
      comments: DocumentComment[];
    }>
  > {
    const response = await apiClient.get<
      ApiResponse<{
        document_id: string;
        total_comments: number;
        comments: DocumentComment[];
      }>
    >(`/comments/document/${documentId}`);
    return response.data;
  },

  async resolveComment(
    commentId: string
  ): Promise<
    ApiResponse<{
      id: string;
      status: string;
      resolved_by_id?: string;
      resolved_at?: string;
    }>
  > {
    const response = await apiClient.post<
      ApiResponse<{
        id: string;
        status: string;
        resolved_by_id?: string;
        resolved_at?: string;
      }>
    >(`/comments/${commentId}/resolve`);
    return response.data;
  },

  // ==========================================================================
  // Mentions & Presence
  // ==========================================================================

  async sendMention(
    payload: MentionSendPayload
  ): Promise<ApiResponse<{ notification_id: string; delivered: boolean }>> {
    const response = await apiClient.post<
      ApiResponse<{ notification_id: string; delivered: boolean }>
    >('/mentions/send', payload);
    return response.data;
  },

  async sendPresenceHeartbeat(
    payload: PresenceHeartbeatPayload
  ): Promise<ApiResponse<{ received: boolean }>> {
    const response = await apiClient.post<ApiResponse<{ received: boolean }>>(
      '/presence/heartbeat',
      payload
    );
    return response.data;
  },

  async getWorkspacePresence(
    workspaceId: string
  ): Promise<
    ApiResponse<{ workspace_id: string; collaborators: PresenceCollaborator[] }>
  > {
    const response = await apiClient.get<
      ApiResponse<{ workspace_id: string; collaborators: PresenceCollaborator[] }>
    >(`/presence/${workspaceId}`);
    return response.data;
  },

  // ==========================================================================
  // Activity Feed
  // ==========================================================================

  async getActivityFeed(
    workspaceId: string,
    activityType?: string,
    limit: number = 30
  ): Promise<
    ApiResponse<{ workspace_id: string; activities: ActivityItem[] }>
  > {
    const params: Record<string, string | number> = {
      workspace_id: workspaceId,
      limit,
    };
    if (activityType) {
      params.activity_type = activityType;
    }
    const response = await apiClient.get<
      ApiResponse<{ workspace_id: string; activities: ActivityItem[] }>
    >('/activity/feed', { params });
    return response.data;
  },

  // ==========================================================================
  // Version History & Rollback
  // ==========================================================================

  async getVersionHistory(
    documentId: string
  ): Promise<
    ApiResponse<{
      document_id: string;
      total_versions: number;
      versions: CollaborationVersionItem[];
    }>
  > {
    const response = await apiClient.get<
      ApiResponse<{
        document_id: string;
        total_versions: number;
        versions: CollaborationVersionItem[];
      }>
    >(`/version/history/${documentId}`);
    return response.data;
  },

  async createVersionCheckpoint(
    payload: VersionCreatePayload
  ): Promise<ApiResponse<CollaborationVersionItem>> {
    const response = await apiClient.post<ApiResponse<CollaborationVersionItem>>(
      '/version/create',
      payload
    );
    return response.data;
  },

  async rollbackVersion(
    payload: VersionRollbackPayload
  ): Promise<ApiResponse<CollaborationVersionItem>> {
    const response = await apiClient.post<ApiResponse<CollaborationVersionItem>>(
      '/version/rollback',
      payload
    );
    return response.data;
  },

  // ==========================================================================
  // AI Collaboration Assistant
  // ==========================================================================

  async summarizeDiscussion(
    documentId: string
  ): Promise<ApiResponse<AIDiscussionSummary>> {
    const response = await apiClient.post<ApiResponse<AIDiscussionSummary>>(
      `/collaboration/discussions/${documentId}/summary`
    );
    return response.data;
  },
};
