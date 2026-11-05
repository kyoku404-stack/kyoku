/**
 * KEEP Enterprise Platform — Production Infrastructure & System Operations Type Definitions.
 * Aligned with backend contracts (docs/Architecture/production-infrastructure-scalability-observability.md
 * and backend/app/schemas/infrastructure.py).
 * Phase: 3.6
 * Role: Member 3 (Frontend & UI Lead)
 */

export type SystemHealthStatus = 'HEALTHY' | 'DEGRADED' | 'CRITICAL' | 'UNKNOWN';

export interface SubsystemProbe {
  name?: string;
  status: SystemHealthStatus;
  latency_ms: number;
  [key: string]: unknown;
}

export interface SystemHealthData {
  status: SystemHealthStatus;
  uptime_seconds: number;
  timestamp: string;
  version: string;
  overall_score: number;
  subsystems: Record<string, SubsystemProbe>;
}

export interface CpuMetrics {
  percent: number;
  cores: number;
  load_avg_1m: number;
}

export interface MemoryMetrics {
  total_mb: number;
  used_mb: number;
  percent: number;
}

export interface DiskMetrics {
  total_gb: number;
  used_gb: number;
  percent: number;
}

export interface NetworkMetrics {
  rx_bytes_sec: number;
  tx_bytes_sec: number;
}

export interface ApplicationMetrics {
  requests_per_second: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  error_rate_percent: number;
  active_connections: number;
}

export interface CacheMetrics {
  hit_ratio_percent: number;
  total_keys: number;
  memory_used_mb: number;
}

export interface SystemMetricsData {
  timestamp: string;
  cpu: CpuMetrics;
  memory: MemoryMetrics;
  disk: DiskMetrics;
  network: NetworkMetrics;
  application: ApplicationMetrics;
  cache: CacheMetrics;
}

export type LogSeverity = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'FATAL';

export interface SystemLogEntryData {
  id: string;
  service_name: string;
  severity: LogSeverity;
  message: string;
  trace_id?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export type MicroserviceState = 'RUNNING' | 'STARTING' | 'STOPPED' | 'CRASH_LOOP' | 'MAINTENANCE';

export interface MicroserviceStatusData {
  service_name: string;
  status: MicroserviceState;
  replicas_desired: number;
  replicas_ready: number;
  version: string;
  uptime_hours: number;
  memory_mb: number;
  cpu_percent: number;
}

export type DeploymentStrategy = 'ROLLING' | 'BLUE_GREEN' | 'CANARY';
export type DeploymentStatus = 'PENDING' | 'IN_PROGRESS' | 'SUCCESS' | 'FAILED' | 'ROLLED_BACK';

export interface DeployTriggerRequest {
  service_name: string;
  version: string;
  strategy: DeploymentStrategy;
  environment?: string;
  auto_rollback_on_failure?: boolean;
}

export interface DeployTriggerData {
  deployment_id: string;
  service_name: string;
  version: string;
  strategy: DeploymentStrategy;
  status: DeploymentStatus;
  started_at: string;
  completed_at?: string | null;
  rollback_version?: string | null;
  details: Record<string, unknown>;
}

export interface SystemVersionData {
  version: string;
  git_commit: string;
  build_date: string;
  environment: string;
  python_version: string;
  frameworks: Record<string, string>;
}

export type BackupType = 'DATABASE' | 'FULL' | 'OBJECT_STORAGE' | 'WAL';
export type BackupStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'VERIFIED';

export interface SystemBackupItemData {
  id: string;
  backup_name: string;
  backup_type: BackupType;
  status: BackupStatus;
  size_bytes: number;
  storage_location: string;
  rpo_drift_seconds: number;
  checksum_sha256?: string | null;
  notes?: string | null;
  verified_at?: string | null;
  created_at: string;
}

export interface SystemBackupsData {
  rpo_target_minutes: number;
  rto_target_minutes: number;
  current_rpo_drift_minutes: number;
  last_successful_backup?: string | null;
  backups: SystemBackupItemData[];
}

export interface CreateBackupRequest {
  backup_type: BackupType;
  notes?: string;
}

export interface CreateBackupData {
  backup_id: string;
  backup_name: string;
  status: string;
  size_bytes: number;
  created_at: string;
}

export interface CacheFlushRequest {
  namespaces: string[];
  flush_all: boolean;
}

export interface CacheFlushData {
  flushed_namespaces: string[];
  keys_removed: number;
}
