/**
 * Phase 3.2 Real-Time Collaboration & Team Workspaces Component Tests.
 * Author: Member 3 (Frontend & UI Lead)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import {
  WorkspaceHeader,
  WorkspaceGrid,
  CreateWorkspaceModal,
  PresenceIndicator,
  ActivityFeedTimeline,
  VersionHistoryDrawer,
} from '@/features/collaboration';
import {
  WorkspaceRole,
  PresenceStatus,
  ActivityType,
  ApprovalStatus,
} from '@/types/collaboration';

describe('Phase 3.2 Collaboration Feature Components', () => {
  it('WorkspaceHeader renders workspace name and action triggers', () => {
    const mockWs = {
      id: 'ws-1',
      name: 'Engineering Workspace',
      slug: 'engineering-workspace',
      description: 'Core engineering RFCs',
      avatar_color: '#4F46E5',
      is_private: false,
      is_archived: false,
      member_count: 5,
      current_user_role: WorkspaceRole.ADMIN,
      members: [],
      created_at: '2026-10-28T09:00:00Z',
    };

    const mockDashboard = {
      workspace_id: 'ws-1',
      active_members_count: 5,
      active_projects_count: 3,
      recent_documents_count: 12,
      open_discussions_count: 4,
      pending_approvals_count: 1,
      recent_activities: [],
      recent_discussions: [],
    };

    const onCreate = vi.fn();
    const onRefresh = vi.fn();
    const onToggle = vi.fn();

    render(
      <WorkspaceHeader
        workspace={mockWs}
        dashboard={mockDashboard}
        collaborators={[{ user_id: 'u-1', full_name: 'Alice', email: 'a@co.com', status: PresenceStatus.ONLINE, last_seen_at: '2026-10-28T09:00:00Z' }]}
        onCreateClick={onCreate}
        onRefreshClick={onRefresh}
        onToggleActivityFeed={onToggle}
        isLoading={false}
      />
    );

    expect(screen.getByText('Engineering Workspace')).toBeInTheDocument();
    expect(screen.getByText('Shared')).toBeInTheDocument();
    expect(screen.getByText('New Workspace')).toBeInTheDocument();

    fireEvent.click(screen.getByText('New Workspace'));
    expect(onCreate).toHaveBeenCalledTimes(1);
  });

  it('WorkspaceGrid renders list and filters by search query', () => {
    const workspaces = [
      {
        id: 'ws-1',
        name: 'Human Resources',
        slug: 'hr-ops',
        avatar_color: '#EC4899',
        is_private: true,
        member_count: 4,
        current_user_role: WorkspaceRole.ADMIN,
        created_at: '2026-10-28T09:00:00Z',
      },
      {
        id: 'ws-2',
        name: 'Security Core',
        slug: 'security-core',
        avatar_color: '#4F46E5',
        is_private: false,
        member_count: 8,
        current_user_role: WorkspaceRole.MEMBER,
        created_at: '2026-10-28T09:00:00Z',
      },
    ];

    const onSelect = vi.fn();
    render(
      <WorkspaceGrid
        workspaces={workspaces}
        activeWorkspaceId="ws-1"
        onSelectWorkspace={onSelect}
        onCreateClick={vi.fn()}
      />
    );

    expect(screen.getByText('Human Resources')).toBeInTheDocument();
    expect(screen.getByText('Security Core')).toBeInTheDocument();

    // Filter
    const searchInput = screen.getByPlaceholderText('Search workspaces...');
    fireEvent.change(searchInput, { target: { value: 'Security' } });

    expect(screen.queryByText('Human Resources')).not.toBeInTheDocument();
    expect(screen.getByText('Security Core')).toBeInTheDocument();
  });

  it('CreateWorkspaceModal submits with valid payload', async () => {
    const onSubmit = vi.fn().mockResolvedValueOnce({});
    const onClose = vi.fn();

    render(
      <CreateWorkspaceModal
        isOpen={true}
        onClose={onClose}
        onSubmit={onSubmit}
      />
    );

    expect(screen.getByText('Create Team Workspace')).toBeInTheDocument();

    const nameInput = screen.getByPlaceholderText('e.g. Human Resources, Engineering, Legal');
    fireEvent.change(nameInput, { target: { value: 'Product Management' } });

    const submitBtn = screen.getByText('Create Workspace');
    fireEvent.click(submitBtn);

    expect(onSubmit).toHaveBeenCalled();
  });

  it('PresenceIndicator displays status', () => {
    render(<PresenceIndicator currentStatus={PresenceStatus.EDITING} />);
    expect(screen.getByText('editing')).toBeInTheDocument();
  });

  it('ActivityFeedTimeline renders activities with filters', () => {
    const activities = [
      {
        id: 'act-1',
        activity_type: ActivityType.COMMENT_ADDED,
        actor_id: 'u-1',
        actor_name: 'Bob',
        entity_id: 'c-1',
        entity_type: 'comment',
        description: 'Bob added a comment on Employee Handbook.pdf',
        created_at: '2026-10-28T10:15:00Z',
      },
    ];

    render(<ActivityFeedTimeline activities={activities} workspaceName="Engineering" />);
    expect(screen.getByText(/Bob added a comment/i)).toBeInTheDocument();
  });

  it('VersionHistoryDrawer renders version history lineage', () => {
    const versions = [
      {
        version_id: 'v-1',
        version_number: 1,
        editor_id: 'u-1',
        editor_name: 'Alice',
        change_summary: 'Initial revision draft',
        approval_status: ApprovalStatus.APPROVED,
        created_at: '2026-10-28T09:00:00Z',
      },
    ];

    render(
      <VersionHistoryDrawer
        isOpen={true}
        onClose={vi.fn()}
        documentId="doc-1"
        documentTitle="Employee Handbook.pdf"
        versions={versions}
        onCreateVersion={vi.fn()}
        onRollback={vi.fn()}
      />
    );

    expect(screen.getByText('Initial revision draft')).toBeInTheDocument();
    expect(screen.getByText('v1')).toBeInTheDocument();
  });
});
