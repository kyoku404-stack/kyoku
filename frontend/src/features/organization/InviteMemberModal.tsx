import React, { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { invitationService } from '@/services/invitationService';
import { departmentService } from '@/services/departmentService';
import { teamService } from '@/services/teamService';
import { Mail, Shield, Layers, Users2, AlertCircle } from 'lucide-react';
import type { InvitationCreate } from '@/types/invitation';
import type { DepartmentResponse } from '@/types/department';
import type { Team } from '@/types/team';

interface InviteMemberModalProps {
  isOpen: boolean;
  onClose: () => void;
  onInvited?: () => void;
}

export const InviteMemberModal: React.FC<InviteMemberModalProps> = ({
  isOpen,
  onClose,
  onInvited,
}) => {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('Member');
  const [departmentId, setDepartmentId] = useState<string>('');
  const [teamId, setTeamId] = useState<string>('');
  const [departments, setDepartments] = useState<DepartmentResponse[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setEmail('');
      setRole('Member');
      setDepartmentId('');
      setTeamId('');
      setErrorMessage(null);

      // Fetch options
      Promise.all([
        departmentService.listDepartments(0, 100),
        teamService.listTeams(),
      ])
        .then(([deptRes, teamsRes]) => {
          setDepartments(deptRes.data);
          const teamItems = Array.isArray(teamsRes.data)
            ? teamsRes.data
            : teamsRes.data?.items || [];
          setTeams(teamItems);
        })
        .catch(() => {});
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setSubmitting(true);
    setErrorMessage(null);

    const payload: InvitationCreate = {
      email: email.trim(),
      role,
      department_id: departmentId ? departmentId : null,
      team_id: teamId ? teamId : null,
    };

    try {
      await invitationService.createInvitation(payload);
      onInvited?.();
      onClose();
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      setErrorMessage(
        errorObj?.response?.data?.error?.message ||
          errorObj?.message ||
          'Failed to dispatch invitation. Please check the email address and permissions.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Invite New Team Member"
      description="Send a secure invitation link to welcome a new collaborator to this workspace."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {errorMessage && (
          <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/30 flex items-center gap-2 text-destructive text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
            Email Address *
          </label>
          <div className="relative">
            <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              type="email"
              placeholder="colleague@domain.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="pl-9"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
            Assigned Role
          </label>
          <div className="relative">
            <Shield className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <select
              className="w-full h-10 pl-9 pr-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              <option value="Viewer">Viewer (Read-only)</option>
              <option value="Member">Member (Standard collaborator)</option>
              <option value="ProjectManager">Project Manager (Workspace lead)</option>
              <option value="OrgAdmin">Org Admin (Full administrative access)</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Department
            </label>
            <div className="relative">
              <Layers className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <select
                className="w-full h-10 pl-9 pr-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={departmentId}
                onChange={(e) => setDepartmentId(e.target.value)}
              >
                <option value="">None (Unassigned)</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Team
            </label>
            <div className="relative">
              <Users2 className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <select
                className="w-full h-10 pl-9 pr-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={teamId}
                onChange={(e) => setTeamId(e.target.value)}
              >
                <option value="">None (Unassigned)</option>
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-3">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" isLoading={submitting}>
            Send Invitation
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default InviteMemberModal;
