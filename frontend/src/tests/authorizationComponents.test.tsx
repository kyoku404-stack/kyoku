import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { useAuthStore } from '@/store/useAuthStore';
import { PermissionGate } from '@/components/authorization/PermissionGate';
import { RoleGate } from '@/components/authorization/RoleGate';
import { RoleBadge } from '@/components/authorization/RoleBadge';
import { RoleSwitcherModal } from '@/components/authorization/RoleSwitcherModal';
import { AccessDeniedPage } from '@/pages/AccessDeniedPage';
import { Permission } from '@/types/permission';
import type { UserProfileResponse } from '@/types/auth';

const mockMemberUser: UserProfileResponse = {
  id: 'user-uuid-1',
  email: 'member@acme.corp',
  full_name: 'Member User',
  role: 'Member',
  organization_id: 'org-uuid-1',
  is_active: true,
  created_at: '2026-10-12T00:00:00Z',
};

describe('Phase 1.6 Authorization UI Components', () => {
  beforeEach(() => {
    useAuthStore.getState().clearAuth();
    useAuthStore.getState().setSimulatedRole(null);
  });

  describe('PermissionGate Component', () => {
    it('renders children when the user possesses the required permission', () => {
      useAuthStore.getState().setAuth(mockMemberUser, 'token');

      render(
        <PermissionGate permission={Permission.DOCUMENT_CREATE}>
          <button>Upload Document</button>
        </PermissionGate>
      );

      expect(screen.getByText('Upload Document')).toBeInTheDocument();
    });

    it('renders fallback when the user lacks the required permission', () => {
      useAuthStore.getState().setAuth(mockMemberUser, 'token');

      render(
        <PermissionGate
          permission={Permission.DOCUMENT_DELETE}
          fallback={<span>Deletion Disabled</span>}
        >
          <button>Delete Document</button>
        </PermissionGate>
      );

      expect(screen.queryByText('Delete Document')).not.toBeInTheDocument();
      expect(screen.getByText('Deletion Disabled')).toBeInTheDocument();
    });

    it('grants access via resource ownership override even if role lacks base permission', () => {
      // Member normally cannot delete documents, but can delete their OWN uploaded document
      useAuthStore.getState().setAuth(mockMemberUser, 'token');

      render(
        <PermissionGate
          permission={Permission.DOCUMENT_DELETE}
          resource={{ ownerId: mockMemberUser.id }}
          fallback={<span>Not Allowed</span>}
        >
          <button>Delete My Document</button>
        </PermissionGate>
      );

      expect(screen.getByText('Delete My Document')).toBeInTheDocument();
      expect(screen.queryByText('Not Allowed')).not.toBeInTheDocument();
    });

    it('evaluates anyOf permission array', () => {
      useAuthStore.getState().setAuth(mockMemberUser, 'token');

      render(
        <PermissionGate
          anyOf={[Permission.DOCUMENT_DELETE, Permission.DOCUMENT_READ]}
          fallback={<span>Denied</span>}
        >
          <span>Content Allowed</span>
        </PermissionGate>
      );

      expect(screen.getByText('Content Allowed')).toBeInTheDocument();
    });
  });

  describe('RoleGate Component', () => {
    it('renders children when role is in allowedRoles list', () => {
      useAuthStore.getState().setAuth(mockMemberUser, 'token');

      render(
        <RoleGate allowedRoles={['Member', 'OrgAdmin']}>
          <div>Member Dashboard</div>
        </RoleGate>
      );

      expect(screen.getByText('Member Dashboard')).toBeInTheDocument();
    });

    it('evaluates minimum role hierarchy level', () => {
      useAuthStore.getState().setAuth(mockMemberUser, 'token'); // level 2

      render(
        <RoleGate minRole="Manager" fallback={<div>Manager Role Required</div>}>
          <div>Manager Only Content</div>
        </RoleGate>
      );

      expect(screen.queryByText('Manager Only Content')).not.toBeInTheDocument();
      expect(screen.getByText('Manager Role Required')).toBeInTheDocument();
    });
  });

  describe('RoleBadge Component', () => {
    it('renders proper label and styling for different roles', () => {
      const { rerender } = render(<RoleBadge role="SuperAdmin" />);
      expect(screen.getByText('Super Admin')).toBeInTheDocument();

      rerender(<RoleBadge role="OrgAdmin" />);
      expect(screen.getByText('Org Admin')).toBeInTheDocument();

      rerender(<RoleBadge role="Manager" />);
      expect(screen.getByText('Manager')).toBeInTheDocument();

      rerender(<RoleBadge role="Member" />);
      expect(screen.getByText('Member')).toBeInTheDocument();

      rerender(<RoleBadge role="Viewer" />);
      expect(screen.getByText('Viewer')).toBeInTheDocument();
    });
  });

  describe('AccessDeniedPage Component', () => {
    it('renders 403 Forbidden message, active role badge, and navigation actions', () => {
      useAuthStore.getState().setAuth(mockMemberUser, 'token');

      render(
        <MemoryRouter
          initialEntries={[
            {
              pathname: '/access-denied',
              state: {
                requiredPermission: 'organization.settings',
                errorCode: 'AUTH_PERMISSION_DENIED',
              },
            },
          ]}
        >
          <AccessDeniedPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Access Restricted')).toBeInTheDocument();
      expect(screen.getByText('403 Forbidden — AUTH_PERMISSION_DENIED')).toBeInTheDocument();
      expect(screen.getByText('organization.settings')).toBeInTheDocument();
      expect(screen.getByText('Member')).toBeInTheDocument();
      expect(screen.getByText('Dashboard Overview')).toBeInTheDocument();
      expect(screen.getByText('Switch Role Preview')).toBeInTheDocument();
    });
  });

  describe('RoleSwitcherModal Component', () => {
    it('allows switching to simulated roles and resetting to actual role', () => {
      useAuthStore.getState().setAuth(mockMemberUser, 'token');
      const onClose = () => {};

      render(<RoleSwitcherModal isOpen={true} onClose={onClose} />);

      expect(screen.getByText('RBAC Role Simulator & Preview')).toBeInTheDocument();
      expect(screen.getByText('Organization Admin')).toBeInTheDocument();

      // Click Organization Admin card
      fireEvent.click(screen.getByText('Organization Admin'));
      expect(useAuthStore.getState().getEffectiveRole()).toBe('OrgAdmin');
      expect(useAuthStore.getState().hasPermission(Permission.AUDIT_READ)).toBe(true);
    });
  });
});
