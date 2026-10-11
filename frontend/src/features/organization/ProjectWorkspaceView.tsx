import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Modal } from '@/components/ui/modal';
import { projectService } from '@/services/projectService';
import { teamService } from '@/services/teamService';
import { formatDate } from '@/utils/formatters';
import {
  FolderKanban,
  Plus,
  Search,
  Users2,
  Calendar,
  FileText,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Edit2,
  Trash2,
  AlertCircle,
  Archive,
} from 'lucide-react';
import type {
  Project,
  ProjectCreate,
  ProjectUpdate,
  ProjectStatus,
  ProjectPriority,
} from '@/types/project';
import type { Team } from '@/types/team';

export const ProjectWorkspaceView: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [teamFilter, setTeamFilter] = useState<string>('ALL');

  // Modals
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  // Form
  const [formData, setFormData] = useState<ProjectCreate>({
    name: '',
    description: '',
    team_id: null,
    priority: 'MEDIUM',
    timeline: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const [projRes, teamsRes] = await Promise.all([
        projectService.listProjects({
          status: statusFilter !== 'ALL' ? (statusFilter as ProjectStatus) : undefined,
          priority: priorityFilter !== 'ALL' ? (priorityFilter as ProjectPriority) : undefined,
          team_id: teamFilter !== 'ALL' ? teamFilter : undefined,
          search: searchQuery || undefined,
        }),
        teamService.listTeams(),
      ]);

      const items = Array.isArray(projRes.data)
        ? projRes.data
        : (projRes.data as any)?.items || [];
      setProjects(items);
      setTeams(teamsRes.data);
    } catch (err: any) {
      setErrorMessage(
        err?.response?.data?.error?.message || 'Failed to load project workspaces.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [statusFilter, priorityFilter, teamFilter, searchQuery]);

  const handleOpenCreate = () => {
    setFormData({
      name: '',
      description: '',
      team_id: teamFilter !== 'ALL' ? teamFilter : null,
      priority: 'MEDIUM',
      timeline: '',
    });
    setCreateModalOpen(true);
  };

  const handleOpenEdit = (project: Project) => {
    setSelectedProject(project);
    setFormData({
      name: project.name,
      description: project.description || '',
      team_id: project.team_id || null,
      priority: project.priority,
      status: project.status,
      timeline: project.timeline || '',
    });
    setEditModalOpen(true);
  };

  const handleOpenDelete = (project: Project) => {
    setSelectedProject(project);
    setDeleteModalOpen(true);
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;
    setSubmitting(true);
    try {
      await projectService.createProject(formData);
      setCreateModalOpen(false);
      await fetchData();
    } catch (err: any) {
      setErrorMessage(
        err?.response?.data?.error?.message || 'Failed to create project workspace.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProject || !formData.name?.trim()) return;
    setSubmitting(true);
    try {
      const payload: ProjectUpdate = {
        name: formData.name,
        description: formData.description,
        team_id: formData.team_id,
        priority: formData.priority,
        status: formData.status,
        timeline: formData.timeline,
      };
      await projectService.updateProject(selectedProject.id, payload);
      setEditModalOpen(false);
      await fetchData();
    } catch (err: any) {
      setErrorMessage(
        err?.response?.data?.error?.message || 'Failed to update project workspace.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteProject = async () => {
    if (!selectedProject) return;
    setSubmitting(true);
    try {
      await projectService.deleteProject(selectedProject.id);
      setDeleteModalOpen(false);
      await fetchData();
    } catch (err: any) {
      setErrorMessage(
        err?.response?.data?.error?.message || 'Failed to delete project.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const teamMap = React.useMemo(() => {
    const map = new Map<string, string>();
    teams.forEach((t) => map.set(t.id, t.name));
    return map;
  }, [teams]);

  const getStatusBadge = (status: ProjectStatus) => {
    switch (status) {
      case 'ACTIVE':
        return (
          <Badge variant="success" className="flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> Active
          </Badge>
        );
      case 'ARCHIVED':
        return (
          <Badge variant="secondary" className="flex items-center gap-1">
            <Archive className="w-3 h-3" /> Archived
          </Badge>
        );
      case 'COMPLETED':
        return (
          <Badge variant="outline" className="flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> Completed
          </Badge>
        );
      default:
        return <Badge variant="default">{status}</Badge>;
    }
  };

  const getPriorityBadge = (priority: ProjectPriority) => {
    switch (priority) {
      case 'CRITICAL':
        return (
          <Badge variant="destructive" className="flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" /> Critical
          </Badge>
        );
      case 'HIGH':
        return <Badge variant="warning">High</Badge>;
      case 'MEDIUM':
        return <Badge variant="secondary">Medium</Badge>;
      case 'LOW':
        return <Badge variant="outline">Low</Badge>;
      default:
        return <Badge variant="default">{priority}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
            <FolderKanban className="w-5 h-5 text-primary" /> Project Workspaces
          </h2>
          <p className="text-sm text-muted-foreground">
            Collaborative workspaces organizing documents, meeting notes, tasks, and scoped AI intelligence.
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreate}>
          <Plus className="w-4 h-4 mr-2" /> New Project
        </Button>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/30 flex items-center gap-3 text-destructive text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Filter Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        <div className="relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <div>
          <select
            className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="COMPLETED">Completed</option>
            <option value="ARCHIVED">Archived</option>
          </select>
        </div>
        <div>
          <select
            className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
          >
            <option value="ALL">All Priorities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>
        <div>
          <select
            className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            value={teamFilter}
            onChange={(e) => setTeamFilter(e.target.value)}
          >
            <option value="ALL">All Teams</option>
            {teams.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse h-52 bg-muted/40" />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <Card className="p-8 text-center text-muted-foreground border-dashed">
          <FolderKanban className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p className="font-medium text-lg text-foreground">No projects found</p>
          <p className="text-sm mt-1">
            Create an enterprise project workspace to begin indexing documents and collaborating.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((proj) => {
            const teamName = proj.team_id ? teamMap.get(proj.team_id) : null;
            return (
              <Card
                key={proj.id}
                className="hover:border-primary/50 transition-all flex flex-col justify-between group"
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="p-2 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                        <FolderKanban className="w-5 h-5" />
                      </div>
                      <div>
                        <CardTitle className="text-base font-semibold">{proj.name}</CardTitle>
                        <CardDescription className="text-xs">
                          ID: {proj.id.slice(0, 8)}...
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0"
                        onClick={() => handleOpenEdit(proj)}
                        title="Edit Project"
                      >
                        <Edit2 className="w-4 h-4 text-muted-foreground hover:text-foreground" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-destructive hover:bg-destructive/10"
                        onClick={() => handleOpenDelete(proj)}
                        title="Delete Project"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0 text-sm text-muted-foreground flex-1 flex flex-col justify-between">
                  <p className="line-clamp-2 mb-3 text-xs font-normal">
                    {proj.description || 'No description provided.'}
                  </p>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      {teamName ? (
                        <span className="flex items-center gap-1 text-primary font-medium">
                          <Users2 className="w-3.5 h-3.5" /> {teamName}
                        </span>
                      ) : (
                        <span className="text-muted-foreground/60 italic">Unassigned Team</span>
                      )}
                      <div className="flex items-center gap-1.5">
                        {getStatusBadge(proj.status)}
                        {getPriorityBadge(proj.priority)}
                      </div>
                    </div>

                    <div className="pt-3 border-t border-border flex items-center justify-between text-xs">
                      <div className="flex items-center gap-3">
                        <span className="flex items-center gap-1">
                          <FileText className="w-3.5 h-3.5" />
                          {proj.document_count ?? 0} docs
                        </span>
                        {proj.timeline && (
                          <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
                            <Clock className="w-3.5 h-3.5" /> {proj.timeline}
                          </span>
                        )}
                      </div>
                      <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
                        <Calendar className="w-3 h-3" />
                        {formatDate(proj.created_at)}
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
        title="Create Project Workspace"
        description="Initialize a collaborative project for documents and AI agents."
      >
        <form onSubmit={handleCreateProject} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Project Name *
            </label>
            <Input
              placeholder="e.g. Apollo RAG Core, Q3 Financial Audit"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Associated Team
              </label>
              <select
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={formData.team_id || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    team_id: e.target.value ? e.target.value : null,
                  })
                }
              >
                <option value="">No Team (Cross-functional)</option>
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Priority
              </label>
              <select
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={formData.priority || 'MEDIUM'}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    priority: e.target.value as ProjectPriority,
                  })
                }
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Timeline / Milestone
            </label>
            <Input
              placeholder="e.g. Q4 2026, 2-week Sprint"
              value={formData.timeline || ''}
              onChange={(e) => setFormData({ ...formData, timeline: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Description & Objectives
            </label>
            <textarea
              className="w-full min-h-[80px] p-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Workspace objectives and scope..."
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={submitting}>
              Create Project
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        title="Edit Project Workspace"
        description="Update project metadata, status, or assigned team."
      >
        <form onSubmit={handleUpdateProject} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Project Name *
            </label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Status
              </label>
              <select
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={formData.status || 'ACTIVE'}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    status: e.target.value as ProjectStatus,
                  })
                }
              >
                <option value="ACTIVE">Active</option>
                <option value="COMPLETED">Completed</option>
                <option value="ARCHIVED">Archived</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Priority
              </label>
              <select
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={formData.priority || 'MEDIUM'}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    priority: e.target.value as ProjectPriority,
                  })
                }
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Team
              </label>
              <select
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={formData.team_id || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    team_id: e.target.value ? e.target.value : null,
                  })
                }
              >
                <option value="">No Team</option>
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Timeline
            </label>
            <Input
              value={formData.timeline || ''}
              onChange={(e) => setFormData({ ...formData, timeline: e.target.value })}
            />
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
        title="Delete Project Workspace"
        description={`Are you sure you want to delete ${selectedProject?.name}?`}
      >
        <div className="space-y-4">
          <p className="text-sm text-destructive">
            Deleting this workspace will unbind associated documents and meeting sessions.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" isLoading={submitting} onClick={handleDeleteProject}>
              Delete Project
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default ProjectWorkspaceView;
