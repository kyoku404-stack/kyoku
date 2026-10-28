/**
 * KEEP Enterprise Platform — Connector Service API Client Unit Tests (Phase 3.1).
 *
 * Verifies all 7 REST endpoints in connectorService:
 * - POST /api/v1/connectors/register
 * - POST /api/v1/connectors/authenticate
 * - GET /api/v1/connectors/list
 * - POST /api/v1/connectors/sync
 * - GET /api/v1/connectors/status/{id}
 * - DELETE /api/v1/connectors/remove/{id}
 * - GET /api/v1/connectors/logs
 *
 * Specification: docs/api/api-contract.md Section 13 & devdocs/p3/p3.1.txt
 * Author: Member 3 (Frontend & UI Lead)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { connectorService } from '@/services/connectorService';
import { apiClient } from '@/services/api';
import {
  AuthType,
  ConnectorStatus,
  PlatformCategory,
  PlatformType,
  SyncJobStatus,
  SyncMode,
} from '@/types/connector';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('Phase 3.1 Connector Service API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('register() posts payload to /connectors/register', async () => {
    const mockResponse = {
      success: true,
      data: {
        id: 'conn-123',
        name: 'Engineering Notion',
        platform_type: PlatformType.NOTION,
        platform_category: PlatformCategory.DOCUMENTATION,
        auth_type: AuthType.API_KEY,
        status: ConnectorStatus.CONFIGURED,
        config: { sync_interval_minutes: 60 },
        total_documents_synced: 0,
        created_at: '2026-10-28T00:00:00Z',
      },
    };

    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ data: mockResponse });

    const payload = {
      name: 'Engineering Notion',
      platform_type: PlatformType.NOTION,
      platform_category: PlatformCategory.DOCUMENTATION,
      auth_type: AuthType.API_KEY,
      config: { sync_interval_minutes: 60 },
    };

    const res = await connectorService.register(payload);

    expect(apiClient.post).toHaveBeenCalledWith('/connectors/register', payload);
    expect(res.data.id).toBe('conn-123');
    expect(res.data.status).toBe(ConnectorStatus.CONFIGURED);
  });

  it('authenticate() posts credentials to /connectors/authenticate', async () => {
    const mockResponse = {
      success: true,
      data: {
        connector_id: 'conn-123',
        status: ConnectorStatus.CONNECTED,
        authenticated_at: '2026-10-28T00:05:00Z',
      },
    };

    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ data: mockResponse });

    const payload = {
      connector_id: 'conn-123',
      auth_type: AuthType.API_KEY,
      credentials: { api_key: 'secret_notion_key_xyz' },
    };

    const res = await connectorService.authenticate(payload);

    expect(apiClient.post).toHaveBeenCalledWith('/connectors/authenticate', payload);
    expect(res.data.connector_id).toBe('conn-123');
    expect(res.data.status).toBe(ConnectorStatus.CONNECTED);
  });

  it('list() retrieves connectors with optional filters', async () => {
    const mockResponse = {
      success: true,
      data: {
        total_connectors: 1,
        connectors: [
          {
            id: 'conn-1',
            name: 'Slack General',
            platform_type: PlatformType.SLACK,
            platform_category: PlatformCategory.COMMUNICATION,
            auth_type: AuthType.OAUTH2,
            status: ConnectorStatus.CONNECTED,
            total_documents_synced: 154,
            last_sync_at: '2026-10-28T01:00:00Z',
            last_sync_status: 'SUCCESS',
            created_at: '2026-10-28T00:00:00Z',
          },
        ],
      },
    };

    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ data: mockResponse });

    const res = await connectorService.list('COMMUNICATION', 'CONNECTED');

    expect(apiClient.get).toHaveBeenCalledWith(
      '/connectors/list?platform_category=COMMUNICATION&status=CONNECTED'
    );
    expect(res.data.total_connectors).toBe(1);
    expect(res.data.connectors[0].name).toBe('Slack General');
  });

  it('sync() dispatches manual synchronization request', async () => {
    const mockResponse = {
      success: true,
      data: {
        sync_job_id: 'job-999',
        connector_id: 'conn-1',
        sync_mode: SyncMode.INCREMENTAL,
        status: SyncJobStatus.RUNNING,
        started_at: '2026-10-28T01:05:00Z',
      },
    };

    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ data: mockResponse });

    const payload = {
      connector_id: 'conn-1',
      sync_mode: SyncMode.INCREMENTAL,
    };

    const res = await connectorService.sync(payload);

    expect(apiClient.post).toHaveBeenCalledWith('/connectors/sync', payload);
    expect(res.data.sync_job_id).toBe('job-999');
    expect(res.data.status).toBe(SyncJobStatus.RUNNING);
  });

  it('getStatus() retrieves connector telemetry and health metrics', async () => {
    const mockResponse = {
      success: true,
      data: {
        id: 'conn-1',
        name: 'GitHub Repo',
        platform_type: PlatformType.GITHUB,
        status: ConnectorStatus.CONNECTED,
        last_sync_at: '2026-10-28T01:00:00Z',
        last_sync_status: 'SUCCESS',
        total_documents_synced: 350,
        active_sync_job: null,
        health_metrics: {
          api_latency_ms: 120.5,
          quota_used_pct: 15.0,
          success_rate_pct: 99.5,
        },
      },
    };

    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ data: mockResponse });

    const res = await connectorService.getStatus('conn-1');

    expect(apiClient.get).toHaveBeenCalledWith('/connectors/status/conn-1');
    expect(res.data.status).toBe(ConnectorStatus.CONNECTED);
    expect(res.data.health_metrics.api_latency_ms).toBe(120.5);
  });

  it('remove() invokes DELETE on /connectors/remove/{id}', async () => {
    const mockResponse = {
      success: true,
      data: {
        id: 'conn-1',
        name: 'GitHub Repo',
        status: 'DISCONNECTED',
      },
    };

    (apiClient.delete as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ data: mockResponse });

    const res = await connectorService.remove('conn-1');

    expect(apiClient.delete).toHaveBeenCalledWith('/connectors/remove/conn-1');
    expect(res.data.status).toBe('DISCONNECTED');
  });

  it('getLogs() fetches audit synchronization logs with query parameters', async () => {
    const mockResponse = {
      success: true,
      data: {
        total_logs: 1,
        logs: [
          {
            id: 'log-1',
            connector_id: 'conn-1',
            sync_job_id: 'job-999',
            external_document_id: 'doc-001',
            document_title: 'API Reference',
            source_url: 'https://github.com/org/repo/wiki/API',
            action_taken: 'ADDED',
            status: 'SUCCESS',
            checksum: 'sha256-abcdef123',
            created_at: '2026-10-28T01:00:00Z',
          },
        ],
      },
    };

    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ data: mockResponse });

    const res = await connectorService.getLogs('conn-1', 25, 'SUCCESS');

    expect(apiClient.get).toHaveBeenCalledWith(
      '/connectors/logs?connector_id=conn-1&limit=25&status=SUCCESS'
    );
    expect(res.data.logs).toHaveLength(1);
    expect(res.data.total_logs).toBe(1);
  });
});
