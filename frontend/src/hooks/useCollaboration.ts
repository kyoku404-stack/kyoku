/**
 * Custom React hook for Real-Time Collaboration & Team Workspaces.
 * Manages workspaces, discussions, presence, activity feed, version history, and AI assistance.
 *
 * Specification: devdocs/p3/p3.2.txt & docs/api/api-contract.md Section 14
 * Author: Member 3 (Frontend & UI Lead)
 */

import { useCallback, useEffect, useState } from 'react';
import { collaborationService } from '@/services/collaborationService';
import type {
  ActivityItem,
  AIDiscussionSummary,
  CommentCreatePayload,
  CommentReplyPayload,
  DocumentComment,
  CollaborationVersionItem,
  MentionSendPayload,
  PresenceCollaborator,
  PresenceStatus,
  VersionCreatePayload,
  VersionRollbackPayload,
  WorkspaceCreatePayload,
  WorkspaceDashboardData,
  WorkspaceDetail,
  WorkspaceSummary,
} from '@/types/collaboration';

export function useCollaboration(initialWorkspaceId?: string) {
  const [workspaces, setWorkspaces] = useState<WorkspaceSummary[]>([]);
  const [currentWorkspace, setCurrentWorkspace] = useState<WorkspaceDetail | null>(null);
  const [dashboardData, setDashboardData] = useState<WorkspaceDashboardData | null>(null);
  const [comments, setComments] = useState<DocumentComment[]>([]);
  const [presence, setPresence] = useState<PresenceCollaborator[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [versions, setVersions] = useState<CollaborationVersionItem[]>([]);
  const [aiSummary, setAiSummary] = useState<AIDiscussionSummary | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [isSummarizing, setIsSummarizing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all workspaces
  const fetchWorkspaces = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await collaborationService.listWorkspaces();
      if (res.data) {
        setWorkspaces(res.data.workspaces || []);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch workspaces';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  // Select and load specific workspace
  const selectWorkspace = useCallback(async (workspaceId: string) => {
    try {
      setLoading(true);
      setError(null);
      const [detailRes, dashRes] = await Promise.all([
        collaborationService.getWorkspace(workspaceId),
        collaborationService.getWorkspaceDashboard(workspaceId),
      ]);
      if (detailRes.data) {
        setCurrentWorkspace(detailRes.data);
      }
      if (dashRes.data) {
        setDashboardData(dashRes.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load workspace';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  // Create workspace
  const createWorkspace = useCallback(async (payload: WorkspaceCreatePayload) => {
    try {
      setLoading(true);
      setError(null);
      const res = await collaborationService.createWorkspace(payload);
      if (res.data) {
        await fetchWorkspaces();
        setCurrentWorkspace(res.data);
      }
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create workspace';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchWorkspaces]);

  // Load comments for document
  const fetchComments = useCallback(async (documentId: string) => {
    try {
      setError(null);
      const res = await collaborationService.getDocumentComments(documentId);
      if (res.data) {
        setComments(res.data.comments || []);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load comments';
      setError(msg);
    }
  }, []);

  // Add root comment
  const addComment = useCallback(async (payload: CommentCreatePayload) => {
    try {
      setError(null);
      const res = await collaborationService.createComment(payload);
      if (res.data) {
        await fetchComments(payload.document_id);
      }
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to post comment';
      setError(msg);
      throw err;
    }
  }, [fetchComments]);

  // Reply to comment
  const replyComment = useCallback(async (documentId: string, payload: CommentReplyPayload) => {
    try {
      setError(null);
      const res = await collaborationService.replyComment(payload);
      if (res.data) {
        await fetchComments(documentId);
      }
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to post reply';
      setError(msg);
      throw err;
    }
  }, [fetchComments]);

  // Resolve comment
  const resolveComment = useCallback(async (documentId: string, commentId: string) => {
    try {
      setError(null);
      const res = await collaborationService.resolveComment(commentId);
      if (res.data) {
        await fetchComments(documentId);
      }
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to resolve comment';
      setError(msg);
      throw err;
    }
  }, [fetchComments]);

  // Presence heartbeat & roster query
  const sendPresence = useCallback(async (
    workspaceId: string,
    status: PresenceStatus,
    documentId?: string
  ) => {
    try {
      await collaborationService.sendPresenceHeartbeat({
        workspace_id: workspaceId,
        status,
        document_id: documentId,
      });
      const rosterRes = await collaborationService.getWorkspacePresence(workspaceId);
      if (rosterRes.data) {
        setPresence(rosterRes.data.collaborators || []);
      }
    } catch (err: unknown) {
      // Ephemeral error suppressed to avoid UI stutter
      console.warn('Presence update error:', err);
    }
  }, []);

  // Send mention
  const sendMention = useCallback(async (payload: MentionSendPayload) => {
    try {
      const res = await collaborationService.sendMention(payload);
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to send mention';
      setError(msg);
      throw err;
    }
  }, []);

  // Activity Feed
  const fetchActivities = useCallback(async (workspaceId: string, activityType?: string) => {
    try {
      const res = await collaborationService.getActivityFeed(workspaceId, activityType);
      if (res.data) {
        setActivities(res.data.activities || []);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load activity feed';
      setError(msg);
    }
  }, []);

  // Version History
  const fetchVersions = useCallback(async (documentId: string) => {
    try {
      const res = await collaborationService.getVersionHistory(documentId);
      if (res.data) {
        setVersions(res.data.versions || []);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load version history';
      setError(msg);
    }
  }, []);

  const createCheckpoint = useCallback(async (payload: VersionCreatePayload) => {
    try {
      const res = await collaborationService.createVersionCheckpoint(payload);
      if (res.data) {
        await fetchVersions(payload.document_id);
      }
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create version checkpoint';
      setError(msg);
      throw err;
    }
  }, [fetchVersions]);

  const rollbackVersion = useCallback(async (payload: VersionRollbackPayload) => {
    try {
      const res = await collaborationService.rollbackVersion(payload);
      if (res.data) {
        await fetchVersions(payload.document_id);
      }
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to rollback version';
      setError(msg);
      throw err;
    }
  }, [fetchVersions]);

  // AI Discussion Summarizer
  const summarizeDiscussion = useCallback(async (documentId: string) => {
    try {
      setIsSummarizing(true);
      setError(null);
      const res = await collaborationService.summarizeDiscussion(documentId);
      if (res.data) {
        setAiSummary(res.data);
      }
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to summarize discussion';
      setError(msg);
      throw err;
    } finally {
      setIsSummarizing(false);
    }
  }, []);

  useEffect(() => {
    fetchWorkspaces();
    if (initialWorkspaceId) {
      selectWorkspace(initialWorkspaceId);
    }
  }, [fetchWorkspaces, selectWorkspace, initialWorkspaceId]);

  return {
    workspaces,
    currentWorkspace,
    dashboardData,
    comments,
    presence,
    activities,
    versions,
    aiSummary,
    loading,
    isSummarizing,
    error,
    fetchWorkspaces,
    selectWorkspace,
    createWorkspace,
    fetchComments,
    addComment,
    replyComment,
    resolveComment,
    sendPresence,
    sendMention,
    fetchActivities,
    fetchVersions,
    createCheckpoint,
    rollbackVersion,
    summarizeDiscussion,
  };
}
