import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { OrgSetupWizard } from '@/features/organization/OrgSetupWizard';
import { DepartmentManager } from '@/features/organization/DepartmentManager';
import { TeamManager } from '@/features/organization/TeamManager';
import { MemberListTable } from '@/features/organization/MemberListTable';
import { InviteMemberModal } from '@/features/organization/InviteMemberModal';
import { AcceptInvitationForm } from '@/features/organization/AcceptInvitationForm';
import { OrgSettingsView } from '@/features/organization/OrgSettingsView';
import { departmentService } from '@/services/departmentService';
import { teamService } from '@/services/teamService';
import { memberService } from '@/services/memberService';
import { orgService } from '@/services/orgService';
import { invitationService } from '@/services/invitationService';

vi.mock('@/services/departmentService', () => ({
  departmentService: {
    listDepartments: vi.fn(),
    createDepartment: vi.fn(),
    updateDepartment: vi.fn(),
    deleteDepartment: vi.fn(),
  },
}));

vi.mock('@/services/teamService', () => ({
  teamService: {
    listTeams: vi.fn(),
    createTeam: vi.fn(),
    updateTeam: vi.fn(),
    deleteTeam: vi.fn(),
  },
}));

vi.mock('@/services/memberService', () => ({
  memberService: {
    listMembers: vi.fn(),
    updateMember: vi.fn(),
    removeMember: vi.fn(),
  },
}));

vi.mock('@/services/orgService', () => ({
  orgService: {
    getCurrentOrganization: vi.fn(),
    createOrganization: vi.fn(),
    updateOrganization: vi.fn(),
  },
}));

vi.mock('@/services/invitationService', () => ({
  invitationService: {
    listInvitations: vi.fn(),
    createInvitation: vi.fn(),
    revokeInvitation: vi.fn(),
    acceptInvitation: vi.fn(),
  },
}));

describe('Phase 1.5 Organization & Workspace UI Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('OrgSetupWizard Component', () => {
    it('renders step 1 Organization Profile inputs', () => {
      render(<OrgSetupWizard />);
      expect(screen.getByText('Organization Profile')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Acme Global Inc.')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('acme.com')).toBeInTheDocument();
    });

    it('advances from step 1 to step 2 when required inputs are provided', () => {
      render(<OrgSetupWizard />);
      const nameInput = screen.getByPlaceholderText('Acme Global Inc.');
      const domainInput = screen.getByPlaceholderText('acme.com');

      fireEvent.change(nameInput, { target: { value: 'Stark Industries' } });
      fireEvent.change(domainInput, { target: { value: 'stark.com' } });

      const continueBtn = screen.getByRole('button', { name: /continue to departments/i });
      expect(continueBtn).not.toBeDisabled();
      fireEvent.click(continueBtn);

      expect(screen.getByText('Department Hierarchy')).toBeInTheDocument();
    });
  });

  describe('DepartmentManager Component', () => {
    it('renders department listings and add department button', async () => {
      vi.mocked(departmentService.listDepartments).mockResolvedValueOnce({
        success: true,
        message: 'Loaded',
        data: [
          {
            id: 'dept-eng',
            organization_id: 'org-1',
            name: 'Engineering Division',
            description: 'Core product engineering',
            team_count: 4,
            member_count: 22,
            created_at: '2026-10-10T10:00:00Z',
          },
        ],
      });

      render(<DepartmentManager />);
      expect(screen.getByText('Departments')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText('Engineering Division')).toBeInTheDocument();
      });
      expect(screen.getByText('4 teams')).toBeInTheDocument();
      expect(screen.getByText('22 members')).toBeInTheDocument();
    });
  });

  describe('TeamManager Component', () => {
    it('renders team listings and department mappings', async () => {
      vi.mocked(teamService.listTeams).mockResolvedValueOnce({
        success: true,
        message: 'Loaded',
        data: [
          {
            id: 'team-backend',
            organization_id: 'org-1',
            department_id: 'dept-1',
            name: 'Backend Core',
            description: 'API & Persistence',
            member_count: 6,
            created_at: '2026-10-10T10:00:00Z',
          },
        ],
      });
      vi.mocked(departmentService.listDepartments).mockResolvedValueOnce({
        success: true,
        message: 'Loaded',
        data: [
          {
            id: 'dept-1',
            organization_id: 'org-1',
            name: 'Engineering',
            created_at: '2026-10-10T10:00:00Z',
          },
        ],
      });

      render(<TeamManager />);
      expect(screen.getByText('Teams')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText('Backend Core')).toBeInTheDocument();
      });
      expect(screen.getByText(/Department: Engineering/i)).toBeInTheDocument();
      expect(screen.getByText('6 members')).toBeInTheDocument();
    });
  });

  describe('MemberListTable Component', () => {
    it('renders member table with roles and status badges', async () => {
      vi.mocked(departmentService.listDepartments).mockResolvedValueOnce({
        success: true,
        message: 'Loaded',
        data: [],
      });
      vi.mocked(teamService.listTeams).mockResolvedValueOnce({
        success: true,
        message: 'Loaded',
        data: [],
      });
      vi.mocked(memberService.listMembers).mockResolvedValueOnce({
        success: true,
        message: 'Loaded',
        data: {
          items: [
            {
              id: 'u-1',
              organization_id: 'org-1',
              email: 'sarah@domain.com',
              full_name: 'Sarah Connor',
              role: 'OrgAdmin',
              is_active: true,
              created_at: '2026-10-10T10:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 10,
          total_pages: 1,
        },
      });

      render(<MemberListTable />);
      expect(screen.getByText('Member Management')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText('Sarah Connor')).toBeInTheDocument();
      });
      expect(screen.getByText('sarah@domain.com')).toBeInTheDocument();
      expect(screen.getAllByText('OrgAdmin').length).toBeGreaterThan(0);
      expect(screen.getByText('Active')).toBeInTheDocument();
    });
  });

  describe('InviteMemberModal Component', () => {
    it('renders inputs and dispatches invitation payload', async () => {
      vi.mocked(departmentService.listDepartments).mockResolvedValueOnce({
        success: true,
        message: 'Loaded',
        data: [],
      });
      vi.mocked(teamService.listTeams).mockResolvedValueOnce({
        success: true,
        message: 'Loaded',
        data: [],
      });
      vi.mocked(invitationService.createInvitation).mockResolvedValueOnce({
        success: true,
        message: 'Sent',
        data: {
          id: 'inv-1',
          organization_id: 'org-1',
          email: 'alex@enterprise.com',
          role: 'Member',
          token: 'token-12345678',
          status: 'PENDING',
          invited_by_id: 'u-1',
          expires_at: '2026-10-18T10:00:00Z',
          created_at: '2026-10-11T10:00:00Z',
        },
      });

      const onClose = vi.fn();
      const onInvited = vi.fn();
      render(<InviteMemberModal isOpen={true} onClose={onClose} onInvited={onInvited} />);

      expect(screen.getByText('Invite New Team Member')).toBeInTheDocument();
      const emailInput = screen.getByPlaceholderText('colleague@domain.com');
      fireEvent.change(emailInput, { target: { value: 'alex@enterprise.com' } });

      const sendBtn = screen.getByRole('button', { name: /send invitation/i });
      fireEvent.click(sendBtn);

      await waitFor(() => {
        expect(invitationService.createInvitation).toHaveBeenCalledWith({
          email: 'alex@enterprise.com',
          role: 'Member',
          department_id: null,
          team_id: null,
        });
      });
      expect(onInvited).toHaveBeenCalled();
      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('AcceptInvitationForm Component', () => {
    it('renders form and displays error if passwords do not match', async () => {
      render(<AcceptInvitationForm initialToken="valid-token-12345" />);

      expect(screen.getByText('Accept Workspace Invitation')).toBeInTheDocument();
      const nameInput = screen.getByPlaceholderText('Jane Doe');
      const passInputs = screen.getAllByPlaceholderText('••••••••••••');

      fireEvent.change(nameInput, { target: { value: 'Jane Doe' } });
      fireEvent.change(passInputs[0], { target: { value: 'Password123!' } });
      fireEvent.change(passInputs[1], { target: { value: 'MismatchPassword!' } });

      const submitBtn = screen.getByRole('button', { name: /activate account & join/i });
      fireEvent.click(submitBtn);

      expect(screen.getByText('Passwords do not match.')).toBeInTheDocument();
      expect(invitationService.acceptInvitation).not.toHaveBeenCalled();
    });
  });

  describe('OrgSettingsView Component', () => {
    it('renders tabs and loads existing organization profile', async () => {
      vi.mocked(orgService.getCurrentOrganization).mockResolvedValueOnce({
        success: true,
        message: 'Loaded',
        data: {
          id: 'org-1',
          name: 'Wayne Enterprises',
          domain: 'wayne.com',
          industry: 'Defense & Technology',
          is_active: true,
          created_at: '2026-10-10T10:00:00Z',
        },
      });

      render(<OrgSettingsView />);

      await waitFor(() => {
        expect(screen.getByText('Workspace Settings')).toBeInTheDocument();
      });
      expect(screen.getByDisplayValue('Wayne Enterprises')).toBeInTheDocument();
      expect(screen.getByDisplayValue('wayne.com')).toBeInTheDocument();
      expect(screen.getByText('Security & Auth')).toBeInTheDocument();
      expect(screen.getByText('AI Governance')).toBeInTheDocument();
    });
  });
});
