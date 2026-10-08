/**
 * KEEP Enterprise Platform — User Domain Types.
 * Aligned with backend schemas (backend/app/schemas/user.py) and PostgreSQL `users` table.
 */

import type { UserRole, UserProfileResponse } from './auth';

export type { UserProfileResponse };

export interface ExtendedUserProfileResponse extends UserProfileResponse {
  avatar_url?: string | null;
  is_verified?: boolean;
  team_id?: string | null;
  is_deleted?: boolean;
}

export interface UserCreate {
  email: string;
  password: string;
  full_name: string;
  role?: UserRole;
  organization_id: string;
  avatar_url?: string;
  team_id?: string;
}

export interface UserUpdate {
  full_name?: string;
  role?: UserRole;
  avatar_url?: string;
  team_id?: string;
  is_active?: boolean;
}

export interface UserFilterParams {
  page?: number;
  page_size?: number;
  role?: UserRole;
  team_id?: string;
  search?: string;
}
