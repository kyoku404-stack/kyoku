/**
 * Auth Feature Module
 * Authentication, multi-tenant organization switching, and RBAC authorization.
 */

export * from '@/types/auth';
export { authService } from '@/services/authService';

export const AUTH_FEATURE = {
  name: 'auth',
  version: '1.2.0',
  description: 'Enterprise authentication and multi-tenancy access control',
};
