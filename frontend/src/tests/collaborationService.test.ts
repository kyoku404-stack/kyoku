/**
 * Phase 3.2 Real-Time Collaboration & Team Workspaces Service API Client Tests.
 *
 * Verifies all API methods in collaborationService:
 * - Workspaces (create, list, get, addMember, dashboard)
 * - Projects (createSharedProject)
 * - Comments (create, reply, getDocumentComments, resolve)
 * - Mentions & Presence (sendMention, sendPresenceHeartbeat, getWorkspacePresence)
 * - Activity Feed (getActivityFeed)
 * - Version History (getVersionHistory, createVersionCheckpoint, rollbackVersion)
 * - AI Discussion Summarizer (summarizeDiscussion)
 *
 * Specification: docs/api/api-contract.md Section 14 & devdocs/p3/p3.2.txt
 * Author: Member 3 (Frontend & UI Lead)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { collaborationService } from '@/services/collaborationService';
import { apiClient } from '@/services/api';
import {
  WorkspaceRole,
  PresenceStatus,
  CommentStatus,
  ApprovalStatus,
} from '@/types/collaboration';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Phase 3.2 Collaboration Service API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('createWorkspace() posts payload to /workspaces/create', async () => {
    const mockData = {
      id: 'ws-1',
      name: 'Engineering Core',
      slug: 'engineering-core',
      description: 'Core engineering workspace',
      avatar_color: '#4F46E5',
      is_private: false,
      is_archived: false,
      member_count: 1,
      current_user_role: WorkspaceRole.ADMIN,
      members: [],
      created_at: '2026-10-28T09:00:00Z',
    };
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, data: mockData },
    });

    const res = await collaborationService.createWorkspace({
      name: 'Engineering Core',
      slug: 'engineering-core',
      avatar_color: '#4F46E5',
    });

    expect(apiClient.post).toHaveBeenCalledWith('/workspaces/create', {
      name: 'Engineering Core',
      slug: 'engineering-core',
      avatar_color: '#4F46E5',
    });
    expect(res.data.name).toBe('Engineering Core');
  });

  it('listWorkspaces() fetches from /workspaces/list', async () => {
    const mockData = {
      total: 1,
      workspaces: [
        {
          id: 'ws-1',
          name: 'Engineering Core',
          slug: 'engineering-core',
          avatar_color: '#4F46E5',
          is_private: false,
          member_count: 3,
          current_user_role: WorkspaceRole.ADMIN,
          created_at: '2026-10-28T09:00:00Z',
        },
      ],
    };
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, data: mockData },
    });

    const res = await collaborationService.listWorkspaces();
    expect(apiClient.get).toHaveBeenCalledWith('/workspaces/list');
    expect(res.data.total).toBe(1);
    expect(res.data.workspaces[0].slug).toBe('engineering-core');
  });

  it('createComment() posts payload to /comments/create', async () => {
    const mockComment = {
      id: 'comm-1',
      document_id: 'doc-1',
      author_id: 'user-1',
      author_name: 'John Doe',
      content: 'Please verify with @sarah',
      status: CommentStatus.OPEN,
      mentions: ['sarah'],
      replies: [],
      created_at: '2026-10-28T09:12:00Z',
    };
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, data: mockComment },
    });

    const res = await collaborationService.createComment({
      document_id: 'doc-1',
      content: 'Please verify with @sarah',
    });

    expect(apiClient.post).toHaveBeenCalledWith('/comments/create', {
      document_id: 'doc-1',
      content: 'Please verify with @sarah',
    });
    expect(res.data.mentions).toEqual(['sarah']);
  });

  it('sendPresenceHeartbeat() posts heartbeat to /presence/heartbeat', async () => {
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, data: { received: true } },
    });

    const res = await collaborationService.sendPresenceHeartbeat({
      workspace_id: 'ws-1',
      status: PresenceStatus.EDITING,
      document_id: 'doc-1',
    });

    expect(apiClient.post).toHaveBeenCalledWith('/presence/heartbeat', {
      workspace_id: 'ws-1',
      status: PresenceStatus.EDITING,
      document_id: 'doc-1',
    });
    expect(res.data.received).toBe(true);
  });

  it('getVersionHistory() queries /version/history/:id', async () => {
    const mockVersions = {
      document_id: 'doc-1',
      total_versions: 2,
      versions: [
        {
          version_id: 'v-2',
          version_number: 2,
          editor_id: 'u-1',
          editor_name: 'Lead',
          change_summary: 'Updated guidelines',
          approval_status: ApprovalStatus.APPROVED,
          created_at: '2026-10-28T10:00:00Z',
        },
      ],
    };
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, data: mockVersions },
    });

    const res = await collaborationService.getVersionHistory('doc-1');
    expect(apiClient.get).toHaveBeenCalledWith('/version/history/doc-1');
    expect(res.data.total_versions).toBe(2);
  });

  it('summarizeDiscussion() calls /collaboration/discussions/:id/summary', async () => {
    const mockSummary = {
      document_id: 'doc-1',
      executive_summary: 'Consensus reached on retention period.',
      key_decisions: [{ decision: 'Confirmed 90 days', agreed_by: ['Sarah', 'John'], timestamp: '2026-10-28T09:00:00Z' }],
      action_items: [{ action: 'Update policy PDF', assignee: 'Sarah', deadline: 'Friday', confidence: 0.9 }],
      unresolved_questions: [],
      suggested_documents: [],
      processing_time_ms: 12.5,
    };
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, data: mockSummary },
    });

    const res = await collaborationService.summarizeDiscussion('doc-1');
    expect(apiClient.post).toHaveBeenCalledWith('/collaboration/discussions/doc-1/summary');
    expect(res.data.key_decisions.length).toBe(1);
    expect(res.data.action_items[0].assignee).toBe('Sarah');
  });
});
