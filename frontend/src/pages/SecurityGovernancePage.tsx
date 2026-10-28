/**
 * Phase 3.3 Enterprise Security, Compliance, Governance & Data Protection Master Page.
 * Centralized dashboard integrating Zero-Trust MFA, Immutable Audit Trails, RBAC Permissions,
 * Data Classification & PII Redaction, AI Safety Guardrails, Regulatory Compliance, and Threat Monitoring.
 *
 * Aligned with docs/api/api-contract.md Section 15 & devdocs/p3/p3.3.txt
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  ShieldCheck,
  FileText,
  Award,
  Lock,
  Sparkles,
  Users,
} from 'lucide-react';
import { useSecurity } from '@/hooks/useSecurity';
import {
  SecurityMetricsBanner,
  MFASetupModal,
  AuditLogViewer,
  DataClassificationDrawer,
  ComplianceReportCard,
  AIGovernanceInspector,
  SecurityAlertsBanner,
  RolePermissionMatrix,
} from '@/features/security';

type SecurityTabType = 'overview' | 'audit' | 'compliance' | 'classification' | 'ai_safety' | 'roles';

export const SecurityGovernancePage: React.FC = () => {
  const {
    compliance,
    auditLogs,
    auditTotal,
    auditPage,
    rolesMatrix,
    mfaSetup,
    mfaStatus,
    classificationResult,
    aiGovernanceLogs,
    aiGovernanceStats,
    threatAlerts,
    loading,
    error,
    fetchCompliance,
    fetchAuditLogs,
    exportAuditLogs,
    fetchRolesMatrix,
    updateRolePermissions,
    setupMFA,
    verifyMFA,
    disableMFA,
    classifyContent,
    fetchAIGovernance,
    fetchThreatAlerts,
    resolveThreatAlert,
    setRetentionPolicy,
    executeGDPRErasure,
  } = useSecurity();

  const [activeTab, setActiveTab] = useState<SecurityTabType>('overview');
  const [isMFAModalOpen, setIsMFAModalOpen] = useState<boolean>(false);

  const isMFAActive = Boolean(mfaStatus?.is_enabled);

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto w-full">
      {/* Metrics & Action Banner */}
      <SecurityMetricsBanner
        compliance={compliance}
        threatAlerts={threatAlerts}
        aiStats={aiGovernanceStats}
        mfaEnabled={isMFAActive}
        onOpenMFAModal={() => setIsMFAModalOpen(true)}
        onRefresh={() => {
          fetchCompliance();
          fetchThreatAlerts();
          fetchAuditLogs();
          fetchAIGovernance();
        }}
        onExportAudit={exportAuditLogs}
        isLoading={loading}
      />

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-xs text-rose-800 dark:text-rose-300">
          {error}
        </div>
      )}

      {/* Real-Time Security Incident Banner (When active threats exist) */}
      <SecurityAlertsBanner
        alerts={threatAlerts}
        onResolveAlert={resolveThreatAlert}
        isLoading={loading}
      />

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-200 dark:border-slate-800 overflow-x-auto pb-px">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'overview'
              ? 'border-teal-500 text-teal-600 dark:text-teal-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          Governance Overview
        </button>

        <button
          onClick={() => {
            setActiveTab('audit');
            fetchAuditLogs();
          }}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'audit'
              ? 'border-teal-500 text-teal-600 dark:text-teal-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
          }`}
        >
          <FileText className="w-4 h-4" />
          Audit Trail
        </button>

        <button
          onClick={() => setActiveTab('compliance')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'compliance'
              ? 'border-teal-500 text-teal-600 dark:text-teal-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
          }`}
        >
          <Award className="w-4 h-4" />
          Compliance & Retention
        </button>

        <button
          onClick={() => setActiveTab('classification')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'classification'
              ? 'border-teal-500 text-teal-600 dark:text-teal-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
          }`}
        >
          <Lock className="w-4 h-4" />
          Data Protection & PII
        </button>

        <button
          onClick={() => {
            setActiveTab('ai_safety');
            fetchAIGovernance();
          }}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'ai_safety'
              ? 'border-teal-500 text-teal-600 dark:text-teal-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          AI Safety & Guardrails
        </button>

        <button
          onClick={() => {
            setActiveTab('roles');
            fetchRolesMatrix();
          }}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'roles'
              ? 'border-teal-500 text-teal-600 dark:text-teal-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
          }`}
        >
          <Users className="w-4 h-4" />
          Access Roles
        </button>
      </div>

      {/* Tab Panels */}
      <div className="flex flex-col gap-6">
        {activeTab === 'overview' && (
          <div className="flex flex-col gap-6">
            <ComplianceReportCard
              compliance={compliance}
              onSetRetentionPolicy={setRetentionPolicy}
              onExecuteErasure={executeGDPRErasure}
              isLoading={loading}
            />
            <AuditLogViewer
              logs={auditLogs.slice(0, 5)}
              total={auditTotal}
              page={auditPage}
              onFetchLogs={fetchAuditLogs}
              onExport={exportAuditLogs}
              isLoading={loading}
            />
          </div>
        )}

        {activeTab === 'audit' && (
          <AuditLogViewer
            logs={auditLogs}
            total={auditTotal}
            page={auditPage}
            onFetchLogs={fetchAuditLogs}
            onExport={exportAuditLogs}
            isLoading={loading}
          />
        )}

        {activeTab === 'compliance' && (
          <ComplianceReportCard
            compliance={compliance}
            onSetRetentionPolicy={setRetentionPolicy}
            onExecuteErasure={executeGDPRErasure}
            isLoading={loading}
          />
        )}

        {activeTab === 'classification' && (
          <DataClassificationDrawer
            onClassify={classifyContent}
            classificationResult={classificationResult}
            isLoading={loading}
          />
        )}

        {activeTab === 'ai_safety' && (
          <AIGovernanceInspector
            logs={aiGovernanceLogs}
            stats={aiGovernanceStats}
            onFetchLogs={fetchAIGovernance}
            isLoading={loading}
          />
        )}

        {activeTab === 'roles' && (
          <RolePermissionMatrix
            rolesMatrix={rolesMatrix}
            onUpdateRolePermissions={updateRolePermissions}
            isLoading={loading}
          />
        )}
      </div>

      {/* MFA Setup / Manage Modal */}
      <MFASetupModal
        isOpen={isMFAModalOpen}
        onClose={() => setIsMFAModalOpen(false)}
        mfaSetup={mfaSetup}
        mfaEnabled={isMFAActive}
        onSetupMFA={setupMFA}
        onVerifyMFA={verifyMFA}
        onDisableMFA={disableMFA}
        isLoading={loading}
      />
    </div>
  );
};

export default SecurityGovernancePage;
