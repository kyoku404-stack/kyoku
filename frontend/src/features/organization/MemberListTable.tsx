import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Modal } from '@/components/ui/modal';
import { memberService } from '@/services/memberService';
import { departmentService } from '@/services/departmentService';
import { teamService } from '@/services/teamService';
import { InviteMemberModal } from './InviteMemberModal';
import { PendingInvitationsList } from './PendingInvitationsList';
import { formatDate } from '@/utils/formatters';
import {
  Users,
  UserPlus,
  Search,
  Layers,
  Users2,
  Edit2,
  Trash2,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  Ban,
} from 'lucide-react';
import type { MemberResponse, MemberUpdate } from '@/types/member';
import type { DepartmentResponse } from '@/types/department';
import type { Team } from '@/types/team';

export const MemberListTable: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'members' | 'invitations'>('members');
  const [members, setMembers] = useState<MemberResponse[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [deptFilter, setDeptFilter] = useState<string>('');
  const [teamFilter, setTeamFilter] = useState<string>('');

  // Department & Team Lookups
  const [departments, setDepartments] = useState<DepartmentResponse[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);

  // Modals
  const [inviteModalOpen, setInviteModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [removeModalOpen, setRemoveModalOpen] = useState(false);
  const [selectedMember, setSelectedMember] = useState<MemberResponse | null>(null);

  // Edit Form
  const [editForm, setEditForm] = useState<MemberUpdate>({
    role: 'Member',
    department_id: null,
    team_id: null,
    is_active: true,
  });
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [invitesRefreshTrigger, setInvitesRefreshTrigger] = useState(0);

  const fetchMembers = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await memberService.listMembers({
        page,
        page_size: pageSize,
        role: roleFilter || undefined,
        department_id: deptFilter || undefined,
        team_id: teamFilter || undefined,
        search: searchQuery || undefined,
      });
      setMembers(res.data.items);
      setTotalCount(res.data.total);
      setTotalPages(res.data.total_pages);
    } catch (err: any) {
      setErrorMessage(
        err?.response?.data?.error?.message || 'Failed to load enterprise members list.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    Promise.all([
      departmentService.listDepartments(0, 100),
      teamService.listTeams(),
    ])
      .then(([deptRes, teamRes]) => {
        setDepartments(deptRes.data);
        setTeams(teamRes.data);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (activeTab === 'members') {
      fetchMembers();
    }
  }, [page, roleFilter, deptFilter, teamFilter, searchQuery, activeTab]);

  const handleOpenEdit = (member: MemberResponse) => {
    setSelectedMember(member);
    setEditForm({
      role: member.role,
      department_id: member.department_id || null,
      team_id: member.team_id || null,
      is_active: member.is_active,
    });
    setEditModalOpen(true);
  };

  const handleOpenRemove = (member: MemberResponse) => {
    setSelectedMember(member);
    setRemoveModalOpen(true);
  };

  const handleUpdateMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMember) return;
    setSubmitting(true);
    try {
      await memberService.updateMember(selectedMember.id, editForm);
      setEditModalOpen(false);
      await fetchMembers();
    } catch (err: any) {
      setErrorMessage(
        err?.response?.data?.error?.message || 'Failed to update member role or assignment.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemoveMember = async () => {
    if (!selectedMember) return;
    setSubmitting(true);
    try {
      await memberService.removeMember(selectedMember.id);
      setRemoveModalOpen(false);
      await fetchMembers();
    } catch (err: any) {
      setErrorMessage(
        err?.response?.data?.error?.message || 'Failed to remove member from organization.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const deptMap = React.useMemo(() => {
    const map = new Map<string, string>();
    departments.forEach((d) => map.set(d.id, d.name));
    return map;
  }, [departments]);

  const teamMap = React.useMemo(() => {
    const map = new Map<string, string>();
    teams.forEach((t) => map.set(t.id, t.name));
    return map;
  }, [teams]);

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'SuperAdmin':
      case 'OrgAdmin':
        return 'destructive';
      case 'ProjectManager':
        return 'warning';
      case 'Member':
        return 'secondary';
      case 'Viewer':
        return 'outline';
      default:
        return 'default';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
            <Users className="w-5 h-5 text-primary" /> Member Management
          </h2>
          <p className="text-sm text-muted-foreground">
            Manage organization accounts, RBAC role permissions, and user department assignments.
          </p>
        </div>
        <Button variant="primary" onClick={() => setInviteModalOpen(true)}>
          <UserPlus className="w-4 h-4 mr-2" /> Invite Member
        </Button>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/30 flex items-center gap-3 text-destructive text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Tab Switcher */}
      <div className="flex border-b border-border">
        <button
          className={`py-2.5 px-4 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'members'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('members')}
        >
          Active Members ({totalCount})
        </button>
        <button
          className={`py-2.5 px-4 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'invitations'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('invitations')}
        >
          Pending Invitations
        </button>
      </div>

      {activeTab === 'invitations' ? (
        <PendingInvitationsList refreshTrigger={invitesRefreshTrigger} />
      ) : (
        <div className="space-y-4">
          {/* Filters Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search name or email..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setPage(1);
                }}
                className="pl-9"
              />
            </div>
            <div>
              <select
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={roleFilter}
                onChange={(e) => {
                  setRoleFilter(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">All Roles</option>
                <option value="SuperAdmin">SuperAdmin</option>
                <option value="OrgAdmin">OrgAdmin</option>
                <option value="ProjectManager">ProjectManager</option>
                <option value="Member">Member</option>
                <option value="Viewer">Viewer</option>
              </select>
            </div>
            <div>
              <select
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={deptFilter}
                onChange={(e) => {
                  setDeptFilter(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">All Departments</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <select
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={teamFilter}
                onChange={(e) => {
                  setTeamFilter(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">All Teams</option>
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Members Table */}
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted/50 text-xs font-semibold uppercase text-muted-foreground border-b border-border">
                  <tr>
                    <th className="px-6 py-3.5">User</th>
                    <th className="px-6 py-3.5">Role</th>
                    <th className="px-6 py-3.5">Department & Team</th>
                    <th className="px-6 py-3.5">Status</th>
                    <th className="px-6 py-3.5">Joined</th>
                    <th className="px-6 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-8 text-center text-muted-foreground">
                        Loading member directory...
                      </td>
                    </tr>
                  ) : members.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-8 text-center text-muted-foreground">
                        No members matching filter criteria.
                      </td>
                    </tr>
                  ) : (
                    members.map((m) => {
                      const deptName = m.department_id ? deptMap.get(m.department_id) : null;
                      const teamName = m.team_id ? teamMap.get(m.team_id) : null;
                      const initials = m.full_name
                        ? m.full_name
                            .split(' ')
                            .map((n) => n[0])
                            .slice(0, 2)
                            .join('')
                            .toUpperCase()
                        : m.email.slice(0, 2).toUpperCase();

                      return (
                        <tr key={m.id} className="hover:bg-muted/30 transition-colors">
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <div className="w-9 h-9 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center text-xs shrink-0">
                                {initials}
                              </div>
                              <div>
                                <div className="font-medium text-foreground">{m.full_name}</div>
                                <div className="text-xs text-muted-foreground">{m.email}</div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <Badge variant={getRoleBadgeVariant(m.role)}>{m.role}</Badge>
                          </td>
                          <td className="px-6 py-4 text-xs">
                            <div className="flex flex-col gap-1">
                              {deptName && (
                                <span className="flex items-center gap-1 text-primary">
                                  <Layers className="w-3 h-3" /> {deptName}
                                </span>
                              )}
                              {teamName && (
                                <span className="flex items-center gap-1 text-muted-foreground">
                                  <Users2 className="w-3 h-3" /> {teamName}
                                </span>
                              )}
                              {!deptName && !teamName && (
                                <span className="text-muted-foreground/60 italic">Unassigned</span>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            {m.is_active ? (
                              <Badge variant="success" className="flex items-center gap-1 w-fit">
                                <CheckCircle2 className="w-3 h-3" /> Active
                              </Badge>
                            ) : (
                              <Badge variant="destructive" className="flex items-center gap-1 w-fit">
                                <Ban className="w-3 h-3" /> Suspended
                              </Badge>
                            )}
                          </td>
                          <td className="px-6 py-4 text-xs text-muted-foreground">
                            {formatDate(m.created_at)}
                          </td>
                          <td className="px-6 py-4 text-right">
                            <div className="flex items-center justify-end gap-1">
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-8 w-8 p-0"
                                onClick={() => handleOpenEdit(m)}
                                title="Edit Role & Assignments"
                              >
                                <Edit2 className="w-4 h-4 text-muted-foreground hover:text-foreground" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-8 w-8 p-0 text-destructive hover:bg-destructive/10"
                                onClick={() => handleOpenRemove(m)}
                                title="Remove User"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-6 py-3 border-t border-border bg-muted/20 text-xs">
                <span className="text-muted-foreground">
                  Showing page {page} of {totalPages} ({totalCount} total members)
                </span>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={page <= 1}
                    onClick={() => setPage(page - 1)}
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={page >= totalPages}
                    onClick={() => setPage(page + 1)}
                  >
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Invite Modal */}
      <InviteMemberModal
        isOpen={inviteModalOpen}
        onClose={() => setInviteModalOpen(false)}
        onInvited={() => {
          setInvitesRefreshTrigger((t) => t + 1);
          setActiveTab('invitations');
        }}
      />

      {/* Edit Member Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        title="Edit Member Assignments"
        description={`Update roles and workspace hierarchy for ${selectedMember?.full_name || selectedMember?.email}.`}
      >
        <form onSubmit={handleUpdateMember} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Role
            </label>
            <select
              className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              value={editForm.role || 'Member'}
              onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
            >
              <option value="SuperAdmin">SuperAdmin</option>
              <option value="OrgAdmin">OrgAdmin</option>
              <option value="ProjectManager">ProjectManager</option>
              <option value="Member">Member</option>
              <option value="Viewer">Viewer</option>
            </select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Department
              </label>
              <select
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={editForm.department_id || ''}
                onChange={(e) =>
                  setEditForm({ ...editForm, department_id: e.target.value || null })
                }
              >
                <option value="">Unassigned</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Team
              </label>
              <select
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={editForm.team_id || ''}
                onChange={(e) =>
                  setEditForm({ ...editForm, team_id: e.target.value || null })
                }
              >
                <option value="">Unassigned</option>
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="pt-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="rounded border-input text-primary focus:ring-primary w-4 h-4"
                checked={editForm.is_active ?? true}
                onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
              />
              <span className="text-sm font-medium text-foreground">
                Account Active (Uncheck to suspend access)
              </span>
            </label>
          </div>

          <div className="flex justify-end gap-2 pt-3">
            <Button type="button" variant="outline" onClick={() => setEditModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={submitting}>
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>

      {/* Remove Member Modal */}
      <Modal
        isOpen={removeModalOpen}
        onClose={() => setRemoveModalOpen(false)}
        title="Remove Member"
        description={`Are you sure you want to remove ${selectedMember?.full_name || selectedMember?.email} from the organization?`}
      >
        <div className="space-y-4">
          <p className="text-sm text-destructive">
            The user will lose immediate access to this organization and all its workspaces.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setRemoveModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" isLoading={submitting} onClick={handleRemoveMember}>
              Remove User
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default MemberListTable;
