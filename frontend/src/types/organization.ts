/**
 * KEEP Enterprise Platform — Organization & Tenant Types.
 * Aligned with backend schemas (backend/app/schemas/organization.py) and PostgreSQL `organizations` table.
 */

export interface OrganizationResponse {
  id: string;
  name: string;
  domain: string;
  subscription_tier?: string;
  max_users?: number;
  max_storage_bytes?: number;
  ai_monthly_token_quota?: number;
  is_active: boolean;
  is_deleted?: boolean;
  deleted_at?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface OrganizationCreate {
  name: string;
  domain: string;
  subscription_tier?: string;
  max_users?: number;
  max_storage_bytes?: number;
  ai_monthly_token_quota?: number;
}

export interface OrganizationUpdate {
  name?: string;
  domain?: string;
  subscription_tier?: string;
  max_users?: number;
  max_storage_bytes?: number;
  ai_monthly_token_quota?: number;
  is_active?: boolean;
}
