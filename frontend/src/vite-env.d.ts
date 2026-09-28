/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_APP_NAME: string;
  readonly VITE_APP_DESCRIPTION: string;
  readonly VITE_ENV: string;
  readonly VITE_ENABLE_RAG_STREAMING: string;
  readonly VITE_ENABLE_KNOWLEDGE_GRAPH: string;
  readonly VITE_ENABLE_ANALYTICS: string;
  readonly VITE_ENABLE_MOCK_FALLBACK: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
