/**
 * KEEP Enterprise Platform — Observability, Health & Telemetry Types.
 * Aligned with Phase 1.9 specifications (devdocs/p1/p1.9.txt and docs/api/api-contract.md Section 6).
 */

export type SubsystemStatus = 'healthy' | 'degraded' | 'unhealthy';

export interface DatabaseConnectionPool {
  size: number;
  checked_out: number;
  overflow: number;
}

export interface DatabaseHealth {
  status: SubsystemStatus;
  latency_ms?: number | null;
  database?: string;
  version?: string;
  vector_extension?: boolean;
  vector_extension_enabled?: boolean;
  connection_pool?: DatabaseConnectionPool;
  pool?: DatabaseConnectionPool;
  error?: string | null;
}

export interface StorageHealth {
  status: SubsystemStatus;
  storage_root?: string;
  writable: boolean;
  latency_ms?: number | null;
  total_bytes?: number;
  used_bytes?: number;
  free_bytes?: number;
  free_space_bytes?: number;
  used_percent?: number;
  error?: string | null;
}

export interface ApiHealth {
  status: SubsystemStatus;
  uptime_seconds: number;
  python_version?: string;
  memory_rss_mb?: number;
  cpu_percent?: number;
  active_requests?: number;
  error?: string | null;
}

export interface AuthHealth {
  status: SubsystemStatus;
  jwt_secret_configured: boolean;
  algorithm: string;
  access_token_expire_minutes?: number;
  refresh_token_expire_days?: number;
  error?: string | null;
}

export interface CompositeHealthDependencies {
  database?: DatabaseHealth;
  storage?: StorageHealth;
  api?: ApiHealth;
  auth?: AuthHealth;
}

export interface CompositeHealthResponse {
  status: SubsystemStatus;
  version: string;
  timestamp: string;
  uptime_seconds: number;
  environment: string;
  dependencies: CompositeHealthDependencies;
}

export interface SystemTelemetryKPIs {
  requests_per_second: number;
  p95_latency_ms: number;
  error_rate_percent: number;
  active_users: number;
  total_documents: number;
  storage_used_bytes: number;
  storage_capacity_bytes: number;
  storage_percent: number;
  database_pool_usage_percent: number;
}

export type AlertSeverity = 'INFO' | 'WARNING' | 'CRITICAL' | 'SECURITY';

export interface SystemAlert {
  id: string;
  severity: AlertSeverity;
  title: string;
  message: string;
  timestamp: string;
  acknowledged?: boolean;
  component?: string;
  metric?: string;
  threshold?: string;
}

export interface SubsystemHealthMatrix {
  database: SubsystemStatus;
  storage: SubsystemStatus;
  api: SubsystemStatus;
  auth: SubsystemStatus;
}

export interface SystemTelemetrySummary {
  system_status: SubsystemStatus;
  uptime_seconds: number;
  timestamp: string;
  kpis: SystemTelemetryKPIs;
  alerts: SystemAlert[];
  subsystem_health: SubsystemHealthMatrix;
}

export type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'CRITICAL';
export type LogCategory = 'Application' | 'Error' | 'Security' | 'Audit' | 'AI';

/**
 * 13-field canonical log schema specified in devdocs/p1/p1.9.txt Chapter 6
 */
export interface StructuredLogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  module: string;
  action: string;
  status: 'Success' | 'Failure' | string;
  user_id?: string | null;
  organization_id?: string | null;
  request_id?: string | null;
  trace_id?: string | null;
  execution_time_ms?: number | null;
  ip_address?: string | null;
  message: string;
  metadata?: Record<string, unknown>;
  stack_trace?: string | null;
}

export interface LogFilterParams {
  query?: string;
  level?: LogLevel | 'ALL';
  module?: string | 'ALL';
  status?: string | 'ALL';
  requestId?: string;
  timeRange?: '15m' | '1h' | '6h' | '24h' | 'ALL';
}

export interface LatencySample {
  timestamp: string;
  latency_ms: number;
  subsystem?: string;
}
