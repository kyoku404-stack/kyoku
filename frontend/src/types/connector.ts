/**
 * Phase 3.1 Enterprise Integrations & Connector Framework TypeScript Definitions.
 * Aligned with docs/api/api-contract.md Section 13 and devdocs/p3/p3.1.txt.
 * Author: Member 3 (Frontend & UI Lead)
 */

export const PlatformType = {
  GOOGLE_DRIVE: 'GOOGLE_DRIVE',
  ONEDRIVE: 'ONEDRIVE',
  SHAREPOINT: 'SHAREPOINT',
  DROPBOX: 'DROPBOX',
  S3: 'S3',
  CONFLUENCE: 'CONFLUENCE',
  NOTION: 'NOTION',
  SLACK: 'SLACK',
  TEAMS: 'TEAMS',
  GITHUB: 'GITHUB',
  GITLAB: 'GITLAB',
  JIRA: 'JIRA',
  SALESFORCE: 'SALESFORCE',
  HUBSPOT: 'HUBSPOT',
} as const;
export type PlatformType = (typeof PlatformType)[keyof typeof PlatformType];

export const PlatformCategory = {
  CLOUD_STORAGE: 'CLOUD_STORAGE',
  DOCUMENTATION: 'DOCUMENTATION',
  COMMUNICATION: 'COMMUNICATION',
  DEVELOPMENT: 'DEVELOPMENT',
  PROJECT_MANAGEMENT: 'PROJECT_MANAGEMENT',
  CRM: 'CRM',
} as const;
export type PlatformCategory = (typeof PlatformCategory)[keyof typeof PlatformCategory];

export const AuthType = {
  OAUTH2: 'OAUTH2',
  OPENID_CONNECT: 'OPENID_CONNECT',
  PERSONAL_ACCESS_TOKEN: 'PERSONAL_ACCESS_TOKEN',
  API_KEY: 'API_KEY',
  SERVICE_ACCOUNT: 'SERVICE_ACCOUNT',
} as const;
export type AuthType = (typeof AuthType)[keyof typeof AuthType];

export const ConnectorStatus = {
  CONFIGURED: 'CONFIGURED',
  AUTHENTICATING: 'AUTHENTICATING',
  CONNECTED: 'CONNECTED',
  SYNCING: 'SYNCING',
  HEALTHY: 'HEALTHY',
  DEGRADED: 'DEGRADED',
  ERROR: 'ERROR',
  DISCONNECTED: 'DISCONNECTED',
} as const;
export type ConnectorStatus = (typeof ConnectorStatus)[keyof typeof ConnectorStatus];

export const SyncMode = {
  FULL: 'FULL',
  INCREMENTAL: 'INCREMENTAL',
  SCHEDULED: 'SCHEDULED',
  REAL_TIME: 'REAL_TIME',
} as const;
export type SyncMode = (typeof SyncMode)[keyof typeof SyncMode];

export const SyncJobStatus = {
  PENDING: 'PENDING',
  RUNNING: 'RUNNING',
  COMPLETED: 'COMPLETED',
  SUCCESS: 'COMPLETED',
  FAILED: 'FAILED',
  CANCELLED: 'CANCELLED',
} as const;
export type SyncJobStatus = (typeof SyncJobStatus)[keyof typeof SyncJobStatus];

export const SyncAction = {
  ADDED: 'ADDED',
  UPDATED: 'UPDATED',
  DELETED: 'DELETED',
  SKIPPED: 'SKIPPED',
  FAILED: 'FAILED',
} as const;
export type SyncAction = (typeof SyncAction)[keyof typeof SyncAction];

export interface ConnectorConfig {
  sync_interval_minutes?: number;
  sync_folders?: string[];
  file_extensions?: string[];
  rate_limit_per_minute?: number;
  max_batch_size?: number;
  [key: string]: unknown;
}

export interface ConnectorRegisterRequest {
  name: string;
  platform_type: PlatformType | string;
  platform_category: PlatformCategory | string;
  auth_type: AuthType | string;
  config?: ConnectorConfig;
}

export interface ConnectorRegisterResponse {
  id: string;
  name: string;
  platform_type: PlatformType | string;
  platform_category: PlatformCategory | string;
  auth_type: AuthType | string;
  status: ConnectorStatus | string;
  config: ConnectorConfig;
  total_documents_synced: number;
  created_at: string;
}

export interface ConnectorAuthenticateRequest {
  connector_id: string;
  auth_type: AuthType | string;
  credentials: {
    access_token?: string;
    refresh_token?: string;
    api_key?: string;
    service_account_key?: string;
    expires_in?: number;
    [key: string]: unknown;
  };
}

export interface ConnectorAuthenticateResponse {
  connector_id: string;
  status: ConnectorStatus | string;
  authenticated_at: string;
}

export interface ConnectorListItem {
  id: string;
  name: string;
  platform_type: PlatformType | string;
  platform_category: PlatformCategory | string;
  auth_type: AuthType | string;
  status: ConnectorStatus | string;
  total_documents_synced: number;
  last_sync_at: string | null;
  last_sync_status: string | null;
  created_at: string;
}

export interface ConnectorListResponse {
  total_connectors: number;
  connectors: ConnectorListItem[];
}

export interface ConnectorSyncRequest {
  connector_id: string;
  sync_mode?: SyncMode | string;
}

export interface ConnectorSyncResponse {
  sync_job_id: string;
  connector_id: string;
  sync_mode: SyncMode | string;
  status: SyncJobStatus | string;
  started_at: string;
}

export interface ConnectorHealthMetrics {
  api_latency_ms: number;
  quota_used_pct: number;
  success_rate_pct: number;
}

export interface ConnectorStatusResponse {
  id: string;
  name: string;
  platform_type: PlatformType | string;
  status: ConnectorStatus | string;
  last_sync_at: string | null;
  last_sync_status: string | null;
  total_documents_synced: number;
  active_sync_job: {
    id: string;
    sync_mode: string;
    started_at: string;
    documents_discovered: number;
  } | null;
  health_metrics: ConnectorHealthMetrics;
}

export interface ConnectorRemoveResponse {
  id: string;
  name: string;
  status: string;
}

export interface ConnectorSyncLogItem {
  id: string;
  connector_id: string;
  sync_job_id: string | null;
  external_document_id: string;
  document_title: string;
  source_url: string | null;
  action_taken: SyncAction | string;
  status: string;
  checksum: string | null;
  created_at: string;
}

export interface ConnectorLogsResponse {
  total_logs: number;
  logs: ConnectorSyncLogItem[];
}
