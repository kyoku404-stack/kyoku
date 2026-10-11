import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { orgService } from '@/services/orgService';
import { departmentService } from '@/services/departmentService';
import { teamService } from '@/services/teamService';
import { projectService } from '@/services/projectService';
import { memberService } from '@/services/memberService';
import { DepartmentManager } from '@/features/organization/DepartmentManager';
import { TeamManager } from '@/features/organization/TeamManager';
import { ProjectWorkspaceView } from '@/features/organization/ProjectWorkspaceView';
import { MemberListTable } from '@/features/organization/MemberListTable';
import { OrgSettingsView } from '@/features/organization/OrgSettingsView';
import {
  Building2,
  Layers,
  Users2,
  FolderKanban,
  Users,
  Settings,
  PlusCircle,
  Activity,
} from 'lucide-react';
import type { OrganizationResponse } from '@/types/organization';

export const OrganizationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'departments' | 'teams' | 'projects' | 'members' | 'settings'>('overview');
  const [org, setOrg] = useState<OrganizationResponse | null>(null);
  const [counts, setCounts] = useState({
    departments: 0,
    teams: 0,
    projects: 0,
    members: 0,
  });

  useEffect(() => {
    const loadOverview = async () => {
      try {
        const [orgRes, deptRes, teamRes, projRes, memRes] = await Promise.all([
          orgService.getCurrentOrganization().catch(() => null),
          departmentService.listDepartments(0, 100).catch(() => ({ data: [] })),
          teamService.listTeams().catch(() => ({ data: [] })),
          projectService.listProjects().catch(() => ({ data: [] })),
          memberService.listMembers({ page: 1, page_size: 1 }).catch(() => ({ data: { total: 0 } })),
        ]);

        if (orgRes?.data) setOrg(orgRes.data);
        setCounts({
          departments: deptRes?.data?.length || 0,
          teams: Array.isArray(teamRes?.data)
            ? teamRes.data.length
            : teamRes?.data?.total || 0,
          projects: Array.isArray(projRes?.data)
            ? projRes.data.length
            : (projRes?.data && typeof projRes.data === 'object' && 'total' in projRes.data)
            ? Number((projRes.data as { total?: number }).total || 0)
            : 0,
          members: memRes?.data?.total || 0,
        });
      } catch {
        // Fallback gracefully
      }
    };
    loadOverview();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold text-xl">
            {org?.logo_url ? (
              <img src={org.logo_url} alt={org.name} className="w-8 h-8 rounded-lg object-cover" />
            ) : (
              <Building2 className="w-6 h-6" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-foreground">{org?.name || 'Workspace Organization'}</h1>
              <Badge variant="success">Tenant Active</Badge>
              {org?.domain && <Badge variant="outline">{org.domain}</Badge>}
            </div>
            <p className="text-sm text-muted-foreground">
              {org?.description || 'Enterprise Multi-Tenant Knowledge Hub & Workspace Management.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => (window.location.href = '/organization/setup')}>
            <PlusCircle className="w-4 h-4 mr-1.5" /> Setup Wizard
          </Button>
          <Button variant="primary" size="sm" onClick={() => setActiveTab('settings')}>
            <Settings className="w-4 h-4 mr-1.5" /> Org Settings
          </Button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-border overflow-x-auto">
        <button
          className={`py-2.5 px-4 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
            activeTab === 'overview'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('overview')}
        >
          <Activity className="w-4 h-4" /> Overview
        </button>
        <button
          className={`py-2.5 px-4 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
            activeTab === 'departments'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('departments')}
        >
          <Layers className="w-4 h-4" /> Departments ({counts.departments})
        </button>
        <button
          className={`py-2.5 px-4 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
            activeTab === 'teams'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('teams')}
        >
          <Users2 className="w-4 h-4" /> Teams ({counts.teams})
        </button>
        <button
          className={`py-2.5 px-4 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
            activeTab === 'projects'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('projects')}
        >
          <FolderKanban className="w-4 h-4" /> Workspaces & Projects ({counts.projects})
        </button>
        <button
          className={`py-2.5 px-4 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
            activeTab === 'members'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('members')}
        >
          <Users className="w-4 h-4" /> Members ({counts.members})
        </button>
        <button
          className={`py-2.5 px-4 text-sm font-medium border-b-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
            activeTab === 'settings'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('settings')}
        >
          <Settings className="w-4 h-4" /> Settings
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Quick Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card
              className="p-4 hover:border-primary/50 transition-colors cursor-pointer"
              onClick={() => setActiveTab('departments')}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-muted-foreground uppercase font-semibold">Departments</div>
                  <div className="text-2xl font-bold mt-1 text-foreground">{counts.departments}</div>
                </div>
                <div className="p-3 rounded-lg bg-primary/10 text-primary">
                  <Layers className="w-6 h-6" />
                </div>
              </div>
            </Card>

            <Card
              className="p-4 hover:border-primary/50 transition-colors cursor-pointer"
              onClick={() => setActiveTab('teams')}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-muted-foreground uppercase font-semibold">Operational Teams</div>
                  <div className="text-2xl font-bold mt-1 text-foreground">{counts.teams}</div>
                </div>
                <div className="p-3 rounded-lg bg-sky-500/10 text-sky-500">
                  <Users2 className="w-6 h-6" />
                </div>
              </div>
            </Card>

            <Card
              className="p-4 hover:border-primary/50 transition-colors cursor-pointer"
              onClick={() => setActiveTab('projects')}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-muted-foreground uppercase font-semibold">Workspaces</div>
                  <div className="text-2xl font-bold mt-1 text-foreground">{counts.projects}</div>
                </div>
                <div className="p-3 rounded-lg bg-emerald-500/10 text-emerald-500">
                  <FolderKanban className="w-6 h-6" />
                </div>
              </div>
            </Card>

            <Card
              className="p-4 hover:border-primary/50 transition-colors cursor-pointer"
              onClick={() => setActiveTab('members')}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-muted-foreground uppercase font-semibold">Active Members</div>
                  <div className="text-2xl font-bold mt-1 text-foreground">{counts.members}</div>
                </div>
                <div className="p-3 rounded-lg bg-amber-500/10 text-amber-500">
                  <Users className="w-6 h-6" />
                </div>
              </div>
            </Card>
          </div>

          {/* Hierarchy Structure Preview */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold">Multi-Tenant Hierarchy Blueprint</CardTitle>
              <CardDescription>
                KEEP enforces strict row-level tenant isolation across four cascading scopes.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
                <div className="p-4 rounded-xl border border-border bg-muted/20">
                  <Building2 className="w-8 h-8 text-primary mx-auto mb-2" />
                  <div className="font-semibold text-sm">1. Organization</div>
                  <p className="text-xs text-muted-foreground mt-1">Tenant quarantine boundary & global AI governance.</p>
                </div>
                <div className="p-4 rounded-xl border border-border bg-muted/20">
                  <Layers className="w-8 h-8 text-sky-500 mx-auto mb-2" />
                  <div className="font-semibold text-sm">2. Department</div>
                  <p className="text-xs text-muted-foreground mt-1">Business division scoping & shared department memory.</p>
                </div>
                <div className="p-4 rounded-xl border border-border bg-muted/20">
                  <Users2 className="w-8 h-8 text-indigo-500 mx-auto mb-2" />
                  <div className="font-semibold text-sm">3. Team</div>
                  <p className="text-xs text-muted-foreground mt-1">Operational squad grouping & team lead access rules.</p>
                </div>
                <div className="p-4 rounded-xl border border-border bg-muted/20">
                  <FolderKanban className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                  <div className="font-semibold text-sm">4. Project Workspace</div>
                  <p className="text-xs text-muted-foreground mt-1">Granular collaboration unit for documents, chats & tasks.</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'departments' && <DepartmentManager />}
      {activeTab === 'teams' && <TeamManager />}
      {activeTab === 'projects' && <ProjectWorkspaceView />}
      {activeTab === 'members' && <MemberListTable />}
      {activeTab === 'settings' && <OrgSettingsView />}
    </div>
  );
};

export default OrganizationPage;
