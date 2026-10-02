/**
 * KEEP Enterprise Platform — Organization & Tenant Types.
 * Aligned with backend schemas (backend/app/schemas/organization.py).
 */

export interface OrganizationResponse {
  id: string;
  name: string;
  domain: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface OrganizationCreate {
  name: string;
  domain: string;
}

export interface OrganizationUpdate {
  name?: string;
  domain?: string;
  is_active?: boolean;
}
