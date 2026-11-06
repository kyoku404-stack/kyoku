/**
 * Centralized strongly-typed route definitions.
 * Updated for Phase 1.5 Organization & Workspace Management, Phase 3.6 Infrastructure, and Phase 3.7 Release Operations.
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
  RAG: '/rag',
  ORGANIZATION: '/organization',
  ORGANIZATION_SETUP: '/organization/setup',
  DEPARTMENTS: '/departments',
  TEAMS: '/teams',
  PROJECTS: '/projects',
  MEMBERS: '/members',
  ORG_SETTINGS: '/organization/settings',
  INVITATION_ACCEPT: '/invitations/accept',
  MEETINGS: '/meetings',
  ANALYTICS: '/analytics',
  AUDIT_LOGS: '/audit/logs',
  ACCESS_DENIED: '/access-denied',
  HEALTH: '/health',
  OBSERVABILITY: '/observability',
  INGESTION: '/ingestion',
  ASSISTANT: '/assistant',
  KNOWLEDGE_GRAPH: '/graph',
  INTELLIGENCE: '/intelligence',
  ENTERPRISE_INTELLIGENCE: '/enterprise-intelligence',
  INTEGRATIONS: '/integrations',
  CONNECTORS: '/connectors',
  COLLABORATION: '/collaboration',
  WORKSPACES: '/workspaces',
  SECURITY: '/security',
  COMPLIANCE: '/compliance',
  WORKFLOWS: '/workflows',
  NOTIFICATIONS: '/notifications',
  PLUGINS: '/plugins',
  MARKETPLACE: '/marketplace',
  SYSTEM: '/system',
  SYSTEM_OPERATIONS: '/system/operations',
  SYSTEM_RELEASE: '/system/release',
  NOT_FOUND: '*',
} as const;

export const PATHS = ROUTES;

export type RouteKey = keyof typeof ROUTES;
