/**
 * KEEP Enterprise Platform — Organization & Tenant Types.
 * Aligned with backend schemas (backend/app/schemas/organization.py) and PostgreSQL `organizations` table.
 */

export interface OrganizationSettings {
  enforce_2fa?: boolean;
  session_timeout_minutes?: number;
  password_expiry_days?: number;
  ip_allowlist?: string[];
  ai_default_model?: string;
  ai_token_quota?: number;
  ai_memory_scope?: string;
  ai_temperature?: number;
  storage_quota_bytes?: number;
  max_user_limit?: number;
  [key: string]: unknown;
}

export interface OrganizationResponse {
  id: string;
  name: string;
  domain?: string | null;
  industry?: string | null;
  company_size?: string | null;
  time_zone?: string | null;
  default_language?: string | null;
  logo_url?: string | null;
  description?: string | null;
  subscription_tier?: string;
  max_users?: number;
  max_storage_bytes?: number;
  ai_monthly_token_quota?: number;
  is_active: boolean;
  settings?: OrganizationSettings | Record<string, unknown> | null;
  is_deleted?: boolean;
  deleted_at?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface OrganizationCreate {
  name: string;
  domain: string;
  industry?: string | null;
  company_size?: string | null;
  time_zone?: string | null;
  default_language?: string | null;
  logo_url?: string | null;
  description?: string | null;
  subscription_tier?: string;
  max_users?: number;
  max_storage_bytes?: number;
  ai_monthly_token_quota?: number;
}

export interface OrganizationUpdate {
  name?: string | null;
  domain?: string | null;
  industry?: string | null;
  company_size?: string | null;
  time_zone?: string | null;
  theme?: string | null;
  default_language?: string | null;
  logo_url?: string | null;
  description?: string | null;
  is_active?: boolean | null;
  settings?: OrganizationSettings | Record<string, unknown> | null;
  subscription_tier?: string;
  max_users?: number;
  max_storage_bytes?: number;
  ai_monthly_token_quota?: number;
}
