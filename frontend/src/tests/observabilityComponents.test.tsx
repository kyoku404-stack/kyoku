import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import {

  SubsystemStatusCard,
  TelemetryMetricsGrid,
  AlertPanel,
  LogViewer,
  DiagnosticsModal,
} from '@/features/observability';
import { ObservabilityPage } from '@/pages/ObservabilityPage';
import { observabilityService } from '@/services/observabilityService';
import type { SystemAlert, StructuredLogEntry } from '@/types/observability';

vi.mock('@/services/observabilityService', () => ({
  observabilityService: {
    getCompositeHealth: vi.fn().mockResolvedValue({
      status: 'healthy',
      version: '1.0.0',
      timestamp: '2026-10-22T10:00:00Z',
      uptime_seconds: 86400,
      environment: 'production',
      dependencies: {
        database: { status: 'healthy', latency_ms: 1.15 },
        storage: { status: 'healthy', writable: true },
        api: { status: 'healthy', memory_rss_mb: 145.2 },
        auth: { status: 'healthy', jwt_secret_configured: true },
      },
    }),
    getDatabaseHealth: vi.fn().mockResolvedValue({
      status: 'healthy',
      latency_ms: 1.15,
      version: 'PostgreSQL 16.4',
      vector_extension: true,
      pool: { size: 20, checked_out: 2, overflow: 0 },
    }),
    getStorageHealth: vi.fn().mockResolvedValue({
      status: 'healthy',
      storage_root: '/app/storage',
      writable: true,
      latency_ms: 0.9,
      total_bytes: 1073741824000,
      used_bytes: 155692564480,
      used_percent: 14.5,
    }),
    getApiHealth: vi.fn().mockResolvedValue({
      status: 'healthy',
      uptime_seconds: 86400,
      python_version: '3.12.3',
      memory_rss_mb: 145.2,
      cpu_percent: 2.4,
      active_requests: 2,
    }),
    getAuthHealth: vi.fn().mockResolvedValue({
      status: 'healthy',
      jwt_secret_configured: true,
      algorithm: 'HS256',
      access_token_expire_minutes: 60,
      refresh_token_expire_days: 7,
    }),
    getTelemetrySummary: vi.fn().mockResolvedValue({
      system_status: 'healthy',
      uptime_seconds: 86400,
      timestamp: '2026-10-22T10:00:00Z',
      kpis: {
        requests_per_second: 14.5,
        p95_latency_ms: 38.5,
        error_rate_percent: 0.05,
        active_users: 18,
        total_documents: 240,
        storage_used_bytes: 155692564480,
        storage_capacity_bytes: 1073741824000,
        storage_percent: 14.5,
        database_pool_usage_percent: 10.0,
      },
      alerts: [
        {
          id: 'alt-001',
          severity: 'INFO',
          title: 'Scheduled Storage Backup',
          message: 'Automated snapshot completed with SHA-256 verification.',
          timestamp: '2026-10-22T09:00:00Z',
          acknowledged: false,
        },
      ],
      subsystem_health: {
        database: 'healthy',
        storage: 'healthy',
        api: 'healthy',
        auth: 'healthy',
      },
    }),
    getRawPrometheusMetrics: vi.fn().mockResolvedValue('# HELP http_requests_total\nhttp_requests_total 412.0'),
    getStructuredLogs: vi.fn().mockReturnValue([
      {
        id: 'log-001',
        timestamp: '2026-10-22T09:55:00Z',
        level: 'INFO',
        module: 'Authentication Service',
        action: 'User Login',
        status: 'Success',
        user_id: 'usr_lead_01',
        organization_id: 'org_acme',
        request_id: 'req-c8d9-4b2a',
        trace_id: '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01',
        execution_time_ms: 42.5,
        ip_address: '192.168.1.104',
        message: 'User authenticated successfully via JWT bearer token.',
        metadata: { role: 'OrgAdmin' },
      },
    ]),
    recordStructuredLog: vi.fn(),
    resetSeedLogs: vi.fn(),
  },
}));

describe('Phase 1.9 System Observability & Monitoring UI Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('SubsystemStatusCard Component', () => {
    it('renders PostgreSQL database card with connection pool and pgvector badge', () => {
      render(
        <SubsystemStatusCard
          type="database"
          status="healthy"
          dbData={{
            status: 'healthy',
            version: 'PostgreSQL 16.4',
            latency_ms: 1.15,
            vector_extension: true,
            connection_pool: { size: 20, checked_out: 2, overflow: 0 },
          }}
        />
      );

      expect(screen.getByText('PostgreSQL Database')).toBeDefined();
      expect(screen.getByText('PostgreSQL 16.4')).toBeDefined();
      expect(screen.getByText('1.15 ms')).toBeDefined();
      expect(screen.getByText('2 / 20')).toBeDefined();
      expect(screen.getByText(/Enabled \(1536-dim\)/i)).toBeDefined();
      expect(screen.getByText('HEALTHY')).toBeDefined();
    });

    it('renders Storage filesystem card with disk capacity and writable probe', () => {
      render(
        <SubsystemStatusCard
          type="storage"
          status="healthy"
          storageData={{
            status: 'healthy',
            storage_root: '/app/storage',
            writable: true,
            latency_ms: 0.85,
            total_bytes: 1073741824000,
            used_bytes: 155692564480,
            used_percent: 15,
          }}
        />
      );

      expect(screen.getByText('Storage & File System')).toBeDefined();
      expect(screen.getByText('/app/storage')).toBeDefined();
      expect(screen.getByText('Writable (OK)')).toBeDefined();
      expect(screen.getByText('0.85 ms')).toBeDefined();
    });

    it('renders FastAPI gateway card with runtime memory and CPU telemetry', () => {
      render(
        <SubsystemStatusCard
          type="api"
          status="healthy"
          apiData={{
            status: 'healthy',
            python_version: '3.12.3',
            memory_rss_mb: 145.2,
            cpu_percent: 2.4,
            active_requests: 3,
            uptime_seconds: 7200,
          }}
        />
      );

      expect(screen.getByText('FastAPI Gateway')).toBeDefined();
      expect(screen.getByText('Python 3.12.3')).toBeDefined();
      expect(screen.getByText('145.2 MB')).toBeDefined();
      expect(screen.getByText('2.4%')).toBeDefined();
      expect(screen.getByText('3 reqs')).toBeDefined();
      expect(screen.getByText('2.0 hours')).toBeDefined();
    });

    it('renders Authentication service card with JWT cryptographic configuration', () => {
      render(
        <SubsystemStatusCard
          type="auth"
          status="healthy"
          authData={{
            status: 'healthy',
            jwt_secret_configured: true,
            algorithm: 'HS256',
            access_token_expire_minutes: 60,
            refresh_token_expire_days: 7,
          }}
        />
      );

      expect(screen.getByText('Authentication & Identity')).toBeDefined();
      expect(screen.getByText('Active & Sealed')).toBeDefined();
      expect(screen.getByText('HS256')).toBeDefined();
      expect(screen.getByText('60m / 7d')).toBeDefined();
    });
  });

  describe('TelemetryMetricsGrid Component', () => {
    it('renders all 8 primary telemetry KPI cards and latency trend sparkline', () => {
      render(
        <TelemetryMetricsGrid
          kpis={{
            requests_per_second: 18.4,
            p95_latency_ms: 32.1,
            error_rate_percent: 0.04,
            active_users: 25,
            total_documents: 450,
            storage_used_bytes: 200000000000,
            storage_capacity_bytes: 1000000000000,
            storage_percent: 20.0,
            database_pool_usage_percent: 12.0,
          }}
          uptimeSeconds={172800}
          latencyHistory={[
            { timestamp: '2026-10-22T09:00:00Z', latency_ms: 35 },
            { timestamp: '2026-10-22T09:01:00Z', latency_ms: 32 },
          ]}
        />
      );

      expect(screen.getByText('Throughput (RPS)')).toBeDefined();
      expect(screen.getByText(/18.4/)).toBeDefined();
      expect(screen.getByText('P95 Latency')).toBeDefined();
      expect(screen.getByText(/32.1/)).toBeDefined();
      expect(screen.getByText('HTTP Error Rate')).toBeDefined();
      expect(screen.getByText('0.04%')).toBeDefined();
      expect(screen.getByText('Active Tenants / Users')).toBeDefined();
      expect(screen.getByText('25')).toBeDefined();
      expect(screen.getByText('Total Documents')).toBeDefined();
      expect(screen.getByText('450')).toBeDefined();
      expect(screen.getByText('20.0%')).toBeDefined();
      expect(screen.getByText('12%')).toBeDefined();
      expect(screen.getByText(/48.0/)).toBeDefined(); // 172800 / 3600 = 48.0 hrs
      expect(screen.getByText(/Real-Time API Latency Trend/i)).toBeDefined();
    });
  });

  describe('AlertPanel Component', () => {
    const alerts: SystemAlert[] = [
      {
        id: 'alt-101',
        severity: 'CRITICAL',
        title: 'High CPU Load Detected',
        message: 'CPU exceeded 90% threshold for > 60 seconds.',
        timestamp: '2026-10-22T09:30:00Z',
        component: 'API Gateway',
        threshold: 'CPU > 90%',
        acknowledged: false,
      },
      {
        id: 'alt-102',
        severity: 'WARNING',
        title: 'Storage Capacity Approaching Quota',
        message: 'Tenant storage has reached 80% of limit.',
        timestamp: '2026-10-22T09:40:00Z',
        component: 'Storage',
        threshold: 'Storage > 75%',
        acknowledged: false,
      },
    ];

    it('renders alerts with severity badges and allows acknowledging an alert', () => {
      const onAckMock = vi.fn();
      render(<AlertPanel alerts={alerts} onAcknowledge={onAckMock} />);

      expect(screen.getByText('High CPU Load Detected')).toBeDefined();
      expect(screen.getByText('Storage Capacity Approaching Quota')).toBeDefined();
      expect(screen.getAllByText('CRITICAL').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('WARNING').length).toBeGreaterThanOrEqual(1);


      const ackButtons = screen.getAllByRole('button', { name: /acknowledge/i });
      expect(ackButtons.length).toBe(2);
      fireEvent.click(ackButtons[0]);
      expect(onAckMock).toHaveBeenCalledWith('alt-101');
    });

    it('filters alerts when severity filter pill is clicked', () => {
      render(<AlertPanel alerts={alerts} />);

      const critFilter = screen.getByRole('button', { name: 'CRITICAL' });
      fireEvent.click(critFilter);

      expect(screen.getByText('High CPU Load Detected')).toBeDefined();
      expect(screen.queryByText('Storage Capacity Approaching Quota')).toBeNull();
    });
  });

  describe('LogViewer Component', () => {
    const mockLogs: StructuredLogEntry[] = [
      {
        id: 'log-001',
        timestamp: '2026-10-22T09:55:00Z',
        level: 'INFO',
        module: 'Authentication Service',
        action: 'User Login',
        status: 'Success',
        user_id: 'usr_lead_01',
        organization_id: 'org_acme',
        request_id: 'req-c8d9-4b2a',
        trace_id: '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01',
        execution_time_ms: 42.5,
        ip_address: '192.168.1.104',
        message: 'User authenticated successfully via JWT bearer token.',
        metadata: { role: 'OrgAdmin' },
      },
      {
        id: 'log-002',
        timestamp: '2026-10-22T09:56:00Z',
        level: 'ERROR',
        module: 'Storage Service',
        action: 'Upload Check',
        status: 'Failure',
        user_id: 'usr_member_02',
        organization_id: 'org_acme',
        request_id: 'req-e31a-9f12',
        trace_id: '00-5c6a1290bb34da6a3ce929d0e0e4736-00a124bb0ca902b7-01',
        execution_time_ms: 12.0,
        ip_address: '192.168.1.105',
        message: 'File upload size exceeds permitted quota.',
        metadata: { error: 'QUOTA_EXCEEDED' },
      },
    ];

    it('renders structured log entries and filters by search text', () => {
      vi.mocked(observabilityService.getStructuredLogs).mockReturnValue(mockLogs);
      render(<LogViewer initialLogs={mockLogs} />);


      expect(screen.getByText('User Login')).toBeDefined();
      expect(screen.getByText('Upload Check')).toBeDefined();
      expect(screen.getByText('req-c8d9-4b2a')).toBeDefined();

      const searchInput = screen.getByPlaceholderText(/search message, user, action/i);
      fireEvent.change(searchInput, { target: { value: 'Login' } });

      expect(observabilityService.getStructuredLogs).toHaveBeenCalledWith(
        expect.objectContaining({ query: 'Login' })
      );
    });

    it('opens detailed canonical 13-field log inspector modal on row click', async () => {
      render(<LogViewer initialLogs={mockLogs} />);

      const inspectBtn = screen.getByTestId('inspect-log-log-001');
      fireEvent.click(inspectBtn);

      await waitFor(() => {
        expect(screen.getByText(/Canonical Structured Log Entry/i)).toBeDefined();
        expect(screen.getAllByText('req-c8d9-4b2a').length).toBeGreaterThanOrEqual(1);
        expect(
          screen.getByText('00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01')
        ).toBeDefined();
        expect(screen.getByText(/Copy Trace ID/i)).toBeDefined();
      });
    });


  });

  describe('DiagnosticsModal Component', () => {
    it('executes diagnostic runner on button click and renders probe results', async () => {
      const onRunMock = vi.fn().mockResolvedValue({
        timestamp: '2026-10-22T10:00:00Z',
        totalDurationMs: 45,
        overallStatus: 'healthy',
        database: { status: 'healthy', latency_ms: 1.15, database: 'postgresql 16' },
        storage: { status: 'healthy', latency_ms: 0.9, writable: true },
        api: { status: 'healthy', memory_rss_mb: 145.2, python_version: '3.12' },
        auth: { status: 'healthy', algorithm: 'HS256' },
      });

      render(
        <DiagnosticsModal
          isOpen={true}
          onClose={vi.fn()}
          onRunDiagnostics={onRunMock}
        />
      );

      expect(screen.getByText('System Health & Diagnostic Runner')).toBeDefined();
      const runBtn = screen.getByRole('button', { name: /run diagnostics/i });
      fireEvent.click(runBtn);

      await waitFor(() => {
        expect(onRunMock).toHaveBeenCalled();
        expect(screen.getByText(/Executed in 45 ms/i)).toBeDefined();
        expect(screen.getByText('Database Probe')).toBeDefined();
        expect(screen.getByText('Storage Probe')).toBeDefined();
      });
    });
  });

  describe('ObservabilityPage Master Integration', () => {
    it('renders the complete Observability Command Center and allows tab switching', async () => {
      render(<ObservabilityPage />);

      await waitFor(() => {
        expect(screen.getByText('System Observability & Monitoring')).toBeDefined();
        expect(screen.getByText(/Platform Operational Status: HEALTHY/i)).toBeDefined();
      });

      // Switch to Telemetry tab
      const telemetryTab = screen.getByRole('button', { name: /kpis & latency trends/i });
      fireEvent.click(telemetryTab);
      expect(screen.getByText(/Throughput \(RPS\)/i)).toBeDefined();

      // Switch to Alerts tab
      const alertsTab = screen.getByRole('button', { name: /alerts & triggers/i });
      fireEvent.click(alertsTab);
      expect(screen.getByText(/System Alerts & Diagnostic Triggers/i)).toBeDefined();

      // Switch to Logs tab
      const logsTab = screen.getByRole('button', { name: /structured log viewer/i });
      fireEvent.click(logsTab);
      expect(screen.getByText(/Structured Application Logs & Request Traces/i)).toBeDefined();
    });
  });
});
