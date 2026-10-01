/**
 * KEEP Enterprise Platform — User Domain Types.
 * Aligned with backend schemas (backend/app/schemas/user.py).
 */

import type { UserRole, UserProfileResponse } from './auth';

export type { UserProfileResponse };

export interface UserCreate {
  email: string;
  password: string;
  full_name: string;
  role?: UserRole;
  organization_id: string;
}

export interface UserUpdate {
  full_name?: string;
  role?: UserRole;
  is_active?: boolean;
}

export interface UserFilterParams {
  page?: number;
  page_size?: number;
  role?: UserRole;
  search?: string;
}
