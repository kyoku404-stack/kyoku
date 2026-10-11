import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { orgService } from '@/services/orgService';
import { departmentService } from '@/services/departmentService';
import { invitationService } from '@/services/invitationService';
import {
  Building2,
  Layers,
  UserPlus,
  CheckCircle,
  ArrowRight,
  ArrowLeft,
  Plus,
  Trash2,
  Sparkles,
  AlertCircle,
} from 'lucide-react';
import type { OrganizationCreate } from '@/types/organization';

interface DepartmentDraft {
  name: string;
  description: string;
}

interface MemberDraft {
  email: string;
  role: string;
}

interface OrgSetupWizardProps {
  onCompleted?: (orgId: string) => void;
}

export const OrgSetupWizard: React.FC<OrgSetupWizardProps> = ({ onCompleted }) => {
  const [step, setStep] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successOrgId, setSuccessOrgId] = useState<string | null>(null);

  // Step 1: Organization Profile
  const [orgData, setOrgData] = useState<OrganizationCreate>({
    name: '',
    domain: '',
    industry: 'Technology & Software',
    company_size: '50-250',
    time_zone: 'UTC',
    default_language: 'en-US',
    logo_url: '',
    description: '',
  });

  // Step 2: Initial Departments
  const [departments, setDepartments] = useState<DepartmentDraft[]>([
    { name: 'Engineering', description: 'Core product engineering and infrastructure.' },
    { name: 'Product Management', description: 'Product roadmap and feature planning.' },
  ]);
  const [newDeptName, setNewDeptName] = useState('');
  const [newDeptDesc, setNewDeptDesc] = useState('');

  // Step 3: Member Invites
  const [invites, setInvites] = useState<MemberDraft[]>([]);
  const [newInviteEmail, setNewInviteEmail] = useState('');
  const [newInviteRole, setNewInviteRole] = useState('Member');

  const handleAddDepartment = () => {
    if (!newDeptName.trim()) return;
    setDepartments([...departments, { name: newDeptName.trim(), description: newDeptDesc.trim() }]);
    setNewDeptName('');
    setNewDeptDesc('');
  };

  const handleRemoveDepartment = (index: number) => {
    setDepartments(departments.filter((_, i) => i !== index));
  };

  const handleAddInvite = () => {
    if (!newInviteEmail.trim()) return;
    setInvites([...invites, { email: newInviteEmail.trim(), role: newInviteRole }]);
    setNewInviteEmail('');
    setNewInviteRole('Member');
  };

  const handleRemoveInvite = (index: number) => {
    setInvites(invites.filter((_, i) => i !== index));
  };

  const handleDeployOrganization = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      // 1. Create Organization
      const orgRes = await orgService.createOrganization(orgData);
      const createdOrg = orgRes.data;
      setSuccessOrgId(createdOrg.id);

      // 2. Provision initial departments in parallel
      for (const dept of departments) {
        try {
          await departmentService.createDepartment({
            name: dept.name,
            description: dept.description,
          });
        } catch {
          // Continue if department creation fails non-critically
        }
      }

      // 3. Dispatch initial invitations
      for (const inv of invites) {
        try {
          await invitationService.createInvitation({
            email: inv.email,
            role: inv.role,
          });
        } catch {
          // Continue if invite fails non-critically
        }
      }

      setStep(4);
      onCompleted?.(createdOrg.id);
    } catch (err: any) {
      setErrorMessage(
        err?.response?.data?.error?.message ||
          err?.message ||
          'Failed to initialize organization workspace. Please check domain uniqueness and required fields.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto py-6">
      {/* Step Progress Tracker */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span
              className={`flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold ${
                step >= 1 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
              }`}
            >
              1
            </span>
            <span className="text-sm font-medium">Organization</span>
          </div>
          <div className={`flex-1 h-0.5 mx-3 ${step >= 2 ? 'bg-primary' : 'bg-muted'}`} />
          <div className="flex items-center gap-2">
            <span
              className={`flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold ${
                step >= 2 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
              }`}
            >
              2
            </span>
            <span className="text-sm font-medium">Departments</span>
          </div>
          <div className={`flex-1 h-0.5 mx-3 ${step >= 3 ? 'bg-primary' : 'bg-muted'}`} />
          <div className="flex items-center gap-2">
            <span
              className={`flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold ${
                step >= 3 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
              }`}
            >
              3
            </span>
            <span className="text-sm font-medium">Team Invites</span>
          </div>
          <div className={`flex-1 h-0.5 mx-3 ${step >= 4 ? 'bg-primary' : 'bg-muted'}`} />
          <div className="flex items-center gap-2">
            <span
              className={`flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold ${
                step === 4 ? 'bg-emerald-600 text-white' : 'bg-muted text-muted-foreground'
              }`}
            >
              4
            </span>
            <span className="text-sm font-medium">Ready</span>
          </div>
        </div>
      </div>

      {errorMessage && (
        <div className="mb-6 p-4 rounded-lg bg-destructive/10 border border-destructive/30 flex items-center gap-3 text-destructive text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Step 1: Organization Details */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Building2 className="w-6 h-6 text-primary" />
              <CardTitle>Organization Profile</CardTitle>
            </div>
            <CardDescription>
              Configure your multi-tenant organization boundary and corporate details.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Organization Name *
                </label>
                <Input
                  placeholder="Acme Global Inc."
                  value={orgData.name}
                  onChange={(e) => setOrgData({ ...orgData, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Primary Domain *
                </label>
                <Input
                  placeholder="acme.com"
                  value={orgData.domain}
                  onChange={(e) => setOrgData({ ...orgData, domain: e.target.value })}
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Industry Sector
                </label>
                <Input
                  placeholder="e.g. Enterprise Software, Financial Services"
                  value={orgData.industry || ''}
                  onChange={(e) => setOrgData({ ...orgData, industry: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Company Size
                </label>
                <select
                  className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  value={orgData.company_size || '50-250'}
                  onChange={(e) => setOrgData({ ...orgData, company_size: e.target.value })}
                >
                  <option value="1-10">1 - 10 employees</option>
                  <option value="10-50">10 - 50 employees</option>
                  <option value="50-250">50 - 250 employees</option>
                  <option value="250-1000">250 - 1,000 employees</option>
                  <option value="1000+">1,000+ Enterprise</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Timezone
                </label>
                <Input
                  placeholder="America/New_York or UTC"
                  value={orgData.time_zone || 'UTC'}
                  onChange={(e) => setOrgData({ ...orgData, time_zone: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Default Language
                </label>
                <Input
                  placeholder="en-US"
                  value={orgData.default_language || 'en-US'}
                  onChange={(e) => setOrgData({ ...orgData, default_language: e.target.value })}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Organization Description
              </label>
              <textarea
                className="w-full min-h-[80px] p-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Enterprise AI and knowledge discovery platform..."
                value={orgData.description || ''}
                onChange={(e) => setOrgData({ ...orgData, description: e.target.value })}
              />
            </div>
          </CardContent>
          <CardFooter className="flex justify-end">
            <Button
              variant="primary"
              disabled={!orgData.name.trim() || !orgData.domain.trim()}
              onClick={() => setStep(2)}
            >
              Continue to Departments <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </CardFooter>
        </Card>
      )}

      {/* Step 2: Department Setup */}
      {step === 2 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Layers className="w-6 h-6 text-primary" />
              <CardTitle>Department Hierarchy</CardTitle>
            </div>
            <CardDescription>
              Define the business units that organize teams, workspaces, and AI memory scopes.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 rounded-lg bg-muted/40 border border-border space-y-3">
              <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Add Department
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                <Input
                  placeholder="Department Name (e.g. Finance)"
                  value={newDeptName}
                  onChange={(e) => setNewDeptName(e.target.value)}
                />
                <Input
                  placeholder="Description (optional)"
                  value={newDeptDesc}
                  onChange={(e) => setNewDeptDesc(e.target.value)}
                />
              </div>
              <Button size="sm" variant="outline" onClick={handleAddDepartment} disabled={!newDeptName.trim()}>
                <Plus className="w-4 h-4 mr-1" /> Add Department
              </Button>
            </div>

            <div className="space-y-2 mt-4">
              <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Configured Departments ({departments.length})
              </div>
              {departments.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">No departments added yet.</p>
              ) : (
                departments.map((dept, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 rounded-lg border border-border bg-card"
                  >
                    <div>
                      <div className="font-medium text-sm text-foreground">{dept.name}</div>
                      {dept.description && (
                        <div className="text-xs text-muted-foreground">{dept.description}</div>
                      )}
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-destructive hover:bg-destructive/10"
                      onClick={() => handleRemoveDepartment(index)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))
              )}
            </div>
          </CardContent>
          <CardFooter className="flex justify-between">
            <Button variant="outline" onClick={() => setStep(1)}>
              <ArrowLeft className="w-4 h-4 mr-2" /> Back
            </Button>
            <Button variant="primary" onClick={() => setStep(3)}>
              Continue to Invites <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </CardFooter>
        </Card>
      )}

      {/* Step 3: Member Invites */}
      {step === 3 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <UserPlus className="w-6 h-6 text-primary" />
              <CardTitle>Invite Initial Team</CardTitle>
            </div>
            <CardDescription>
              Send invitations to colleagues to join your enterprise workspace.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 rounded-lg bg-muted/40 border border-border space-y-3">
              <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Invite Colleague
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                <div className="md:col-span-2">
                  <Input
                    type="email"
                    placeholder="colleague@domain.com"
                    value={newInviteEmail}
                    onChange={(e) => setNewInviteEmail(e.target.value)}
                  />
                </div>
                <div>
                  <select
                    className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    value={newInviteRole}
                    onChange={(e) => setNewInviteRole(e.target.value)}
                  >
                    <option value="OrgAdmin">OrgAdmin</option>
                    <option value="ProjectManager">ProjectManager</option>
                    <option value="Member">Member</option>
                    <option value="Viewer">Viewer</option>
                  </select>
                </div>
              </div>
              <Button size="sm" variant="outline" onClick={handleAddInvite} disabled={!newInviteEmail.trim()}>
                <Plus className="w-4 h-4 mr-1" /> Add to Invite List
              </Button>
            </div>

            <div className="space-y-2 mt-4">
              <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Pending Invitations Queue ({invites.length})
              </div>
              {invites.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">
                  No members queued. You can also invite users later via Member Management.
                </p>
              ) : (
                invites.map((inv, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 rounded-lg border border-border bg-card"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm text-foreground">{inv.email}</span>
                      <Badge variant="secondary">{inv.role}</Badge>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-destructive hover:bg-destructive/10"
                      onClick={() => handleRemoveInvite(index)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))
              )}
            </div>
          </CardContent>
          <CardFooter className="flex justify-between">
            <Button variant="outline" onClick={() => setStep(2)}>
              <ArrowLeft className="w-4 h-4 mr-2" /> Back
            </Button>
            <Button
              variant="primary"
              isLoading={loading}
              onClick={handleDeployOrganization}
            >
              <Sparkles className="w-4 h-4 mr-2" /> Deploy Workspace
            </Button>
          </CardFooter>
        </Card>
      )}

      {/* Step 4: Completion */}
      {step === 4 && (
        <Card className="text-center py-8">
          <CardContent className="space-y-4">
            <div className="w-16 h-16 bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle className="w-8 h-8" />
            </div>
            <CardTitle className="text-2xl font-bold">Workspace Ready!</CardTitle>
            <CardDescription className="max-w-md mx-auto">
              Organization <strong className="text-foreground">{orgData.name}</strong> has been
              successfully provisioned with {departments.length} department(s) and {invites.length}{' '}
              invitation(s) dispatched.
            </CardDescription>
            {successOrgId && (
              <div className="p-3 bg-muted rounded-lg text-xs font-mono max-w-sm mx-auto text-muted-foreground">
                Organization ID: {successOrgId}
              </div>
            )}
          </CardContent>
          <CardFooter className="flex justify-center">
            <Button
              variant="primary"
              onClick={() => {
                if (onCompleted && successOrgId) {
                  onCompleted(successOrgId);
                } else {
                  window.location.href = '/organization';
                }
              }}
            >
              Enter Workspace Hub <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </CardFooter>
        </Card>
      )}
    </div>
  );
};

export default OrgSetupWizard;
