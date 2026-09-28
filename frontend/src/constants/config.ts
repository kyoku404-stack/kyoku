/**
 * Application-wide configuration and environment variables.
 */

export const CONFIG = {
  APP_NAME: import.meta.env.VITE_APP_NAME || 'KEEP',
  APP_DESCRIPTION:
    import.meta.env.VITE_APP_DESCRIPTION ||
    'Knowledge Extraction & Enterprise Platform',
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  ENVIRONMENT: import.meta.env.VITE_ENV || 'development',
  FEATURES: {
    RAG_STREAMING: import.meta.env.VITE_ENABLE_RAG_STREAMING === 'true',
    KNOWLEDGE_GRAPH: import.meta.env.VITE_ENABLE_KNOWLEDGE_GRAPH === 'true',
    ANALYTICS: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
    MOCK_FALLBACK: import.meta.env.VITE_ENABLE_MOCK_FALLBACK === 'true',
  },
} as const;
