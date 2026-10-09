/**
 * Centralized strongly-typed route definitions.
 */

export const ROUTES = {
  HOME: '/',
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  FORGOT_PASSWORD: '/auth/forgot-password',
  RESET_PASSWORD: '/auth/reset-password',
  PROFILE: '/profile',
  DASHBOARD: '/dashboard',
  SEARCH: '/search',
  DOCUMENTS: '/documents',
  UPLOAD: '/upload',
  CHAT: '/chat',
  PROJECTS: '/projects',
  MEETINGS: '/meetings',
  ANALYTICS: '/analytics',
  HEALTH: '/health',
  NOT_FOUND: '*',
} as const;

export type RouteKey = keyof typeof ROUTES;
