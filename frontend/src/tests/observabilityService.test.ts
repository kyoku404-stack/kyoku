import { describe, it, expect, vi, beforeEach } from 'vitest';
import { observabilityService } from '@/services/observabilityService';
import { apiClient } from '@/services/api';
import axios from 'axios';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    defaults: { baseURL: 'http://localhost:8000/api/v1' },
  },
}));

vi.mock('axios');

describe('Phase 1.9 Observability & System Monitoring Client Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    observabilityService.resetSeedLogs();
  });

  it('fetches composite platform health check probe (/health)', async () => {
    const mockComposite = {
      status: 'healthy',
      version: '1.0.0',
      timestamp: '2026-10-22T10:00:00Z',
      uptime_seconds: 86400,
      environment: 'production',
      dependencies: {
        database: { status: 'healthy', latency_ms: 1.25 },
        storage: { status: 'healthy', writable: true },
        api: { status: 'healthy', memory_rss_mb: 145.2 },
        auth: { status: 'healthy', jwt_secret_configured: true },
      },
    };

    vi.mocked(axios.get).mockResolvedValueOnce({ data: mockComposite });

    const result = await observabilityService.getCompositeHealth();
    expect(result.status).toBe('healthy');
    expect(result.dependencies.database?.status).toBe('healthy');
    expect(result.dependencies.storage?.writable).toBe(true);
  });

  it('fetches isolated database health check probe (/health/database)', async () => {
    const mockDb = {
      status: 'healthy',
      latency_ms: 1.15,
      database: 'postgresql',
      version: 'PostgreSQL 16.4',
      vector_extension: true,
      pool: { size: 20, checked_out: 2, overflow: 0 },
    };

    vi.mocked(axios.get).mockResolvedValueOnce({ data: mockDb });

    const result = await observabilityService.getDatabaseHealth();
    expect(result.status).toBe('healthy');
    expect(result.latency_ms).toBe(1.15);
    expect(result.vector_extension).toBe(true);
    expect(result.pool?.size).toBe(20);
  });

  it('fetches isolated storage health check probe (/health/storage)', async () => {
    const mockStorage = {
      status: 'healthy',
      storage_root: '/app/storage',
      writable: true,
      latency_ms: 0.9,
      total_bytes: 1073741824000,
      used_bytes: 155692564480,
      free_bytes: 918049259520,
      used_percent: 14.5,
    };

    vi.mocked(axios.get).mockResolvedValueOnce({ data: mockStorage });

    const result = await observabilityService.getStorageHealth();
    expect(result.status).toBe('healthy');
    expect(result.writable).toBe(true);
    expect(result.used_percent).toBe(14.5);
  });

  it('fetches API runtime process health probe (/health/api)', async () => {
    const mockApi = {
      status: 'healthy',
      uptime_seconds: 86400,
      python_version: '3.12.3',
      memory_rss_mb: 145.2,
      cpu_percent: 2.4,
      active_requests: 2,
    };

    vi.mocked(axios.get).mockResolvedValueOnce({ data: mockApi });

    const result = await observabilityService.getApiHealth();
    expect(result.status).toBe('healthy');
    expect(result.memory_rss_mb).toBe(145.2);
    expect(result.active_requests).toBe(2);
  });

  it('fetches authentication readiness probe (/health/auth)', async () => {
    const mockAuth = {
      status: 'healthy',
      jwt_secret_configured: true,
      algorithm: 'HS256',
      access_token_expire_minutes: 60,
      refresh_token_expire_days: 7,
    };

    vi.mocked(axios.get).mockResolvedValueOnce({ data: mockAuth });

    const result = await observabilityService.getAuthHealth();
    expect(result.status).toBe('healthy');
    expect(result.jwt_secret_configured).toBe(true);
    expect(result.algorithm).toBe('HS256');
  });

  it('fetches operational telemetry metrics summary (/api/v1/metrics/summary)', async () => {
    const mockSummary = {
      success: true,
      message: 'Telemetry summary retrieved',
      data: {
        system_status: 'healthy',
        uptime_seconds: 86400,
        timestamp: '2026-10-22T10:00:00Z',
        kpis: {
          requests_per_second: 15.2,
          p95_latency_ms: 36.8,
          error_rate_percent: 0.02,
          active_users: 22,
          total_documents: 310,
          storage_used_bytes: 200000000000,
          storage_capacity_bytes: 1000000000000,
          storage_percent: 20.0,
          database_pool_usage_percent: 15.0,
        },
        alerts: [],
        subsystem_health: {
          database: 'healthy',
          storage: 'healthy',
          api: 'healthy',
          auth: 'healthy',
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockSummary });

    const result = await observabilityService.getTelemetrySummary();
    expect(result.system_status).toBe('healthy');
    expect(result.kpis.requests_per_second).toBe(15.2);
    expect(result.kpis.total_documents).toBe(310);
  });

  it('fetches raw Prometheus exposition text (/metrics)', async () => {
    const mockPrometheus = `# HELP http_requests_total Total number of HTTP requests processed.
# TYPE http_requests_total counter
http_requests_total{handler="/api/v1/documents",method="GET",status="200"} 412.0`;

    vi.mocked(axios.get).mockResolvedValueOnce({ data: mockPrometheus });


    const result = await observabilityService.getRawPrometheusMetrics();
    expect(result).toContain('http_requests_total');
    expect(result).toContain('412.0');
  });

  it('retrieves, filters, and records structured application logs', () => {
    const initialLogs = observabilityService.getStructuredLogs();
    expect(initialLogs.length).toBeGreaterThan(0);

    // Filter by level
    const infoLogs = observabilityService.getStructuredLogs({ level: 'INFO' });
    expect(infoLogs.every((l) => l.level === 'INFO')).toBe(true);

    // Record new log entry
    const newEntry = observabilityService.recordStructuredLog({
      level: 'ERROR',
      module: 'Test Module',
      action: 'Simulate Error',
      status: 'Failure',
      user_id: 'usr_test_01',
      organization_id: 'org_test',
      request_id: 'req-test-99',
      trace_id: '00-test-trace-id-01',
      execution_time_ms: 55.4,
      ip_address: '10.0.0.1',
      message: 'Test simulated error log',
      metadata: { code: 'TEST_ERR' },
    });

    expect(newEntry.id).toBeDefined();
    expect(newEntry.timestamp).toBeDefined();

    // Query by query text
    const found = observabilityService.getStructuredLogs({ query: 'Simulate Error' });
    expect(found.length).toBeGreaterThanOrEqual(1);
    expect(found[0].action).toBe('Simulate Error');
    expect(found[0].status).toBe('Failure');

    // Query by Request ID
    const byReq = observabilityService.getStructuredLogs({ requestId: 'req-test-99' });
    expect(byReq.length).toBe(1);
    expect(byReq[0].request_id).toBe('req-test-99');
  });
});
