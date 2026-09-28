/**
 * Centralized strongly-typed route definitions.
 */

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
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
