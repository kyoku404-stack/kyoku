/**
 * KEEP Enterprise Platform — Connector Feature Components Unit Tests (Phase 3.1).
 *
 * Verifies UI components:
 * 1. ConnectorMetricsBanner
 * 2. ConnectorGrid
 * 3. RegisterConnectorModal
 * 4. AuthenticateModal
 * 5. ConnectorStatusDrawer
 * 6. SyncHistoryTable
 *
 * Specification: docs/api/api-contract.md Section 13 & devdocs/p3/p3.1.txt
 * Author: Member 3 (Frontend & UI Lead)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import {
  ConnectorMetricsBanner,
  ConnectorGrid,
  RegisterConnectorModal,
  AuthenticateModal,
  ConnectorStatusDrawer,
  SyncHistoryTable,
} from '@/features/connectors';
import {
  AuthType,
  ConnectorStatus,
  PlatformCategory,
  PlatformType,
  SyncJobStatus,
  type ConnectorListItem,
  type ConnectorStatusResponse,
  type ConnectorSyncLogItem,
} from '@/types/connector';

describe('Phase 3.1 Connector UI Components', () => {
  it('ConnectorMetricsBanner renders title, metrics KPIs, and handles clicks', () => {
    const onRegisterClick = vi.fn();
    const onRefreshClick = vi.fn();

    const metrics = {
      totalConnectors: 5,
      healthyCount: 4,
      syncingCount: 1,
      errorCount: 0,
      totalDocsSynced: 1250,
    };

    render(
      <ConnectorMetricsBanner
        metrics={metrics}
        onRegisterClick={onRegisterClick}
        onRefreshClick={onRefreshClick}
        isLoading={false}
      />
    );

    expect(screen.getByText('Enterprise Integrations')).toBeInTheDocument();
    expect(screen.getByText('Phase 3.1')).toBeInTheDocument();
    expect(screen.getByText('1,250')).toBeInTheDocument();

    const addBtn = screen.getByText('Connect Platform');
    fireEvent.click(addBtn);
    expect(onRegisterClick).toHaveBeenCalledTimes(1);

    const refreshBtn = screen.getByTitle('Refresh connectors');
    fireEvent.click(refreshBtn);
    expect(onRefreshClick).toHaveBeenCalledTimes(1);
  });

  it('ConnectorGrid renders connectors, badges, search bar, and action triggers', () => {
    const mockConnectors: ConnectorListItem[] = [
      {
        id: 'conn-slack',
        name: 'Slack #general',
        platform_type: PlatformType.SLACK,
        platform_category: PlatformCategory.COMMUNICATION,
        auth_type: AuthType.OAUTH2,
        status: ConnectorStatus.CONNECTED,
        total_documents_synced: 840,
        last_sync_at: '2026-10-28T01:00:00Z',
        last_sync_status: 'SUCCESS',
        created_at: '2026-10-28T00:00:00Z',
      },
      {
        id: 'conn-github',
        name: 'Backend Core Repo',
        platform_type: PlatformType.GITHUB,
        platform_category: PlatformCategory.DEVELOPMENT,
        auth_type: AuthType.API_KEY,
        status: ConnectorStatus.CONFIGURED,
        total_documents_synced: 0,
        last_sync_at: null,
        last_sync_status: null,
        created_at: '2026-10-28T00:00:00Z',
      },
    ];

    const onCategoryChange = vi.fn();
    const onStatusChange = vi.fn();
    const onSearchChange = vi.fn();
    const onSync = vi.fn();
    const onInspectStatus = vi.fn();
    const onAuthenticate = vi.fn();
    const onRemove = vi.fn();
    const onRegisterClick = vi.fn();

    render(
      <ConnectorGrid
        connectors={mockConnectors}
        isLoading={false}
        categoryFilter="ALL"
        statusFilter="ALL"
        searchQuery=""
        onCategoryChange={onCategoryChange}
        onStatusChange={onStatusChange}
        onSearchChange={onSearchChange}
        onSync={onSync}
        onInspectStatus={onInspectStatus}
        onAuthenticate={onAuthenticate}
        onRemove={onRemove}
        onRegisterClick={onRegisterClick}
      />
    );

    expect(screen.getByText('Slack #general')).toBeInTheDocument();
    expect(screen.getByText('Backend Core Repo')).toBeInTheDocument();
    expect(screen.getAllByText('Connected').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Configured').length).toBeGreaterThanOrEqual(1);

    const syncButtons = screen.getAllByTitle('Run manual sync');
    fireEvent.click(syncButtons[0]);
    expect(onSync).toHaveBeenCalledWith('conn-slack');

    const statusButtons = screen.getAllByTitle('View health telemetry');
    fireEvent.click(statusButtons[0]);
    expect(onInspectStatus).toHaveBeenCalledWith('conn-slack');
  });

  it('RegisterConnectorModal handles form submission and validation', () => {
    const onClose = vi.fn();
    const onSubmit = vi.fn().mockResolvedValue(true);

    render(
      <RegisterConnectorModal
        isOpen={true}
        onClose={onClose}
        onSubmit={onSubmit}
      />
    );

    expect(screen.getByText('Connect External Platform')).toBeInTheDocument();

    const nameInput = screen.getByPlaceholderText(/Corporate Google Drive/i);
    fireEvent.change(nameInput, { target: { value: 'Product Documentation' } });

    const submitBtn = screen.getByText('Register Connector');
    fireEvent.click(submitBtn);

    expect(onSubmit).toHaveBeenCalled();
  });

  it('AuthenticateModal renders authentication inputs and triggers auth flow', () => {
    const onClose = vi.fn();
    const onSubmit = vi.fn().mockResolvedValue(true);

    const connector: ConnectorListItem = {
      id: 'conn-jira',
      name: 'Corporate Jira',
      platform_type: PlatformType.JIRA,
      platform_category: PlatformCategory.PROJECT_MANAGEMENT,
      auth_type: AuthType.API_KEY,
      status: ConnectorStatus.CONFIGURED,
      total_documents_synced: 0,
      last_sync_at: null,
      last_sync_status: null,
      created_at: '2026-10-28T00:00:00Z',
    };

    render(
      <AuthenticateModal
        isOpen={true}
        connector={connector}
        onClose={onClose}
        onSubmit={onSubmit}
      />
    );

    expect(screen.getByText('Authenticate Connector')).toBeInTheDocument();
    expect(screen.getByText(/Corporate Jira/i)).toBeInTheDocument();

    const keyInput = screen.getByPlaceholderText(/Paste external platform access token or API key/i);
    fireEvent.change(keyInput, { target: { value: 'jira_secret_token_12345' } });

    const authBtn = screen.getByText('Save & Authenticate');
    fireEvent.click(authBtn);

    expect(onSubmit).toHaveBeenCalledWith({
      connector_id: 'conn-jira',
      auth_type: 'OAUTH2',
      credentials: {
        access_token: 'jira_secret_token_12345',
        expires_in: 3600,
      },
    });
  });

  it('ConnectorStatusDrawer displays live metrics and health indicators', () => {
    const onClose = vi.fn();
    const onTriggerSync = vi.fn();

    const statusData: ConnectorStatusResponse = {
      id: 'conn-1',
      name: 'Production Confluence',
      platform_type: PlatformType.CONFLUENCE,
      status: ConnectorStatus.CONNECTED,
      last_sync_at: '2026-10-28T01:30:00Z',
      last_sync_status: 'SUCCESS',
      total_documents_synced: 412,
      active_sync_job: null,
      health_metrics: {
        api_latency_ms: 185.0,
        quota_used_pct: 14.5,
        success_rate_pct: 99.8,
      },
    };

    render(
      <ConnectorStatusDrawer
        isOpen={true}
        status={statusData}
        onClose={onClose}
        onTriggerSync={onTriggerSync}
        isSyncing={false}
      />
    );

    expect(screen.getByText('Production Confluence')).toBeInTheDocument();
    expect(screen.getByText('Health & SLA Telemetry')).toBeInTheDocument();
    expect(screen.getByText('185.0 ms')).toBeInTheDocument();
    expect(screen.getByText('99.8%')).toBeInTheDocument();

    const syncBtn = screen.getByText('Trigger Sync');
    fireEvent.click(syncBtn);
    expect(onTriggerSync).toHaveBeenCalledWith('conn-1');
  });

  it('SyncHistoryTable renders audit logs and handles refresh', () => {
    const onRefresh = vi.fn();

    const logs: ConnectorSyncLogItem[] = [
      {
        id: 'log-101',
        sync_job_id: 'job-501',
        connector_id: 'conn-1',
        external_document_id: 'doc-eng-001',
        document_title: 'Architecture Blueprint v3',
        source_url: 'https://notion.so/arch-blueprint',
        action_taken: 'ADDED',
        status: SyncJobStatus.SUCCESS,
        checksum: 'sha256-abcdef1234567890',
        created_at: '2026-10-28T01:45:00Z',
      },
      {
        id: 'log-102',
        sync_job_id: 'job-501',
        connector_id: 'conn-1',
        external_document_id: 'doc-eng-002',
        document_title: 'Sprint Retrospective',
        source_url: null,
        action_taken: 'UPDATED',
        status: SyncJobStatus.SUCCESS,
        checksum: 'sha256-0987654321fedcba',
        created_at: '2026-10-28T01:45:01Z',
      },
    ];

    render(<SyncHistoryTable logs={logs} isLoading={false} onRefresh={onRefresh} />);

    expect(screen.getByText('Architecture Blueprint v3')).toBeInTheDocument();
    expect(screen.getByText('Sprint Retrospective')).toBeInTheDocument();
    expect(screen.getByText('doc-eng-001')).toBeInTheDocument();
    expect(screen.getByText('Added')).toBeInTheDocument();
    expect(screen.getByText('Updated')).toBeInTheDocument();

    const refreshBtn = screen.getByTitle('Refresh audit logs');
    fireEvent.click(refreshBtn);
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});
