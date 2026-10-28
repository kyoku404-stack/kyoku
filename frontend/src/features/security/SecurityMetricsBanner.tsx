/**
 * Phase 3.3 SecurityMetricsBanner Component.
 * Displays high-level KPIs: Compliance Score, Active Threat Alerts, MFA Status, and AI Safety Rating.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  KeyRound,
  Sparkles,
  RefreshCw,
  Download,
  AlertTriangle,
} from 'lucide-react';
import type { ComplianceOverviewData, SecurityThreatAlertItem, AIGovernanceStatsData } from '@/types/security';

interface SecurityMetricsBannerProps {
  compliance: ComplianceOverviewData | null;
  threatAlerts: SecurityThreatAlertItem[];
  aiStats: AIGovernanceStatsData | null;
  mfaEnabled: boolean;
  onOpenMFAModal: () => void;
  onRefresh: () => void;
  onExportAudit: (format: 'json' | 'csv') => void;
  isLoading: boolean;
}

export const SecurityMetricsBanner: React.FC<SecurityMetricsBannerProps> = ({
  compliance,
  threatAlerts,
  aiStats,
  mfaEnabled,
  onOpenMFAModal,
  onRefresh,
  onExportAudit,
  isLoading,
}) => {
  const activeAlertsCount = threatAlerts.filter((a) => !a.resolved).length;
  const complianceScore = compliance?.overall_compliance_score ?? 94.5;
  const safetyPercentage = aiStats?.safety_score_percentage ?? 99.2;

  return (
    <div className="flex flex-col gap-5">
      {/* Top Header & Actions */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-lg shadow-emerald-500/20">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Enterprise Security & Governance
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Zero-Trust Identity, Real-Time Compliance, AI Guardrails & Sensitive Data Protection
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => onExportAudit('csv')}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            Export Audit (CSV)
          </button>
          <button
            onClick={onOpenMFAModal}
            className={`inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg text-white shadow-sm transition ${
              mfaEnabled
                ? 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/20'
                : 'bg-amber-600 hover:bg-amber-700 shadow-amber-600/20'
            }`}
          >
            <KeyRound className="w-3.5 h-3.5" />
            {mfaEnabled ? 'MFA Active' : 'Setup MFA'}
          </button>
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition shadow-sm"
            title="Refresh Security Telemetry"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Compliance Rating Card */}
        <div className="p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/60 backdrop-blur-sm shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            <span>Compliance Score</span>
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 dark:text-white">
              {complianceScore.toFixed(1)}%
            </span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
              SOC 2 / GDPR
            </span>
          </div>
          <div className="mt-3 w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-emerald-500 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(complianceScore, 100)}%` }}
            />
          </div>
        </div>

        {/* Threat Alerts Card */}
        <div className="p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/60 backdrop-blur-sm shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            <span>Threat Incidents</span>
            {activeAlertsCount > 0 ? (
              <AlertTriangle className="w-4 h-4 text-rose-500 animate-pulse" />
            ) : (
              <ShieldAlert className="w-4 h-4 text-slate-400" />
            )}
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span
              className={`text-3xl font-extrabold ${
                activeAlertsCount > 0
                  ? 'text-rose-600 dark:text-rose-400'
                  : 'text-slate-900 dark:text-white'
              }`}
            >
              {activeAlertsCount}
            </span>
            <span
              className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                activeAlertsCount > 0
                  ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300'
                  : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
              }`}
            >
              {activeAlertsCount > 0 ? 'Requires Action' : 'System Secure'}
            </span>
          </div>
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
            Real-time anomaly & brute force detection
          </p>
        </div>

        {/* AI Guardrail Safety Rating */}
        <div className="p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/60 backdrop-blur-sm shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            <span>AI Safety Index</span>
            <Sparkles className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 dark:text-white">
              {safetyPercentage.toFixed(1)}%
            </span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300">
              {aiStats?.guardrail_blocks ?? 0} Blocked
            </span>
          </div>
          <div className="mt-3 w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-indigo-500 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(safetyPercentage, 100)}%` }}
            />
          </div>
        </div>

        {/* Zero-Trust MFA Status */}
        <div className="p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/60 backdrop-blur-sm shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            <span>MFA Enforcement</span>
            <KeyRound className="w-4 h-4 text-teal-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 dark:text-white">
              {mfaEnabled ? 'Enforced' : 'Optional'}
            </span>
            <span
              className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                mfaEnabled
                  ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300'
                  : 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300'
              }`}
            >
              RFC 6238 TOTP
            </span>
          </div>
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
            {mfaEnabled
              ? 'Multi-factor authentication active'
              : 'Protect your account with 2FA'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default SecurityMetricsBanner;
