import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Modal } from '@/components/ui/modal';
import { departmentService } from '@/services/departmentService';
import { formatDate } from '@/utils/formatters';
import {
  Layers,
  Plus,
  Users,
  FolderGit2,
  Edit2,
  Trash2,
  Search,
  Calendar,
  AlertCircle,
  Building,
} from 'lucide-react';
import type { DepartmentResponse, DepartmentCreate, DepartmentUpdate } from '@/types/department';

export const DepartmentManager: React.FC = () => {
  const [departments, setDepartments] = useState<DepartmentResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Modal States
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedDept, setSelectedDept] = useState<DepartmentResponse | null>(null);

  // Form states
  const [formData, setFormData] = useState<DepartmentCreate>({
    name: '',
    description: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchDepartments = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await departmentService.listDepartments(0, 100);
      setDepartments(res.data);
    } catch (err: any) {
      setErrorMessage(
        err?.response?.data?.error?.message || 'Failed to retrieve department listings.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDepartments();
  }, []);

  const handleOpenCreate = () => {
    setFormData({ name: '', description: '' });
    setCreateModalOpen(true);
  };

  const handleOpenEdit = (dept: DepartmentResponse) => {
    setSelectedDept(dept);
    setFormData({ name: dept.name, description: dept.description || '' });
    setEditModalOpen(true);
  };

  const handleOpenDelete = (dept: DepartmentResponse) => {
    setSelectedDept(dept);
    setDeleteModalOpen(true);
  };

  const handleCreateDepartment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;
    setSubmitting(true);
    try {
      await departmentService.createDepartment(formData);
      setCreateModalOpen(false);
      await fetchDepartments();
    } catch (err: any) {
      setErrorMessage(
        err?.response?.data?.error?.message || 'Failed to create department.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateDepartment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDept || !formData.name?.trim()) return;
    setSubmitting(true);
    try {
      const updatePayload: DepartmentUpdate = {
        name: formData.name,
        description: formData.description,
      };
      await departmentService.updateDepartment(selectedDept.id, updatePayload);
      setEditModalOpen(false);
      await fetchDepartments();
    } catch (err: any) {
      setErrorMessage(
        err?.response?.data?.error?.message || 'Failed to update department.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteDepartment = async () => {
    if (!selectedDept) return;
    setSubmitting(true);
    try {
      await departmentService.deleteDepartment(selectedDept.id);
      setDeleteModalOpen(false);
      await fetchDepartments();
    } catch (err: any) {
      setErrorMessage(
        err?.response?.data?.error?.message ||
          'Failed to remove department. Ensure all associated teams and members are reassigned.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const filteredDepartments = departments.filter((dept) =>
    dept.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (dept.description && dept.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
            <Layers className="w-5 h-5 text-primary" /> Departments
          </h2>
          <p className="text-sm text-muted-foreground">
            Manage functional business units, cross-team collaboration, and workspace boundaries.
          </p>
        </div>
        <Button variant="primary" onClick={handleOpenCreate}>
          <Plus className="w-4 h-4 mr-2" /> Add Department
        </Button>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/30 flex items-center gap-3 text-destructive text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Search Input */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search departments..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Department Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse h-48 bg-muted/40" />
          ))}
        </div>
      ) : filteredDepartments.length === 0 ? (
        <Card className="p-8 text-center text-muted-foreground border-dashed">
          <Building className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p className="font-medium text-lg text-foreground">No departments configured</p>
          <p className="text-sm mt-1">
            Create an enterprise department to organize teams and projects into logical divisions.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDepartments.map((dept) => (
            <Card key={dept.id} className="hover:border-primary/50 transition-all flex flex-col justify-between">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-primary/10 text-primary">
                      <Layers className="w-5 h-5" />
                    </div>
                    <div>
                      <CardTitle className="text-base font-semibold">{dept.name}</CardTitle>
                      <CardDescription className="text-xs">ID: {dept.id.slice(0, 8)}...</CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 w-8 p-0"
                      onClick={() => handleOpenEdit(dept)}
                      title="Edit Department"
                    >
                      <Edit2 className="w-4 h-4 text-muted-foreground hover:text-foreground" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 w-8 p-0 text-destructive hover:bg-destructive/10"
                      onClick={() => handleOpenDelete(dept)}
                      title="Delete Department"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0 text-sm text-muted-foreground flex-1 flex flex-col justify-between">
                <p className="line-clamp-2 mb-4 text-xs font-normal">
                  {dept.description || 'No description provided.'}
                </p>

                <div className="pt-3 border-t border-border flex items-center justify-between text-xs">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1" title="Teams in department">
                      <FolderGit2 className="w-3.5 h-3.5 text-primary" />
                      {dept.team_count ?? 0} teams
                    </span>
                    <span className="flex items-center gap-1" title="Members in department">
                      <Users className="w-3.5 h-3.5 text-secondary-foreground" />
                      {dept.member_count ?? 0} members
                    </span>
                  </div>
                  <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
                    <Calendar className="w-3 h-3" />
                    {formatDate(dept.created_at)}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Create Department"
        description="Add a new business unit to organize organizational teams and workspaces."
      >
        <form onSubmit={handleCreateDepartment} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Department Name *
            </label>
            <Input
              placeholder="e.g. Engineering, Sales, Product"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Description
            </label>
            <textarea
              className="w-full min-h-[80px] p-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Primary responsibilities and focus..."
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={submitting}>
              Create Department
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        title="Edit Department"
        description="Update department details and description."
      >
        <form onSubmit={handleUpdateDepartment} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Department Name *
            </label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
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
        title="Delete Department"
        description={`Are you sure you want to delete ${selectedDept?.name}? This action cannot be undone.`}
      >
        <div className="space-y-4">
          <p className="text-sm text-destructive">
            Deleting this department will remove the hierarchy association for its teams and projects.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" isLoading={submitting} onClick={handleDeleteDepartment}>
              Delete Department
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default DepartmentManager;
