/**
 * KEEP Enterprise Platform — Role-Based Access Control & Permission Definitions.
 * Aligned with backend architecture (docs/Architecture/authorization-architecture.md,
 * backend/app/core/authorization.py, and backend/app/services/ai/interfaces.py).
 */

import type { UserRole } from './auth';

/**
 * Action-based fine-grained permissions across the platform.
 */
export const Permission = {
  // Documents
  DOCUMENT_CREATE: 'document.create',
  DOCUMENT_READ: 'document.read',
  DOCUMENT_UPDATE: 'document.update',
  DOCUMENT_DELETE: 'document.delete',

  // Projects
  PROJECT_CREATE: 'project.create',
  PROJECT_READ: 'project.read',
  PROJECT_UPDATE: 'project.update',
  PROJECT_DELETE: 'project.delete',
  PROJECT_MANAGE: 'project.manage',

  // Meetings
  MEETING_CREATE: 'meeting.create',
  MEETING_READ: 'meeting.read',
  MEETING_MANAGE: 'meeting.manage',

  // AI & RAG
  AI_CHAT: 'ai.chat',
  AI_SEARCH: 'ai.search',
  AI_ADMIN: 'ai.admin',
  AI_CONFIG: 'ai.config',

  // Organization & Hierarchy
  ORGANIZATION_CREATE: 'organization.create',
  ORGANIZATION_READ: 'organization.read',
  ORGANIZATION_MANAGE: 'organization.manage',
  ORGANIZATION_SETTINGS: 'organization.settings',
  DEPT_CREATE: 'dept.create',
  DEPT_READ: 'dept.read',
  DEPT_UPDATE: 'dept.update',
  DEPT_DELETE: 'dept.delete',
  TEAM_CREATE: 'team.create',
  TEAM_READ: 'team.read',
  TEAM_UPDATE: 'team.update',
  TEAM_DELETE: 'team.delete',

  // Members & Invitations
  USER_VIEW: 'user.view',
  USER_INVITE: 'user.invite',
  USER_MANAGE: 'user.manage',
  MEMBER_READ: 'member.read',
  MEMBER_UPDATE: 'member.update',
  MEMBER_REMOVE: 'member.remove',
  INVITATION_READ: 'invitation.read',
  INVITATION_REVOKE: 'invitation.revoke',

  // Connectors & Integrations
  CONNECTOR_VIEW: 'connector:view',
  CONNECTOR_MANAGE: 'connector:manage',
  CONNECTOR_SYNC: 'connector:sync',

  // Analytics & Audit
  ANALYTICS_VIEW: 'analytics.view',
  ANALYTICS_EXPORT: 'analytics.export',
  AUDIT_READ: 'audit.read',
} as const;

export type PermissionKey = keyof typeof Permission;
export type PermissionValue = (typeof Permission)[PermissionKey];

/**
 * Numeric role hierarchy level (higher = more privileged).
 */
export const ROLE_HIERARCHY: Record<UserRole, number> = {
  SuperAdmin: 5,
  OrgAdmin: 4,
  Manager: 3,
  Member: 2,
  Viewer: 1,
  Guest: 0,
};

/**
 * Canonical permissions assigned to Viewer role.
 */
export const VIEWER_PERMISSIONS: Set<string> = new Set([
  Permission.DOCUMENT_READ,
  Permission.PROJECT_READ,
  Permission.MEETING_READ,
  Permission.AI_CHAT,
  Permission.AI_SEARCH,
  Permission.USER_VIEW,
  Permission.ANALYTICS_VIEW,
  Permission.ORGANIZATION_READ,
  Permission.DEPT_READ,
  Permission.TEAM_READ,
  Permission.MEMBER_READ,
  Permission.CONNECTOR_VIEW,
]);

/**
 * Canonical permissions assigned to Member (Employee) role.
 * Inherits all Viewer permissions + creation and update abilities.
 */
export const MEMBER_PERMISSIONS: Set<string> = new Set([
  ...VIEWER_PERMISSIONS,
  Permission.DOCUMENT_CREATE,
  Permission.DOCUMENT_UPDATE,
  Permission.PROJECT_CREATE,
  Permission.PROJECT_UPDATE,
  Permission.INVITATION_READ,
  Permission.CONNECTOR_SYNC,
]);

/**
 * Canonical permissions assigned to Manager (Project Manager) role.
 * Inherits all Member permissions + deletion, project management, meeting creation.
 */
export const MANAGER_PERMISSIONS: Set<string> = new Set([
  ...MEMBER_PERMISSIONS,
  Permission.DOCUMENT_DELETE,
  Permission.PROJECT_DELETE,
  Permission.PROJECT_MANAGE,
  Permission.TEAM_CREATE,
  Permission.TEAM_UPDATE,
  Permission.MEETING_CREATE,
  Permission.MEETING_MANAGE,
  Permission.USER_INVITE,
]);

/**
 * Canonical permissions assigned to Organization Admin role.
 * Inherits Manager permissions + org settings, department lifecycle, user admin, audit.
 */
export const ORG_ADMIN_PERMISSIONS: Set<string> = new Set([
  ...MANAGER_PERMISSIONS,
  Permission.ORGANIZATION_MANAGE,
  Permission.ORGANIZATION_SETTINGS,
  Permission.DEPT_CREATE,
  Permission.DEPT_UPDATE,
  Permission.DEPT_DELETE,
  Permission.TEAM_DELETE,
  Permission.USER_MANAGE,
  Permission.MEMBER_UPDATE,
  Permission.MEMBER_REMOVE,
  Permission.INVITATION_REVOKE,
  Permission.AI_ADMIN,
  Permission.AI_CONFIG,
  Permission.ANALYTICS_EXPORT,
  Permission.AUDIT_READ,
  Permission.CONNECTOR_MANAGE,
]);

/**
 * Canonical permissions assigned to SuperAdmin role.
 * Possesses all platform permissions including multi-org creation.
 */
export const SUPER_ADMIN_PERMISSIONS: Set<string> = new Set([
  ...ORG_ADMIN_PERMISSIONS,
  Permission.ORGANIZATION_CREATE,
]);

/**
 * Mapping of canonical UserRole to their complete granted permissions set.
 */
export const ROLE_PERMISSIONS_MAP: Record<UserRole, Set<string>> = {
  SuperAdmin: SUPER_ADMIN_PERMISSIONS,
  OrgAdmin: ORG_ADMIN_PERMISSIONS,
  Manager: MANAGER_PERMISSIONS,
  Member: MEMBER_PERMISSIONS,
  Viewer: VIEWER_PERMISSIONS,
  Guest: new Set([Permission.DOCUMENT_READ, Permission.ORGANIZATION_READ]),
};

/**
 * Permissions that can be bypassed by resource ownership (author/uploader).
 */
export const OWNERSHIP_OVERRIDE_PERMISSIONS = new Set<string>([
  Permission.DOCUMENT_UPDATE,
  Permission.DOCUMENT_DELETE,
  Permission.DOCUMENT_READ,
  Permission.MEETING_MANAGE,
  Permission.MEETING_READ,
]);

/**
 * Resource ownership context evaluated in authorization checks.
 */
export interface ResourceContext {
  resourceId?: string;
  resourceType?: string;
  ownerId?: string;
  projectId?: string;
  organizationId?: string;
}

/**
 * Structured authorization decision returned by UI evaluation helpers.
 */
export interface AuthDecision {
  allowed: boolean;
  reason: string;
  errorCode?: string;
  requiredPermission?: string;
  requiredRole?: UserRole;
}
