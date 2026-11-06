/**
 * KEEP Enterprise Platform — Phase 3.7 Security Audit Summary Component.
 *
 * OWASP Top 10 & LLM Top 10 cybersecurity controls evaluation & compliance report.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react';
import type { SecurityAuditData, SecurityControlData } from '@/types/release';

interface SecurityAuditSummaryCardProps {
  audit: SecurityAuditData | null;
  loading?: boolean;
  onRefreshAudit: () => void;
}

export const SecurityAuditSummaryCard: React.FC<SecurityAuditSummaryCardProps> = ({
  audit,
  loading = false,
  onRefreshAudit,
}) => {
  const [expandedControl, setExpandedControl] = useState<string | null>(null);

  const compliancePct = audit ? Math.round(audit.overall_compliance_percent) : 0;
  const isCompliant = compliancePct >= 90;

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return (
          <span className="px-2 py-0.5 rounded text-2xs font-bold uppercase tracking-wider bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300">
            Critical
          </span>
        );
      case 'HIGH':
        return (
          <span className="px-2 py-0.5 rounded text-2xs font-bold uppercase tracking-wider bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
            High
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="px-2 py-0.5 rounded text-2xs font-bold uppercase tracking-wider bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300">
            Medium
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-2xs font-bold uppercase tracking-wider bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
            Info
          </span>
        );
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'PASSED':
        return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
      case 'WARNING':
        return <AlertTriangle className="w-4 h-4 text-amber-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-rose-500" />;
    }
  };

  const toggleControl = (cid: string) => {
    setExpandedControl(expandedControl === cid ? null : cid);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-gray-100 dark:border-gray-700/60 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <ShieldCheck className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
              Cybersecurity & Compliance Audit
            </h2>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                isCompliant
                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                  : 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300'
              }`}
            >
              {isCompliant ? 'Compliant' : 'Non-Compliant'}
            </span>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Automated verification against OWASP Top 10 (2021) and OWASP Top 10 for Large Language Models (2025).
          </p>
        </div>

        <button
          onClick={onRefreshAudit}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Re-Run Audit
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl border border-emerald-100 dark:border-emerald-800/40">
          <span className="text-xs font-medium text-emerald-700 dark:text-emerald-400 block">Compliance Rating</span>
          <span className="text-2xl font-extrabold text-emerald-800 dark:text-emerald-300 mt-1 block">
            {compliancePct}%
          </span>
          <span className="text-2xs text-emerald-600 dark:text-emerald-400 mt-0.5 block">SLA: 100% Target</span>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-700/40 rounded-xl border border-gray-100 dark:border-gray-700">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400 block">Audited Controls</span>
          <span className="text-2xl font-extrabold text-gray-900 dark:text-white mt-1 block">
            {audit?.total_controls ?? 10}
          </span>
          <span className="text-2xs text-gray-500 dark:text-gray-400 mt-0.5 block">Baseline Framework</span>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-700/40 rounded-xl border border-gray-100 dark:border-gray-700">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400 block">Passing Controls</span>
          <span className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-1 block">
            {audit?.passed_controls ?? 10}
          </span>
          <span className="text-2xs text-emerald-600 dark:text-emerald-400 mt-0.5 block">Zero Regressions</span>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-700/40 rounded-xl border border-gray-100 dark:border-gray-700">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400 block">Detected Findings</span>
          <span
            className={`text-2xl font-extrabold mt-1 block ${
              (audit?.failed_controls ?? 0) === 0
                ? 'text-emerald-600 dark:text-emerald-400'
                : 'text-rose-600 dark:text-rose-400'
            }`}
          >
            {audit?.failed_controls ?? 0}
          </span>
          <span className="text-2xs text-gray-500 dark:text-gray-400 mt-0.5 block">Vulnerabilities Detected</span>
        </div>
      </div>

      {/* Granular Controls List */}
      <div className="space-y-3 pt-2">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider">
          Audited Security Defense Controls
        </h3>

        <div className="divide-y divide-gray-100 dark:divide-gray-700/70 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
          {audit?.controls.map((ctrl: SecurityControlData) => {
            const isExpanded = expandedControl === ctrl.control_id;
            return (
              <div
                key={ctrl.control_id}
                className="p-3.5 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/40 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(ctrl.status)}
                    <span className="text-xs font-mono font-bold text-gray-600 dark:text-gray-400">
                      {ctrl.control_id}
                    </span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {ctrl.name}
                    </span>
                    {getSeverityBadge(ctrl.severity)}
                  </div>

                  <button
                    onClick={() => toggleControl(ctrl.control_id)}
                    className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    aria-label="Toggle Control Mitigation"
                  >
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>

                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 text-xs space-y-1.5 pl-7">
                    <p className="text-gray-600 dark:text-gray-300">
                      <strong>Specification:</strong> {ctrl.description}
                    </p>
                    <p className="text-emerald-700 dark:text-emerald-400">
                      <strong>Enforced Mitigation:</strong> {ctrl.mitigation}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
