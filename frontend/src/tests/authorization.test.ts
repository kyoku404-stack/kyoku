import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from '@/store/useAuthStore';
import {
  Permission,
  ROLE_PERMISSIONS_MAP,
  ROLE_HIERARCHY,
  VIEWER_PERMISSIONS,
  MEMBER_PERMISSIONS,
  MANAGER_PERMISSIONS,
  ORG_ADMIN_PERMISSIONS,
  SUPER_ADMIN_PERMISSIONS,
} from '@/types/permission';
import type { UserProfileResponse } from '@/types/auth';

const mockUser: UserProfileResponse = {
  id: 'user-uuid-1',
  email: 'employee@acme.corp',
  full_name: 'Alex Employee',
  role: 'Member',
  organization_id: 'org-uuid-1',
  is_active: true,
  created_at: '2026-10-12T00:00:00Z',
};

describe('Phase 1.6 Authorization & RBAC Logic', () => {
  beforeEach(() => {
    useAuthStore.getState().clearAuth();
    useAuthStore.getState().setSimulatedRole(null);
  });

  describe('Role Hierarchy & Canonical Permissions Mapping', () => {
    it('hierarchically elevates permissions from Viewer to SuperAdmin', () => {
      expect(ROLE_HIERARCHY.Viewer).toBeLessThan(ROLE_HIERARCHY.Member);
      expect(ROLE_HIERARCHY.Member).toBeLessThan(ROLE_HIERARCHY.Manager);
      expect(ROLE_HIERARCHY.Manager).toBeLessThan(ROLE_HIERARCHY.OrgAdmin);
      expect(ROLE_HIERARCHY.OrgAdmin).toBeLessThan(ROLE_HIERARCHY.SuperAdmin);

      // Verify inheritance
      VIEWER_PERMISSIONS.forEach((perm) => {
        expect(MEMBER_PERMISSIONS.has(perm)).toBe(true);
        expect(MANAGER_PERMISSIONS.has(perm)).toBe(true);
        expect(ORG_ADMIN_PERMISSIONS.has(perm)).toBe(true);
        expect(SUPER_ADMIN_PERMISSIONS.has(perm)).toBe(true);
      });

      // Member adds document.create
      expect(MEMBER_PERMISSIONS.has(Permission.DOCUMENT_CREATE)).toBe(true);
      expect(VIEWER_PERMISSIONS.has(Permission.DOCUMENT_CREATE)).toBe(false);

      // Manager adds document.delete
      expect(MANAGER_PERMISSIONS.has(Permission.DOCUMENT_DELETE)).toBe(true);
      expect(MEMBER_PERMISSIONS.has(Permission.DOCUMENT_DELETE)).toBe(false);

      // OrgAdmin adds audit.read and organization.settings
      expect(ORG_ADMIN_PERMISSIONS.has(Permission.AUDIT_READ)).toBe(true);
      expect(ORG_ADMIN_PERMISSIONS.has(Permission.ORGANIZATION_SETTINGS)).toBe(true);
      expect(MANAGER_PERMISSIONS.has(Permission.AUDIT_READ)).toBe(false);

      // SuperAdmin adds organization.create
      expect(SUPER_ADMIN_PERMISSIONS.has(Permission.ORGANIZATION_CREATE)).toBe(true);
      expect(ORG_ADMIN_PERMISSIONS.has(Permission.ORGANIZATION_CREATE)).toBe(false);
    });

    it('accurately resolves permissions in ROLE_PERMISSIONS_MAP', () => {
      expect(ROLE_PERMISSIONS_MAP.Viewer.has(Permission.AI_SEARCH)).toBe(true);
      expect(ROLE_PERMISSIONS_MAP.Member.has(Permission.AI_CHAT)).toBe(true);
      expect(ROLE_PERMISSIONS_MAP.Manager.has(Permission.PROJECT_MANAGE)).toBe(true);
      expect(ROLE_PERMISSIONS_MAP.OrgAdmin.has(Permission.USER_MANAGE)).toBe(true);
    });
  });

  describe('useAuthStore Authorization State', () => {
    it('correctly evaluates permissions for an authenticated Member', () => {
      useAuthStore.getState().setAuth(mockUser, 'test-token');

      const state = useAuthStore.getState();
      expect(state.getEffectiveRole()).toBe('Member');
      expect(state.hasPermission(Permission.DOCUMENT_READ)).toBe(true);
      expect(state.hasPermission(Permission.DOCUMENT_CREATE)).toBe(true);
      expect(state.hasPermission(Permission.DOCUMENT_DELETE)).toBe(false);
      expect(state.hasPermission(Permission.AUDIT_READ)).toBe(false);

      expect(state.isAtLeastRole('Viewer')).toBe(true);
      expect(state.isAtLeastRole('Member')).toBe(true);
      expect(state.isAtLeastRole('Manager')).toBe(false);
    });

    it('evaluates hasAllPermissions and hasAnyPermission', () => {
      useAuthStore.getState().setAuth(mockUser, 'test-token');
      const state = useAuthStore.getState();

      expect(
        state.hasAllPermissions([Permission.DOCUMENT_READ, Permission.DOCUMENT_CREATE])
      ).toBe(true);
      expect(
        state.hasAllPermissions([Permission.DOCUMENT_READ, Permission.DOCUMENT_DELETE])
      ).toBe(false);

      expect(
        state.hasAnyPermission([Permission.DOCUMENT_DELETE, Permission.DOCUMENT_CREATE])
      ).toBe(true);
      expect(
        state.hasAnyPermission([Permission.DOCUMENT_DELETE, Permission.AUDIT_READ])
      ).toBe(false);
    });

    it('switches to simulated role and updates permissions dynamically', () => {
      useAuthStore.getState().setAuth(mockUser, 'test-token');
      expect(useAuthStore.getState().hasPermission(Permission.AUDIT_READ)).toBe(false);

      // Simulate OrgAdmin
      useAuthStore.getState().setSimulatedRole('OrgAdmin');
      expect(useAuthStore.getState().getEffectiveRole()).toBe('OrgAdmin');
      expect(useAuthStore.getState().hasPermission(Permission.AUDIT_READ)).toBe(true);
      expect(useAuthStore.getState().isAtLeastRole('Manager')).toBe(true);

      // Simulate Viewer (downgrade)
      useAuthStore.getState().setSimulatedRole('Viewer');
      expect(useAuthStore.getState().getEffectiveRole()).toBe('Viewer');
      expect(useAuthStore.getState().hasPermission(Permission.DOCUMENT_CREATE)).toBe(false);
      expect(useAuthStore.getState().hasPermission(Permission.DOCUMENT_READ)).toBe(true);

      // Reset simulation
      useAuthStore.getState().setSimulatedRole(null);
      expect(useAuthStore.getState().getEffectiveRole()).toBe('Member');
      expect(useAuthStore.getState().hasPermission(Permission.DOCUMENT_CREATE)).toBe(true);
    });
  });
});
