/**
 * Phase 3.3 ComplianceReportCard Component.
 * Multi-standard regulatory compliance reporting (GDPR, ISO 27001, SOC 2, HIPAA),
 * data retention policy management, and GDPR Article 17 Right to Erasure execution.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  Award,
  Clock,
  Trash2,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';
import type {
  ComplianceOverviewData,
  DataRetentionPolicyPayload,
  DataRetentionRuleData,
  GDPRErasureData,
  GDPRErasurePayload,
} from '@/types/security';

interface ComplianceReportCardProps {
  compliance: ComplianceOverviewData | null;
  onSetRetentionPolicy: (payload: DataRetentionPolicyPayload) => Promise<DataRetentionRuleData | undefined>;
  onExecuteErasure: (payload: GDPRErasurePayload) => Promise<GDPRErasureData | undefined>;
  isLoading: boolean;
}

export const ComplianceReportCard: React.FC<ComplianceReportCardProps> = ({
  compliance,
  onSetRetentionPolicy,
  onExecuteErasure,
  isLoading,
}) => {
  const [activeTab, setActiveTab] = useState<'frameworks' | 'retention' | 'erasure'>('frameworks');

  // Retention form state
  const [resourceType, setResourceType] = useState('audit_logs');
  const [retentionDays, setRetentionDays] = useState(365);
  const [actionOnExpiry, setActionOnExpiry] = useState('ANONYMIZE');
  const [retentionSuccess, setRetentionSuccess] = useState<string | null>(null);

  // Erasure form state
  const [erasureUserId, setErasureUserId] = useState('');
  const [erasureReason, setErasureReason] = useState('User requested account deletion under GDPR Art. 17');
  const [erasureSuccess, setErasureSuccess] = useState<string | null>(null);

  const handleRetentionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setRetentionSuccess(null);
    const res = await onSetRetentionPolicy({
      resource_type: resourceType,
      retention_days: Number(retentionDays),
      action_on_expiry: actionOnExpiry,
    });
    if (res) {
      setRetentionSuccess(`Retention policy for '${resourceType}' set to ${retentionDays} days (${actionOnExpiry}).`);
      setTimeout(() => setRetentionSuccess(null), 3000);
    }
  };

  const handleErasureSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!erasureUserId.trim()) return;
    setErasureSuccess(null);
    const res = await onExecuteErasure({
      target_user_id: erasureUserId.trim(),
      reason: erasureReason,
    });
    if (res) {
      setErasureSuccess(`Erasure request ${res.erasure_id} completed successfully at ${new Date(res.completed_at).toLocaleTimeString()}.`);
      setErasureUserId('');
      setTimeout(() => setErasureSuccess(null), 4000);
    }
  };

  const standards = compliance?.standards || [
    { standard: 'GDPR', score: 94.0, status: 'COMPLIANT', controls_passed: 18, controls_total: 20 },
    { standard: 'ISO_27001', score: 92.0, status: 'COMPLIANT', controls_passed: 23, controls_total: 25 },
    { standard: 'SOC_2', score: 95.0, status: 'COMPLIANT', controls_passed: 19, controls_total: 20 },
    { standard: 'HIPAA', score: 90.0, status: 'PARTIAL', controls_passed: 18, controls_total: 20 },
  ];

  return (
    <div className="flex flex-col gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm p-5">
      {/* Header and Navigation Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <Award className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          <div>
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">
              Compliance Framework & Governance Engine
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Regulatory readiness evaluation, automated lifecycle retention, and GDPR erasure
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('frameworks')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition ${
              activeTab === 'frameworks'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Standards
          </button>
          <button
            onClick={() => setActiveTab('retention')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition ${
              activeTab === 'retention'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Retention Rules
          </button>
          <button
            onClick={() => setActiveTab('erasure')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition ${
              activeTab === 'erasure'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            GDPR Erasure
          </button>
        </div>
      </div>

      {/* Tab 1: Frameworks */}
      {activeTab === 'frameworks' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
          {standards.map((std) => (
            <div
              key={std.standard}
              className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50 flex flex-col justify-between"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-slate-900 dark:text-white">
                  {std.standard.replace('_', ' ')}
                </span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    std.status === 'COMPLIANT'
                      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                      : 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
                  }`}
                >
                  {std.status}
                </span>
              </div>

              <div className="mt-3 flex items-baseline justify-between">
                <span className="text-2xl font-black text-slate-900 dark:text-white">
                  {std.score.toFixed(1)}%
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {std.controls_passed}/{std.controls_total} Controls
                </span>
              </div>

              <div className="mt-2 w-full bg-slate-200 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-teal-500 h-1.5 rounded-full transition-all duration-500"
                  style={{ width: `${std.score}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 2: Data Retention Policy */}
      {activeTab === 'retention' && (
        <form onSubmit={handleRetentionSubmit} className="flex flex-col gap-4 max-w-xl pt-2">
          {retentionSuccess && (
            <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-700 dark:text-emerald-300 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>{retentionSuccess}</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Resource Domain
              </label>
              <select
                value={resourceType}
                onChange={(e) => setResourceType(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-teal-500"
              >
                <option value="audit_logs">Audit Logs</option>
                <option value="ai_governance_logs">AI Governance Logs</option>
                <option value="classification_scans">Data Classification Scans</option>
                <option value="threat_alerts">Threat Alerts</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Retention Window (Days)
              </label>
              <input
                type="number"
                min={30}
                max={3650}
                value={retentionDays}
                onChange={(e) => setRetentionDays(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-teal-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Action on Expiry
            </label>
            <select
              value={actionOnExpiry}
              onChange={(e) => setActionOnExpiry(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-teal-500"
            >
              <option value="ANONYMIZE">Anonymize / Redact Identifiers</option>
              <option value="ARCHIVE">Archive to Cold Storage</option>
              <option value="DELETE">Permanent Cryptographic Erasure</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex items-center justify-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-teal-600 hover:bg-teal-700 text-white transition shadow-sm w-fit"
          >
            <Clock className="w-3.5 h-3.5" />
            Apply Retention Policy
          </button>
        </form>
      )}

      {/* Tab 3: GDPR Article 17 Erasure */}
      {activeTab === 'erasure' && (
        <form onSubmit={handleErasureSubmit} className="flex flex-col gap-4 max-w-xl pt-2">
          {erasureSuccess && (
            <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-700 dark:text-emerald-300 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>{erasureSuccess}</span>
            </div>
          )}

          <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-xs text-rose-800 dark:text-rose-300 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">GDPR Article 17 "Right to be Forgotten"</p>
              <p className="mt-0.5 text-[11px] leading-relaxed">
                Executing an erasure will cryptographically redact personal identities, revoke all active sessions, and anonymize user activity while preserving financial audit compliance.
              </p>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Target User ID (UUID)
            </label>
            <input
              type="text"
              placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
              value={erasureUserId}
              onChange={(e) => setErasureUserId(e.target.value)}
              className="w-full px-3 py-2 text-xs font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-rose-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Reason / Regulatory Justification
            </label>
            <input
              type="text"
              value={erasureReason}
              onChange={(e) => setErasureReason(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-rose-500"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading || !erasureUserId.trim()}
            className="inline-flex items-center justify-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-rose-600 hover:bg-rose-700 text-white transition shadow-sm w-fit disabled:opacity-50"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Execute Cryptographic Erasure
          </button>
        </form>
      )}
    </div>
  );
};

export default ComplianceReportCard;
