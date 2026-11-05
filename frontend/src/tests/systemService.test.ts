/**
 * Phase 3.6 Production Infrastructure & Operations API Client Tests.
 * Author: Member 3 (Frontend & UI Lead)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { systemService } from '@/services/systemService';
import { apiClient } from '@/services/api';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Phase 3.6 System Service API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getHealth() queries /api/v1/system/health', async () => {
    const mockHealth = {
      status: 'HEALTHY',
      uptime_seconds: 86400,
      timestamp: '2026-11-06T03:00:00Z',
      version: '3.6.0',
      overall_score: 0.995,
      subsystems: {},
    };
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: mockHealth },
    });

    const res = await systemService.getHealth();
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/system/health');
    expect(res.data).toEqual(mockHealth);
  });

  it('getMetrics() queries /api/v1/system/metrics', async () => {
    const mockMetrics = {
      timestamp: '2026-11-06T03:00:00Z',
      cpu: { percent: 25.4, cores: 8, load_avg_1m: 0.8 },
      memory: { total_mb: 16384, used_mb: 4096, percent: 25.0 },
      disk: { total_gb: 256, used_gb: 64, percent: 25.0 },
      network: { rx_bytes_sec: 1000, tx_bytes_sec: 2000 },
      application: {
        requests_per_second: 50.0,
        p50_latency_ms: 12.0,
        p95_latency_ms: 45.0,
        p99_latency_ms: 110.0,
        error_rate_percent: 0.01,
        active_connections: 80,
      },
      cache: { hit_ratio_percent: 95.0, total_keys: 10000, memory_used_mb: 64.0 },
    };
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: mockMetrics },
    });

    const res = await systemService.getMetrics();
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/system/metrics');
    expect(res.data?.cpu.percent).toBe(25.4);
  });

  it('getLogs() queries /api/v1/system/logs with query parameters', async () => {
    const mockLogs = [
      {
        id: 'log-1',
        service_name: 'keep-backend-api',
        severity: 'INFO',
        message: 'Platform started',
        created_at: '2026-11-06T03:00:00Z',
        metadata: {},
      },
    ];
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: mockLogs },
    });

    const res = await systemService.getLogs({ service_name: 'keep-backend-api', severity: 'INFO' });
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/system/logs', {
      params: { service_name: 'keep-backend-api', severity: 'INFO' },
    });
    expect(res.data).toEqual(mockLogs);
  });

  it('triggerDeploy() posts payload to /api/v1/system/deploy', async () => {
    const mockDeploy = {
      deployment_id: 'dep-123',
      service_name: 'keep-backend-api',
      version: '3.6.1',
      strategy: 'BLUE_GREEN',
      status: 'SUCCESS',
      started_at: '2026-11-06T03:00:00Z',
      details: {},
    };
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: mockDeploy },
    });

    const res = await systemService.triggerDeploy({
      service_name: 'keep-backend-api',
      version: '3.6.1',
      strategy: 'BLUE_GREEN',
    });
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/system/deploy', {
      service_name: 'keep-backend-api',
      version: '3.6.1',
      strategy: 'BLUE_GREEN',
    });
    expect(res.data?.status).toBe('SUCCESS');
  });

  it('getVersion() queries /api/v1/system/version', async () => {
    const mockVersion = {
      version: '3.6.0',
      git_commit: '599b185',
      build_date: '2026-11-06T03:00:00Z',
      environment: 'production',
      python_version: '3.12.10',
      frameworks: {},
    };
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: mockVersion },
    });

    const res = await systemService.getVersion();
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/system/version');
    expect(res.data?.version).toBe('3.6.0');
  });

  it('getStatus() queries /api/v1/system/status', async () => {
    const mockStatus = [
      {
        service_name: 'keep-frontend',
        status: 'RUNNING',
        replicas_desired: 2,
        replicas_ready: 2,
        version: '3.6.0',
        uptime_hours: 100,
        memory_mb: 80,
        cpu_percent: 2.0,
      },
    ];
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: mockStatus },
    });

    const res = await systemService.getStatus();
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/system/status');
    expect(res.data).toHaveLength(1);
  });

  it('getBackups() and createBackup() interact with backup endpoints', async () => {
    const mockBackups = {
      rpo_target_minutes: 60,
      rto_target_minutes: 240,
      current_rpo_drift_minutes: 20,
      backups: [],
    };
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: mockBackups },
    });

    const listRes = await systemService.getBackups();
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/system/backups');
    expect(listRes.data?.rpo_target_minutes).toBe(60);

    const mockCreate = {
      backup_id: 'bak-99',
      backup_name: 'backup-keep-manual-test',
      status: 'COMPLETED',
      size_bytes: 1000000,
      created_at: '2026-11-06T03:00:00Z',
    };
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: mockCreate },
    });

    const createRes = await systemService.createBackup({ backup_type: 'DATABASE', notes: 'Test' });
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/system/backups/create', {
      backup_type: 'DATABASE',
      notes: 'Test',
    });
    expect(createRes.data?.status).toBe('COMPLETED');
  });

  it('flushCache() posts payload to /api/v1/system/cache/flush', async () => {
    const mockFlush = {
      flushed_namespaces: ['keep:ai:resp:', 'keep:vector:q:'],
      keys_removed: 900,
    };
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: mockFlush },
    });

    const res = await systemService.flushCache({
      namespaces: ['ai_response', 'vector_query'],
      flush_all: false,
    });
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/system/cache/flush', {
      namespaces: ['ai_response', 'vector_query'],
      flush_all: false,
    });
    expect(res.data?.flushed_namespaces).toHaveLength(2);
  });
});
