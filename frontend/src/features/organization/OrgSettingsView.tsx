import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { orgService } from '@/services/orgService';
import {
  Settings,
  ShieldCheck,
  Cpu,
  HardDrive,
  Save,
  CheckCircle2,
  AlertCircle,
  Building2,
} from 'lucide-react';
import type {
  OrganizationResponse,
  OrganizationUpdate,
  OrganizationSettings,
} from '@/types/organization';

export const OrgSettingsView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'general' | 'security' | 'ai' | 'limits'>('general');
  const [org, setOrg] = useState<OrganizationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form State
  const [generalForm, setGeneralForm] = useState({
    name: '',
    domain: '',
    industry: '',
    company_size: '',
    time_zone: 'UTC',
    default_language: 'en-US',
    logo_url: '',
    description: '',
    is_active: true,
  });

  const [securityForm, setSecurityForm] = useState({
    enforce_2fa: false,
    session_timeout_minutes: 60,
    password_expiry_days: 90,
    ip_allowlist: '',
  });

  const [aiForm, setAiForm] = useState({
    ai_default_model: 'gemini-1.5-pro',
    ai_token_quota: 5000000,
    ai_memory_scope: 'Organization',
    ai_temperature: 0.2,
  });

  const fetchOrgDetails = React.useCallback(async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await orgService.getCurrentOrganization();
      const data = res.data;
      setOrg(data);

      setGeneralForm({
        name: data.name || '',
        domain: data.domain || '',
        industry: data.industry || 'Technology & Software',
        company_size: data.company_size || '50-250',
        time_zone: data.time_zone || 'UTC',
        default_language: data.default_language || 'en-US',
        logo_url: data.logo_url || '',
        description: data.description || '',
        is_active: data.is_active ?? true,
      });

      const settings: OrganizationSettings = (data.settings as OrganizationSettings) || {};
      setSecurityForm({
        enforce_2fa: settings.enforce_2fa ?? false,
        session_timeout_minutes: settings.session_timeout_minutes ?? 60,
        password_expiry_days: settings.password_expiry_days ?? 90,
        ip_allowlist: Array.isArray(settings.ip_allowlist)
          ? settings.ip_allowlist.join(', ')
          : '',
      });

      setAiForm({
        ai_default_model: settings.ai_default_model || 'gemini-1.5-pro',
        ai_token_quota: data.ai_monthly_token_quota ?? settings.ai_token_quota ?? 5000000,
        ai_memory_scope: settings.ai_memory_scope || 'Organization',
        ai_temperature: settings.ai_temperature ?? 0.2,
      });
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { error?: { message?: string } } } };
      setErrorMessage(
        errorObj?.response?.data?.error?.message ||
          'Failed to load organization settings. Using local tenant state.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOrgDetails();
  }, [fetchOrgDetails]);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!org) return;

    setSaving(true);
    setSuccessMessage(null);
    setErrorMessage(null);

    const mergedSettings: OrganizationSettings = {
      ...(org.settings as OrganizationSettings),
      enforce_2fa: securityForm.enforce_2fa,
      session_timeout_minutes: Number(securityForm.session_timeout_minutes),
      password_expiry_days: Number(securityForm.password_expiry_days),
      ip_allowlist: securityForm.ip_allowlist
        ? securityForm.ip_allowlist.split(',').map((ip) => ip.trim())
        : [],
      ai_default_model: aiForm.ai_default_model,
      ai_token_quota: Number(aiForm.ai_token_quota),
      ai_memory_scope: aiForm.ai_memory_scope,
      ai_temperature: Number(aiForm.ai_temperature),
    };

    const updatePayload: OrganizationUpdate = {
      name: generalForm.name,
      domain: generalForm.domain,
      industry: generalForm.industry,
      company_size: generalForm.company_size,
      time_zone: generalForm.time_zone,
      default_language: generalForm.default_language,
      logo_url: generalForm.logo_url,
      description: generalForm.description,
      is_active: generalForm.is_active,
      settings: mergedSettings,
      ai_monthly_token_quota: Number(aiForm.ai_token_quota),
    };

    try {
      const res = await orgService.updateOrganization(org.id, updatePayload);
      setOrg(res.data);
      setSuccessMessage('Organization workspace settings successfully updated.');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { error?: { message?: string } } } };
      setErrorMessage(
        errorObj?.response?.data?.error?.message || 'Failed to persist organization settings.'
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Card className="animate-pulse h-64 bg-muted/40" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
          <Settings className="w-5 h-5 text-primary" /> Workspace Settings
        </h2>
        <p className="text-sm text-muted-foreground">
          Configure multi-tenant boundaries, security compliance policies, and enterprise AI quotas.
        </p>
      </div>

      {successMessage && (
        <div className="p-4 rounded-lg bg-emerald-100 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-800 flex items-center gap-3 text-emerald-800 dark:text-emerald-300 text-sm">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/30 flex items-center gap-3 text-destructive text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-border">
        <button
          className={`py-2.5 px-4 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'general'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('general')}
        >
          <Building2 className="w-4 h-4" /> General Profile
        </button>
        <button
          className={`py-2.5 px-4 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'security'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('security')}
        >
          <ShieldCheck className="w-4 h-4" /> Security & Auth
        </button>
        <button
          className={`py-2.5 px-4 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'ai'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('ai')}
        >
          <Cpu className="w-4 h-4" /> AI Governance
        </button>
        <button
          className={`py-2.5 px-4 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'limits'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('limits')}
        >
          <HardDrive className="w-4 h-4" /> Quotas & Storage
        </button>
      </div>

      <form onSubmit={handleSaveSettings} className="space-y-6">
        {/* General Tab */}
        {activeTab === 'general' && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold">Tenant Identification</CardTitle>
              <CardDescription>
                Corporate profile and tenant metadata applied across all departments.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                    Organization Name *
                  </label>
                  <Input
                    value={generalForm.name}
                    onChange={(e) => setGeneralForm({ ...generalForm, name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                    Domain *
                  </label>
                  <Input
                    value={generalForm.domain}
                    onChange={(e) => setGeneralForm({ ...generalForm, domain: e.target.value })}
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
                    value={generalForm.industry}
                    onChange={(e) => setGeneralForm({ ...generalForm, industry: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                    Company Size
                  </label>
                  <select
                    className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    value={generalForm.company_size}
                    onChange={(e) => setGeneralForm({ ...generalForm, company_size: e.target.value })}
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
                    value={generalForm.time_zone}
                    onChange={(e) => setGeneralForm({ ...generalForm, time_zone: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                    Default Language
                  </label>
                  <Input
                    value={generalForm.default_language}
                    onChange={(e) => setGeneralForm({ ...generalForm, default_language: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Logo URL
                </label>
                <Input
                  value={generalForm.logo_url}
                  onChange={(e) => setGeneralForm({ ...generalForm, logo_url: e.target.value })}
                  placeholder="https://assets.domain.com/logo.png"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Description
                </label>
                <textarea
                  className="w-full min-h-[80px] p-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  value={generalForm.description}
                  onChange={(e) => setGeneralForm({ ...generalForm, description: e.target.value })}
                />
              </div>

              <div className="pt-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="rounded border-input text-primary focus:ring-primary w-4 h-4"
                    checked={generalForm.is_active}
                    onChange={(e) => setGeneralForm({ ...generalForm, is_active: e.target.checked })}
                  />
                  <span className="text-sm font-medium text-foreground">
                    Tenant Active Status (Uncheck to temporarily freeze organization)
                  </span>
                </label>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Security Tab */}
        {activeTab === 'security' && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold">Security & Access Compliance</CardTitle>
              <CardDescription>
                Enforce authentication guardrails and corporate security governance.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 rounded-lg border border-border bg-muted/30 flex items-center justify-between">
                <div>
                  <div className="font-semibold text-sm text-foreground">
                    Enforce Multi-Factor Authentication (2FA)
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Require TOTP authentication for all members accessing workspace resources.
                  </div>
                </div>
                <input
                  type="checkbox"
                  className="rounded border-input text-primary focus:ring-primary w-5 h-5"
                  checked={securityForm.enforce_2fa}
                  onChange={(e) =>
                    setSecurityForm({ ...securityForm, enforce_2fa: e.target.checked })
                  }
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                    Session Timeout (Minutes)
                  </label>
                  <Input
                    type="number"
                    value={securityForm.session_timeout_minutes}
                    onChange={(e) =>
                      setSecurityForm({
                        ...securityForm,
                        session_timeout_minutes: Number(e.target.value),
                      })
                    }
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                    Password Expiration (Days)
                  </label>
                  <Input
                    type="number"
                    value={securityForm.password_expiry_days}
                    onChange={(e) =>
                      setSecurityForm({
                        ...securityForm,
                        password_expiry_days: Number(e.target.value),
                      })
                    }
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  IP CIDR Allowlist (Comma separated)
                </label>
                <Input
                  placeholder="e.g. 192.168.1.0/24, 10.0.0.0/8"
                  value={securityForm.ip_allowlist}
                  onChange={(e) =>
                    setSecurityForm({ ...securityForm, ip_allowlist: e.target.value })
                  }
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Leave empty to allow logins from any network location.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* AI Governance Tab */}
        {activeTab === 'ai' && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold">AI Workspace Governance</CardTitle>
              <CardDescription>
                Configure memory scoping, foundational models, and retrieval policies.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                    Primary Foundational Model
                  </label>
                  <select
                    className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    value={aiForm.ai_default_model}
                    onChange={(e) => setAiForm({ ...aiForm, ai_default_model: e.target.value })}
                  >
                    <option value="gemini-1.5-pro">Gemini 1.5 Pro (Deep reasoning)</option>
                    <option value="gemini-1.5-flash">Gemini 1.5 Flash (High speed)</option>
                    <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
                    <option value="gpt-4o">GPT-4o</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                    AI Memory Isolation Scope
                  </label>
                  <select
                    className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    value={aiForm.ai_memory_scope}
                    onChange={(e) => setAiForm({ ...aiForm, ai_memory_scope: e.target.value })}
                  >
                    <option value="Organization">Organization-wide (Cross-department knowledge)</option>
                    <option value="Department">Department Boundary (Isolated per department)</option>
                    <option value="Team">Team Boundary (Isolated per team)</option>
                    <option value="Project">Project Workspace Only (Strict quarantine)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Monthly Token Quota
                </label>
                <Input
                  type="number"
                  value={aiForm.ai_token_quota}
                  onChange={(e) => setAiForm({ ...aiForm, ai_token_quota: Number(e.target.value) })}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  RAG Retrieval Temperature: {aiForm.ai_temperature}
                </label>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.05"
                  className="w-full accent-primary"
                  value={aiForm.ai_temperature}
                  onChange={(e) => setAiForm({ ...aiForm, ai_temperature: parseFloat(e.target.value) })}
                />
                <div className="flex justify-between text-[11px] text-muted-foreground mt-1">
                  <span>0.0 (Strict / Deterministic)</span>
                  <span>1.0 (Creative)</span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quotas & Storage Tab */}
        {activeTab === 'limits' && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold">Tier Quotas & Resource Allocation</CardTitle>
              <CardDescription>
                System limits and multi-tenant resource boundaries.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-muted/40 border border-border">
                  <div className="text-xs text-muted-foreground font-semibold uppercase">
                    Subscription Tier
                  </div>
                  <div className="text-xl font-bold mt-1 text-foreground flex items-center gap-2">
                    {org?.subscription_tier || 'ENTERPRISE'}
                    <Badge variant="success">Active</Badge>
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-muted/40 border border-border">
                  <div className="text-xs text-muted-foreground font-semibold uppercase">
                    User Seat Allocation
                  </div>
                  <div className="text-xl font-bold mt-1 text-foreground">
                    {org?.max_users || 500} Seats
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-muted/40 border border-border">
                  <div className="text-xs text-muted-foreground font-semibold uppercase">
                    Storage Boundary
                  </div>
                  <div className="text-xl font-bold mt-1 text-foreground">
                    {org?.max_storage_bytes
                      ? `${(org.max_storage_bytes / (1024 * 1024 * 1024)).toFixed(0)} GB`
                      : '500 GB'}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="flex justify-end">
          <Button type="submit" variant="primary" isLoading={saving}>
            <Save className="w-4 h-4 mr-2" /> Save Workspace Settings
          </Button>
        </div>
      </form>
    </div>
  );
};

export default OrgSettingsView;
