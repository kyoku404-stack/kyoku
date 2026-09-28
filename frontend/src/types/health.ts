export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  environment: string;
  version: string;
  timestamp: string;
}

export interface RootDiscoveryResponse {
  name: string;
  version: string;
  status: string;
  documentation: string;
}
