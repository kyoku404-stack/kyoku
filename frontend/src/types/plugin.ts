/**
 * KEEP Enterprise Platform — Plugin SDK & Developer Ecosystem Types.
 *
 * Phase: 3.5
 * Specification: devdocs/p3/p3.5.txt & docs/API/api-contract.md (Section 17)
 * Role: Member 3 (Frontend & UI Lead)
 */

export type PluginCategory = 'AI' | 'INTEGRATION' | 'WORKFLOW' | 'UI' | 'ANALYTICS';

export type PluginStatus = 'ACTIVE' | 'DISABLED' | 'INSTALLED' | 'ERROR';

export type PluginVerificationTier = 'COMMUNITY' | 'VERIFIED' | 'CERTIFIED';

export type PluginExecutionStatus = 'SUCCESS' | 'FAILED' | 'TIMEOUT' | 'SECURITY_BLOCKED';

export interface PluginItem {
  id: string;
  plugin_id: string;
  name: string;
  version: string;
  category: PluginCategory;
  status: PluginStatus;
  is_enabled: boolean;
  developer?: string;
  description?: string;
  permissions: string[];
  event_hooks: string[];
  configuration: Record<string, unknown>;
  installed_at?: string;
  updated_at?: string;
}

export interface PluginMarketplaceItem {
  id: string;
  plugin_id: string;
  name: string;
  description: string;
  category: PluginCategory;
  developer: string;
  version: string;
  verification_tier: PluginVerificationTier;
  rating: number;
  installs_count: number;
  is_installed: boolean;
  min_keep_version: string;
  max_keep_version: string;
  permissions: string[];
  event_hooks: string[];
  icon_url?: string | null;
  documentation_url?: string | null;
}

export interface PluginExecutionResponse {
  execution_id: string;
  plugin_id: string;
  action: string;
  status: string;
  duration_ms: number;
  result: Record<string, unknown>;
  error_message?: string | null;
}

export interface PluginExecutionLog {
  id: string;
  plugin_id: string;
  action: string;
  status: string;
  duration_ms: number;
  triggered_by: string;
  error_message?: string | null;
  created_at: string;
}

export interface PluginAnalytics {
  total_installed_plugins: number;
  active_plugins: number;
  total_executions: number;
  avg_latency_ms: number;
  error_rate: number;
  plugins_by_category: Record<string, number>;
}

// ============================================================================
// Payload Types
// ============================================================================

export interface PluginInstallPayload {
  plugin_id: string;
  version?: string;
  configuration?: Record<string, unknown>;
  approved_permissions?: string[];
  marketplace_package_url?: string;
}

export interface PluginUpdatePayload {
  plugin_id: string;
  target_version: string;
}

export interface PluginUninstallPayload {
  plugin_id: string;
  purge_data?: boolean;
}

export interface PluginExecutePayload {
  action: string;
  parameters?: Record<string, unknown>;
  timeout_seconds?: number;
}

export interface PluginConfigUpdatePayload {
  configuration: Record<string, unknown>;
}

export interface PluginPublishPayload {
  id: string;
  name: string;
  description: string;
  category: PluginCategory;
  developer: string;
  version: string;
  entry_point: string;
  min_keep_version: string;
  max_keep_version: string;
  permissions?: string[];
  event_hooks?: string[];
  configuration_schema?: Record<string, unknown>;
  icon_url?: string;
  documentation_url?: string;
}
