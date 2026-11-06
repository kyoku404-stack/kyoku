/**
 * KEEP Enterprise Platform — Phase 3.7 Production Release & Security Audit Master Page.
 *
 * Operations command center for pre-flight verification, production release deployment,
 * OWASP Top 10 compliance audits, release history timeline, and sponsor demonstration.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  AlertCircle,
  Award,
  CheckCircle2,
  Layers,
  RefreshCw,
  Rocket,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { useReleaseManagement } from '@/hooks/useReleaseManagement';
import {
  ProductionReleaseModal,
  ReleaseHistoryTimeline,
  ReleaseReadinessGauge,
  SecurityAuditSummaryCard,
  SponsorDemoLauncher,
} from '@/features/release';

export const ProductionReleasePage: React.FC = () => {
  const {
    readiness,
    releases,
    securityAudit,
    loading,
    deploying,
    error,
    successMessage,
    setError,
    setSuccessMessage,
    fetchReadiness,
    fetchSecurityAudit,
    triggerRelease,
    refreshAll,
  } = useReleaseManagement();

  const [activeTab, setActiveTab] = useState<'readiness' | 'audit' | 'history' | 'sponsor'>('readiness');
  const [isReleaseModalOpen, setIsReleaseModalOpen] = useState(false);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-xs border border-gray-200 dark:border-gray-700">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-xl">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Production Release & Quality Assurance
                </h1>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300">
                  Phase 3.7 (v1.0.0)
                </span>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Automated pre-flight readiness verification, SemVer release candidate packaging, and enterprise security governance.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => refreshAll()}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>

          <button
            onClick={() => setIsReleaseModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors"
          >
            <Rocket className="w-4 h-4" />
            Deploy Release
          </button>
        </div>
      </div>

      {/* Success Notification Banner */}
      {successMessage && (
        <div className="p-4 bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-700/50 rounded-xl flex items-center justify-between text-xs text-emerald-800 dark:text-emerald-200">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <span>{successMessage}</span>
          </div>
          <button
            onClick={() => setSuccessMessage(null)}
            className="text-emerald-700 dark:text-emerald-400 hover:underline font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Error Notification Banner */}
      {error && (
        <div className="p-4 bg-rose-50 dark:bg-rose-900/30 border border-rose-200 dark:border-rose-700/50 rounded-xl flex items-center justify-between text-xs text-rose-800 dark:text-rose-200">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-rose-700 dark:text-rose-400 hover:underline font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setActiveTab('readiness')}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'readiness'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
          }`}
        >
          <Layers className="w-4 h-4" />
          Pre-Flight Readiness
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'audit'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          Security Audit (OWASP Top 10)
        </button>

        <button
          onClick={() => setActiveTab('history')}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'history'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
          }`}
        >
          <Award className="w-4 h-4" />
          Release History ({releases.length})
        </button>

        <button
          onClick={() => setActiveTab('sponsor')}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'sponsor'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          Sponsor Demo Showcase
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === 'readiness' && (
        <div className="space-y-6">
          <ReleaseReadinessGauge
            readiness={readiness}
            loading={loading}
            onRefresh={() => fetchReadiness()}
            onOpenReleaseModal={() => setIsReleaseModalOpen(true)}
            canDeploy={true}
          />
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="space-y-6">
          <SecurityAuditSummaryCard
            audit={securityAudit}
            loading={loading}
            onRefreshAudit={() => fetchSecurityAudit()}
          />
        </div>
      )}

      {activeTab === 'history' && (
        <div className="space-y-6">
          <ReleaseHistoryTimeline
            releases={releases}
            loading={loading}
          />
        </div>
      )}

      {activeTab === 'sponsor' && (
        <div className="space-y-6">
          <SponsorDemoLauncher />
        </div>
      )}

      {/* Release Deployment Modal */}
      <ProductionReleaseModal
        isOpen={isReleaseModalOpen}
        onClose={() => setIsReleaseModalOpen(false)}
        onDeploy={triggerRelease}
        preflightReady={readiness?.is_ready ?? false}
        preflightScore={readiness?.overall_score ?? 0}
        initialVersion={readiness?.target_version ?? '1.0.0'}
        isDeploying={deploying}
      />
    </div>
  );
};

export default ProductionReleasePage;

