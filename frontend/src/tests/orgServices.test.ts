import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '@/services/api';
import {
  departmentService,
  teamService,
  invitationService,
  memberService,
  orgService,
} from '@/services';
import type { ApiResponse, PaginatedData } from '@/types/api';
import type { DepartmentResponse } from '@/types/department';
import type { Team } from '@/types/team';
import type { InvitationResponse } from '@/types/invitation';
import type { MemberResponse } from '@/types/member';
import type { OrganizationResponse } from '@/types/organization';

vi.mock('@/services/api', async () => {
  const actual = await vi.importActual<typeof import('@/services/api')>('@/services/api');
  return {
    ...actual,
    apiClient: {
      get: vi.fn(),
      post: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
      defaults: { baseURL: 'http://localhost:8000/api/v1' },
    },
  };
});

describe('Phase 1.5 Organization & Workspace API Client Services', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('departmentService', () => {
    it('listDepartments calls GET /departments with pagination params', async () => {
      const mockRes: ApiResponse<DepartmentResponse[]> = {
        success: true,
        message: 'Departments retrieved.',
        data: [
          {
            id: 'dept-1',
            organization_id: 'org-1',
            name: 'Engineering',
            description: 'Core dev',
            manager_id: null,
            team_count: 3,
            member_count: 15,
            created_at: '2026-10-10T10:00:00Z',
          },
        ],
      };
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockRes });

      const res = await departmentService.listDepartments(0, 50);
      expect(apiClient.get).toHaveBeenCalledWith('/departments', {
        params: { skip: 0, limit: 50 },
      });
      expect(res.data).toHaveLength(1);
      expect(res.data[0].name).toBe('Engineering');
    });

    it('getDepartment calls GET /departments/{id}', async () => {
      const mockRes: ApiResponse<DepartmentResponse> = {
        success: true,
        message: 'Department details.',
        data: {
          id: 'dept-1',
          organization_id: 'org-1',
          name: 'Engineering',
          created_at: '2026-10-10T10:00:00Z',
        },
      };
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockRes });

      const res = await departmentService.getDepartment('dept-1');
      expect(apiClient.get).toHaveBeenCalledWith('/departments/dept-1');
      expect(res.data.id).toBe('dept-1');
    });

    it('createDepartment calls POST /departments with payload', async () => {
      const payload = { name: 'Product Management', description: 'Product ops' };
      const mockRes: ApiResponse<DepartmentResponse> = {
        success: true,
        message: 'Department created.',
        data: {
          id: 'dept-2',
          organization_id: 'org-1',
          name: 'Product Management',
          description: 'Product ops',
          created_at: '2026-10-10T10:00:00Z',
        },
      };
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockRes });

      const res = await departmentService.createDepartment(payload);
      expect(apiClient.post).toHaveBeenCalledWith('/departments', payload);
      expect(res.data.name).toBe('Product Management');
    });

    it('updateDepartment calls PATCH /departments/{id}', async () => {
      const payload = { name: 'Platform Engineering' };
      const mockRes: ApiResponse<DepartmentResponse> = {
        success: true,
        message: 'Department updated.',
        data: {
          id: 'dept-1',
          organization_id: 'org-1',
          name: 'Platform Engineering',
          created_at: '2026-10-10T10:00:00Z',
        },
      };
      vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: mockRes });

      const res = await departmentService.updateDepartment('dept-1', payload);
      expect(apiClient.patch).toHaveBeenCalledWith('/departments/dept-1', payload);
      expect(res.data.name).toBe('Platform Engineering');
    });

    it('deleteDepartment calls DELETE /departments/{id}', async () => {
      const mockRes: ApiResponse<{ success: boolean }> = {
        success: true,
        message: 'Department deleted.',
        data: { success: true },
      };
      vi.mocked(apiClient.delete).mockResolvedValueOnce({ data: mockRes });

      const res = await departmentService.deleteDepartment('dept-1');
      expect(apiClient.delete).toHaveBeenCalledWith('/departments/dept-1');
      expect(res.data.success).toBe(true);
    });
  });

  describe('teamService', () => {
    it('listTeams passes optional department_id filter', async () => {
      const mockRes: ApiResponse<Team[]> = {
        success: true,
        message: 'Teams retrieved.',
        data: [
          {
            id: 'team-1',
            organization_id: 'org-1',
            department_id: 'dept-1',
            name: 'Backend Core',
            created_at: '2026-10-10T10:00:00Z',
          },
        ],
      };
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockRes });

      const res = await teamService.listTeams({ department_id: 'dept-1' });
      expect(apiClient.get).toHaveBeenCalledWith('/teams', {
        params: { department_id: 'dept-1' },
      });
      expect(res.data).toHaveLength(1);
    });

    it('deleteTeam calls DELETE /teams/{id}', async () => {
      const mockRes: ApiResponse<{ success: boolean }> = {
        success: true,
        message: 'Team deleted.',
        data: { success: true },
      };
      vi.mocked(apiClient.delete).mockResolvedValueOnce({ data: mockRes });

      const res = await teamService.deleteTeam('team-1');
      expect(apiClient.delete).toHaveBeenCalledWith('/teams/team-1');
      expect(res.data.success).toBe(true);
    });
  });

  describe('invitationService', () => {
    it('listInvitations calls GET /invitations', async () => {
      const mockRes: ApiResponse<InvitationResponse[]> = {
        success: true,
        message: 'Invitations retrieved.',
        data: [
          {
            id: 'inv-1',
            organization_id: 'org-1',
            email: 'invitee@domain.com',
            role: 'Member',
            token: 'tok-abc-1234567890',
            status: 'PENDING',
            invited_by_id: 'u-1',
            expires_at: '2026-10-18T10:00:00Z',
            created_at: '2026-10-11T10:00:00Z',
          },
        ],
      };
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockRes });

      const res = await invitationService.listInvitations(0, 100);
      expect(apiClient.get).toHaveBeenCalledWith('/invitations', {
        params: { skip: 0, limit: 100 },
      });
      expect(res.data[0].email).toBe('invitee@domain.com');
    });

    it('createInvitation dispatches POST /invitations', async () => {
      const payload = { email: 'new@domain.com', role: 'ProjectManager' };
      const mockRes: ApiResponse<InvitationResponse> = {
        success: true,
        message: 'Invitation dispatched.',
        data: {
          id: 'inv-2',
          organization_id: 'org-1',
          email: 'new@domain.com',
          role: 'ProjectManager',
          token: 'token-xyz-123456789',
          status: 'PENDING',
          invited_by_id: 'u-1',
          expires_at: '2026-10-18T10:00:00Z',
          created_at: '2026-10-11T10:00:00Z',
        },
      };
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockRes });

      const res = await invitationService.createInvitation(payload);
      expect(apiClient.post).toHaveBeenCalledWith('/invitations', payload);
      expect(res.data.role).toBe('ProjectManager');
    });

    it('revokeInvitation calls DELETE /invitations/{id}', async () => {
      const mockRes: ApiResponse<{ success: boolean }> = {
        success: true,
        message: 'Invitation revoked.',
        data: { success: true },
      };
      vi.mocked(apiClient.delete).mockResolvedValueOnce({ data: mockRes });

      const res = await invitationService.revokeInvitation('inv-1');
      expect(apiClient.delete).toHaveBeenCalledWith('/invitations/inv-1');
      expect(res.data.success).toBe(true);
    });

    it('acceptInvitation posts token and user credentials to /invitations/accept', async () => {
      const payload = {
        token: 'token-xyz-123456789',
        full_name: 'Jane Doe',
        password: 'Password123!',
      };
      const mockRes = {
        success: true,
        message: 'Invitation accepted.',
        data: {
          user_id: 'u-2',
          email: 'new@domain.com',
          organization_id: 'org-1',
        },
      };
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockRes });

      const res = await invitationService.acceptInvitation(payload);
      expect(apiClient.post).toHaveBeenCalledWith('/invitations/accept', payload);
      expect(res.data.user_id).toBe('u-2');
    });
  });

  describe('memberService', () => {
    it('listMembers calls GET /members with query parameters', async () => {
      const mockRes: ApiResponse<PaginatedData<MemberResponse>> = {
        success: true,
        message: 'Members retrieved.',
        data: {
          items: [
            {
              id: 'u-1',
              organization_id: 'org-1',
              email: 'admin@domain.com',
              full_name: 'Admin User',
              role: 'OrgAdmin',
              is_active: true,
              created_at: '2026-10-10T10:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
          total_pages: 1,
        },
      };
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockRes });

      const res = await memberService.listMembers({ role: 'OrgAdmin', page: 1 });
      expect(apiClient.get).toHaveBeenCalledWith('/members', {
        params: { role: 'OrgAdmin', page: 1 },
      });
      expect(res.data.items).toHaveLength(1);
    });

    it('updateMember calls PATCH /members/{user_id}', async () => {
      const payload = { role: 'ProjectManager', is_active: false };
      const mockRes: ApiResponse<MemberResponse> = {
        success: true,
        message: 'Member updated.',
        data: {
          id: 'u-1',
          organization_id: 'org-1',
          email: 'admin@domain.com',
          full_name: 'Admin User',
          role: 'ProjectManager',
          is_active: false,
          created_at: '2026-10-10T10:00:00Z',
        },
      };
      vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: mockRes });

      const res = await memberService.updateMember('u-1', payload);
      expect(apiClient.patch).toHaveBeenCalledWith('/members/u-1', payload);
      expect(res.data.role).toBe('ProjectManager');
      expect(res.data.is_active).toBe(false);
    });

    it('removeMember calls DELETE /members/{user_id}', async () => {
      const mockRes: ApiResponse<{ success: boolean }> = {
        success: true,
        message: 'Member removed.',
        data: { success: true },
      };
      vi.mocked(apiClient.delete).mockResolvedValueOnce({ data: mockRes });

      const res = await memberService.removeMember('u-1');
      expect(apiClient.delete).toHaveBeenCalledWith('/members/u-1');
      expect(res.data.success).toBe(true);
    });
  });

  describe('orgService', () => {
    it('createOrganization calls POST /organizations with corporate profile', async () => {
      const payload = {
        name: 'Acme Enterprise',
        domain: 'acme.com',
        industry: 'Software',
      };
      const mockRes: ApiResponse<OrganizationResponse> = {
        success: true,
        message: 'Organization created.',
        data: {
          id: 'org-new',
          name: 'Acme Enterprise',
          domain: 'acme.com',
          is_active: true,
          created_at: '2026-10-11T10:00:00Z',
        },
      };
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockRes });

      const res = await orgService.createOrganization(payload);
      expect(apiClient.post).toHaveBeenCalledWith('/organizations', payload);
      expect(res.data.id).toBe('org-new');
    });

    it('updateOrganization calls PATCH /organizations/{id}', async () => {
      const payload = {
        name: 'Acme Global Worldwide',
        settings: { enforce_2fa: true },
      };
      const mockRes: ApiResponse<OrganizationResponse> = {
        success: true,
        message: 'Organization updated.',
        data: {
          id: 'org-1',
          name: 'Acme Global Worldwide',
          is_active: true,
          created_at: '2026-10-11T10:00:00Z',
        },
      };
      vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: mockRes });

      const res = await orgService.updateOrganization('org-1', payload);
      expect(apiClient.patch).toHaveBeenCalledWith('/organizations/org-1', payload);
      expect(res.data.name).toBe('Acme Global Worldwide');
    });

    it('deleteOrganization calls DELETE /organizations/{id}', async () => {
      const mockRes: ApiResponse<{ success: boolean }> = {
        success: true,
        message: 'Organization deleted.',
        data: { success: true },
      };
      vi.mocked(apiClient.delete).mockResolvedValueOnce({ data: mockRes });

      const res = await orgService.deleteOrganization('org-1');
      expect(apiClient.delete).toHaveBeenCalledWith('/organizations/org-1');
      expect(res.data.success).toBe(true);
    });
  });
});
