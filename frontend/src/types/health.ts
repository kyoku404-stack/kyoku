/**
 * KEEP Enterprise Platform — Health Diagnostics & Observability Types.
 * Aligned with backend schemas (backend/app/schemas/health.py) and devdocs/p1/p1.9.txt.
 */

export * from './observability';

export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy' | string;
  environment: string;
  version: string;
  timestamp: string;
  uptime_seconds?: number;
}

export interface ComponentHealth {
  status: 'healthy' | 'degraded' | 'unhealthy' | string;
  latency_ms?: number | null;
  details?: string | null;
  [key: string]: unknown;
}

export interface DetailedHealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy' | string;
  environment: string;
  version: string;
  timestamp: string;
  uptime_seconds: number;
  components: Record<string, ComponentHealth>;
}

export interface RootDiscoveryResponse {
  name: string;
  version: string;
  status: string;
  docs_url?: string;
  api_v1_prefix?: string;
  documentation?: string;
}

