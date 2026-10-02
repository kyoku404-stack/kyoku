/**
 * KEEP Enterprise Platform — Health Diagnostics Types.
 * Aligned with backend schemas (backend/app/schemas/health.py).
 */

export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy' | string;
  environment: string;
  version: string;
  timestamp: string;
}

export interface ComponentHealth {
  status: 'healthy' | 'degraded' | 'unhealthy' | string;
  latency_ms?: number | null;
  details?: string | null;
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
