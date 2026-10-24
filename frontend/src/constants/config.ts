/**
 * Application-wide configuration and environment variables.
 *
 * Owner: Member 3 (Frontend Lead)
 * Specification: devdocs/p1/p1.10.txt (Chapters 7, 8, 15, 18) & ADR-029
 * Phase: 1.10 — Deployment, Infrastructure & Production Readiness
 */

const envMode = (
  import.meta.env.VITE_ENV ||
  (import.meta.env.PROD ? 'production' : 'development')
).toLowerCase();

const isProd = envMode === 'production' || Boolean(import.meta.env.PROD);
const isStaging = envMode === 'staging';
const isDev = !isProd && !isStaging;

// In production behind reverse proxy (Nginx), relative /api/v1 routes seamlessly through ingress
const resolvedApiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ||
  (isProd ? '/api/v1' : 'http://localhost:8000/api/v1');

export const CONFIG = {
  APP_NAME: import.meta.env.VITE_APP_NAME || 'KEEP',
  APP_DESCRIPTION:
    import.meta.env.VITE_APP_DESCRIPTION ||
    'Knowledge Extraction & Enterprise Platform',
  API_BASE_URL: resolvedApiBaseUrl,
  ENVIRONMENT: envMode,
  IS_PRODUCTION: isProd,
  IS_STAGING: isStaging,
  IS_DEVELOPMENT: isDev,
  VERSION: '0.1.0',
  DEPLOYMENT: {
    REVERSE_PROXY: 'Nginx 1.27',
    GATEWAY_PROTOCOL: isProd ? 'HTTPS / TLS 1.3' : 'HTTP / Local',
    HEALTH_ENDPOINT: '/health',
    METRICS_ENDPOINT: '/metrics',
    STORAGE_SLO_RPO_HOURS: 1,
    STORAGE_SLO_RTO_MINUTES: 15,
  },
  FEATURES: {
    RAG_STREAMING: import.meta.env.VITE_ENABLE_RAG_STREAMING === 'true',
    KNOWLEDGE_GRAPH: import.meta.env.VITE_ENABLE_KNOWLEDGE_GRAPH === 'true',
    ANALYTICS: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
    MOCK_FALLBACK: import.meta.env.VITE_ENABLE_MOCK_FALLBACK === 'true',
  },
} as const;
