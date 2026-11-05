/**
 * Phase 3.6 System Feature Components Tests.
 * Author: Member 3 (Frontend & UI Lead)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import {
  SystemMetricsBanner,
  MicroservicesGrid,
  SystemHealthDrawer,
  DeployServiceModal,
  DisasterRecoveryPanel,
  SystemLogsViewer,
  CacheFlushModal,
} from '@/features/system';
import type {
  MicroserviceStatusData,
  SystemBackupsData,
  SystemHealthData,
  SystemLogEntryData,
  SystemMetricsData,
} from '@/types/system';

describe('Phase 3.6 System Operations Feature Components', () => {
  it('SystemMetricsBanner displays all KPIs and health status correctly', () => {
    const mockHealth: SystemHealthData = {
      status: 'HEALTHY',
      uptime_seconds: 7200,
      timestamp: '2026-11-06T03:00:00Z',
      version: '3.6.0',
      overall_score: 0.99,
      subsystems: {},
    };
    const mockMetrics: SystemMetricsData = {
      timestamp: '2026-11-06T03:00:00Z',
      cpu: { percent: 34.2, cores: 8, load_avg_1m: 1.1 },
      memory: { total_mb: 16384, used_mb: 6144, percent: 37.5 },
      disk: { total_gb: 256, used_gb: 64, percent: 25.0 },
      network: { rx_bytes_sec: 1000, tx_bytes_sec: 2000 },
      application: {
        requests_per_second: 84.5,
        p50_latency_ms: 18.2,
        p95_latency_ms: 84.6,
        p99_latency_ms: 210.0,
        error_rate_percent: 0.04,
        active_connections: 128,
      },
      cache: { hit_ratio_percent: 93.8, total_keys: 42100, memory_used_mb: 182.4 },
    };

    render(<SystemMetricsBanner health={mockHealth} metrics={mockMetrics} />);

    expect(screen.getByText('Platform Health')).toBeDefined();
    expect(screen.getByText('HEALTHY')).toBeDefined();
    expect(screen.getByText('34.2%')).toBeDefined();
    expect(screen.getByText('37.5%')).toBeDefined();
    expect(screen.getByText('84.5')).toBeDefined();
    expect(screen.getByText('93.8%')).toBeDefined();
  });

  it('MicroservicesGrid renders service cards and handles deploy click', () => {
    const mockServices: MicroserviceStatusData[] = [
      {
        service_name: 'keep-backend-api',
        status: 'RUNNING',
        replicas_desired: 3,
        replicas_ready: 3,
        version: '3.6.0',
        uptime_hours: 142.5,
        memory_mb: 420.5,
        cpu_percent: 8.4,
      },
      {
        service_name: 'keep-frontend',
        status: 'RUNNING',
        replicas_desired: 2,
        replicas_ready: 2,
        version: '3.6.0',
        uptime_hours: 142.5,
        memory_mb: 84.0,
        cpu_percent: 1.2,
      },
    ];

    const onDeployMock = vi.fn();
    render(<MicroservicesGrid services={mockServices} onDeployService={onDeployMock} />);

    expect(screen.getByText('keep-backend-api')).toBeDefined();
    expect(screen.getByText('keep-frontend')).toBeDefined();
    expect(screen.getByText('3 / 3 Healthy')).toBeDefined();

    const deployButtons = screen.getAllByText('Deploy');
    fireEvent.click(deployButtons[0]);
    expect(onDeployMock).toHaveBeenCalledWith('keep-backend-api');
  });

  it('SystemHealthDrawer renders subsystem details when open', () => {
    const mockHealth: SystemHealthData = {
      status: 'HEALTHY',
      uptime_seconds: 7200,
      timestamp: '2026-11-06T03:00:00Z',
      version: '3.6.0',
      overall_score: 0.99,
      subsystems: {
        database: {
          status: 'HEALTHY',
          latency_ms: 2.4,
          engine: 'PostgreSQL 16',
        },
        redis: {
          status: 'HEALTHY',
          latency_ms: 0.8,
          version: '7.2.4',
        },
      },
    };

    const { rerender } = render(<SystemHealthDrawer isOpen={false} onClose={vi.fn()} health={mockHealth} />);
    expect(screen.queryByText('Subsystem Diagnostics')).toBeNull();

    rerender(<SystemHealthDrawer isOpen={true} onClose={vi.fn()} health={mockHealth} />);
    expect(screen.getByText('Subsystem Diagnostics')).toBeDefined();
    expect(screen.getByText(/database/i)).toBeDefined();
    expect(screen.getByText(/redis/i)).toBeDefined();
  });

  it('DeployServiceModal submits deployment configuration', () => {
    const onDeployMock = vi.fn().mockResolvedValue({});
    const onCloseMock = vi.fn();

    render(
      <DeployServiceModal
        isOpen={true}
        onClose={onCloseMock}
        initialService="keep-backend-api"
        onDeploy={onDeployMock}
        deploying={false}
      />
    );

    expect(screen.getByText('Trigger Service Deployment')).toBeDefined();
    const submitBtn = screen.getByText('Execute Deployment');
    fireEvent.click(submitBtn);

    expect(onDeployMock).toHaveBeenCalledWith({
      service_name: 'keep-backend-api',
      version: '3.6.1-patch1',
      strategy: 'BLUE_GREEN',
      environment: 'production',
      auto_rollback_on_failure: true,
    });
  });

  it('DisasterRecoveryPanel displays RPO compliance and backup inventory', () => {
    const mockBackups: SystemBackupsData = {
      rpo_target_minutes: 60,
      rto_target_minutes: 240,
      current_rpo_drift_minutes: 18,
      backups: [
        {
          id: 'bak-1',
          backup_name: 'backup-keep-prod-001',
          backup_type: 'DATABASE',
          status: 'VERIFIED',
          size_bytes: 145000000,
          storage_location: 's3://keep/bak.tar.gz',
          rpo_drift_seconds: 1080,
          created_at: '2026-11-06T03:00:00Z',
        },
      ],
    };

    render(
      <DisasterRecoveryPanel
        backupsData={mockBackups}
        onCreateBackup={vi.fn().mockResolvedValue({})}
        creatingBackup={false}
      />
    );

    expect(screen.getByText('Disaster Recovery & Backup Strategy')).toBeDefined();
    expect(screen.getByText('18m drift')).toBeDefined();
    expect(screen.getByText('backup-keep-prod-001')).toBeDefined();
    expect(screen.getByText('VERIFIED')).toBeDefined();
  });

  it('SystemLogsViewer displays logs and handles refresh', () => {
    const mockLogs: SystemLogEntryData[] = [
      {
        id: 'log-1',
        service_name: 'keep-backend-api',
        severity: 'INFO',
        message: 'API worker initialized',
        metadata: { port: 8000 },
        created_at: '2026-11-06T03:00:00Z',
      },
    ];

    const onRefreshMock = vi.fn();
    render(<SystemLogsViewer logs={mockLogs} onRefresh={onRefreshMock} loading={false} />);

    expect(screen.getByText('Centralized Operational Logs')).toBeDefined();
    expect(screen.getByText('API worker initialized')).toBeDefined();

    const warnBtn = screen.getByText('WARN');
    fireEvent.click(warnBtn);
    expect(onRefreshMock).toHaveBeenCalledWith({
      service_name: undefined,
      severity: 'WARN',
      query: undefined,
    });
  });

  it('CacheFlushModal handles namespace selection and flush execution', () => {
    const onFlushMock = vi.fn().mockResolvedValue({});
    const onCloseMock = vi.fn();

    render(
      <CacheFlushModal
        isOpen={true}
        onClose={onCloseMock}
        onFlush={onFlushMock}
        flushing={false}
      />
    );

    expect(screen.getByText('Flush Redis Cache')).toBeDefined();
    const flushBtn = screen.getByText('Flush Cache');
    fireEvent.click(flushBtn);

    expect(onFlushMock).toHaveBeenCalledWith({
      namespaces: ['ai_response', 'vector_query', 'dashboard'],
      flush_all: false,
    });
  });
});
