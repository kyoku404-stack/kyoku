import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Modal } from '@/components/ui/modal';
import { teamService } from '@/services/teamService';
import { departmentService } from '@/services/departmentService';
import { formatDate } from '@/utils/formatters';
import {
  Users2,
  Plus,
  Users,
  Layers,
  Edit2,
  Trash2,
  Search,
  Calendar,
  AlertCircle,
  UserCheck,
} from 'lucide-react';
import type { Team, TeamCreate, TeamUpdate } from '@/types/team';
import type { DepartmentResponse } from '@/types/department';

export const TeamManager: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [departments, setDepartments] = useState<DepartmentResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedDeptFilter, setSelectedDeptFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Modals
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);

  // Form
  const [formData, setFormData] = useState<TeamCreate>({
    name: '',
    description: '',
    department_id: null,
    lead_user_id: null,
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchData = React.useCallback(async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const [teamsRes, deptRes] = await Promise.all([
        teamService.listTeams(
          selectedDeptFilter !== 'ALL' ? { department_id: selectedDeptFilter } : undefined
        ),
        departmentService.listDepartments(0, 100),
      ]);
      const teamItems = Array.isArray(teamsRes.data)
        ? teamsRes.data
        : teamsRes.data?.items || [];
      setTeams(teamItems);
      setDepartments(deptRes.data);
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { error?: { message?: string } } } };
      setErrorMessage(
        errorObj?.response?.data?.error?.message || 'Failed to load team and department data.'
      );
    } finally {
      setLoading(false);
    }
  }, [selectedDeptFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleOpenCreate = () => {
    setFormData({
      name: '',
      description: '',
      department_id: selectedDeptFilter !== 'ALL' ? selectedDeptFilter : null,
      lead_user_id: null,
    });
    setCreateModalOpen(true);
  };

  const handleOpenEdit = (team: Team) => {
    setSelectedTeam(team);
    setFormData({
      name: team.name,
      description: team.description || '',
      department_id: team.department_id || null,
      lead_user_id: team.lead_user_id || null,
    });
    setEditModalOpen(true);
  };

  const handleOpenDelete = (team: Team) => {
    setSelectedTeam(team);
    setDeleteModalOpen(true);
  };

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;
    setSubmitting(true);
    try {
      await teamService.createTeam(formData);
      setCreateModalOpen(false);
      await fetchData();
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { error?: { message?: string } } } };
      setErrorMessage(
        errorObj?.response?.data?.error?.message || 'Failed to create team.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTeam || !formData.name?.trim()) return;
    setSubmitting(true);
    try {
      const payload: TeamUpdate = {
        name: formData.name,
        description: formData.description,
        department_id: formData.department_id,
        lead_user_id: formData.lead_user_id,
      };
      await teamService.updateTeam(selectedTeam.id, payload);
      setEditModalOpen(false);
      await fetchData();
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { error?: { message?: string } } } };
      setErrorMessage(
        errorObj?.response?.data?.error?.message || 'Failed to update team.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteTeam = async () => {
    if (!selectedTeam) return;
    setSubmitting(true);
    try {
      await teamService.deleteTeam(selectedTeam.id);
      setDeleteModalOpen(false);
      await fetchData();
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { error?: { message?: string } } } };
      setErrorMessage(
        errorObj?.response?.data?.error?.message || 'Failed to delete team.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const departmentMap = React.useMemo(() => {
    const map = new Map<string, string>();
    departments.forEach((d) => map.set(d.id, d.name));
    return map;
  }, [departments]);

  const filteredTeams = teams.filter((t) =>
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (t.description && t.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
            <Users2 className="w-5 h-5 text-primary" /> Teams
          </h2>
          <p className="text-sm text-muted-foreground">
            Manage operational teams, assigned department boundaries, and team lead leads.
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreate}>
          <Plus className="w-4 h-4 mr-2" /> Add Team
        </Button>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/30 flex items-center gap-3 text-destructive text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search teams by name or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="w-full sm:w-64">
          <select
            className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            value={selectedDeptFilter}
            onChange={(e) => setSelectedDeptFilter(e.target.value)}
          >
            <option value="ALL">All Departments</option>
            {departments.map((dept) => (
              <option key={dept.id} value={dept.id}>
                {dept.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Teams Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse h-48 bg-muted/40" />
          ))}
        </div>
      ) : filteredTeams.length === 0 ? (
        <Card className="p-8 text-center text-muted-foreground border-dashed">
          <Users2 className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p className="font-medium text-lg text-foreground">No teams found</p>
          <p className="text-sm mt-1">
            Create your first team to group collaborators under a department.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTeams.map((team) => {
            const deptName = team.department_id ? departmentMap.get(team.department_id) : null;
            return (
              <Card key={team.id} className="hover:border-primary/50 transition-all flex flex-col justify-between">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="p-2 rounded-lg bg-primary/10 text-primary">
                        <Users2 className="w-5 h-5" />
                      </div>
                      <div>
                        <CardTitle className="text-base font-semibold">{team.name}</CardTitle>
                        <CardDescription className="text-xs">ID: {team.id.slice(0, 8)}...</CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0"
                        onClick={() => handleOpenEdit(team)}
                        title="Edit Team"
                      >
                        <Edit2 className="w-4 h-4 text-muted-foreground hover:text-foreground" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-destructive hover:bg-destructive/10"
                        onClick={() => handleOpenDelete(team)}
                        title="Delete Team"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0 text-sm text-muted-foreground flex-1 flex flex-col justify-between">
                  <p className="line-clamp-2 mb-3 text-xs font-normal">
                    {team.description || 'No description provided.'}
                  </p>

                  <div className="space-y-2">
                    {deptName && (
                      <div className="flex items-center gap-1.5 text-xs text-primary font-medium">
                        <Layers className="w-3.5 h-3.5" />
                        <span>Department: {deptName}</span>
                      </div>
                    )}

                    <div className="pt-3 border-t border-border flex items-center justify-between text-xs">
                      <div className="flex items-center gap-3">
                        <span className="flex items-center gap-1" title="Members in team">
                          <Users className="w-3.5 h-3.5 text-secondary-foreground" />
                          {team.member_count ?? team.members_count ?? 0} members
                        </span>
                        {team.lead_user_id && (
                          <span className="flex items-center gap-1 text-[11px] text-muted-foreground" title="Team Lead ID">
                            <UserCheck className="w-3.5 h-3.5 text-emerald-500" /> Lead assigned
                          </span>
                        )}
                      </div>
                      <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
                        <Calendar className="w-3 h-3" />
                        {formatDate(team.created_at)}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Create Team"
        description="Establish an operational unit under a department."
      >
        <form onSubmit={handleCreateTeam} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Team Name *
            </label>
            <Input
              placeholder="e.g. Backend Platform, Growth Marketing"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Department Assignment
            </label>
            <select
              className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              value={formData.department_id || ''}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  department_id: e.target.value ? e.target.value : null,
                })
              }
            >
              <option value="">No Department (Unassigned)</option>
              {departments.map((dept) => (
                <option key={dept.id} value={dept.id}>
                  {dept.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Description
            </label>
            <textarea
              className="w-full min-h-[80px] p-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Team mission, core focus, and objectives..."
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={submitting}>
              Create Team
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        title="Edit Team"
        description="Modify team details and department affiliation."
      >
        <form onSubmit={handleUpdateTeam} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Team Name *
            </label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Department Assignment
            </label>
            <select
              className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              value={formData.department_id || ''}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  department_id: e.target.value ? e.target.value : null,
                })
              }
            >
              <option value="">No Department</option>
              {departments.map((dept) => (
                <option key={dept.id} value={dept.id}>
                  {dept.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Description
            </label>
            <textarea
              className="w-full min-h-[80px] p-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setEditModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={submitting}>
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Delete Team"
        description={`Are you sure you want to delete ${selectedTeam?.name}?`}
      >
        <div className="space-y-4">
          <p className="text-sm text-destructive">
            Deleting this team will unassign all its members and projects.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" isLoading={submitting} onClick={handleDeleteTeam}>
              Delete Team
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default TeamManager;
