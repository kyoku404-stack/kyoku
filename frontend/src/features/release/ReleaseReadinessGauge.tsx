/**
 * KEEP Enterprise Platform — Phase 3.7 Pre-Flight Release Readiness Gauge Component.
 *
 * Visual circular gauge and granular subsystem gate status cards.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Cpu,
  Database,
  HardDrive,
  Layers,
  RefreshCw,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import type { PreflightCheckDetail, SystemReadinessData } from '@/types/release';

interface ReleaseReadinessGaugeProps {
  readiness: SystemReadinessData | null;
  loading: boolean;
  onRefresh: () => void;
  onOpenReleaseModal?: () => void;
  canDeploy?: boolean;
}

export const ReleaseReadinessGauge: React.FC<ReleaseReadinessGaugeProps> = ({
  readiness,
  loading,
  onRefresh,
  onOpenReleaseModal,
  canDeploy = true,
}) => {
  const [expandedCheck, setExpandedCheck] = useState<string | null>(null);

  const score = readiness ? Math.round(readiness.overall_score * 100) : 0;
  const isReady = readiness?.is_ready ?? false;

  const getCheckIcon = (name: string) => {
    switch (name) {
      case 'database_migrations':
      case 'database_pool':
        return <Database className="w-5 h-5 text-indigo-500" />;
      case 'redis_cache':
        return <Zap className="w-5 h-5 text-amber-500" />;
      case 'storage_headroom':
        return <HardDrive className="w-5 h-5 text-blue-500" />;
      case 'vector_database':
        return <Layers className="w-5 h-5 text-purple-500" />;
      case 'ai_model_cache':
        return <Cpu className="w-5 h-5 text-teal-500" />;
      case 'security_audit':
        return <ShieldCheck className="w-5 h-5 text-emerald-500" />;
      default:
        return <Layers className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PASSED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            PASSED
          </span>
        );
      case 'WARNING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
            WARNING
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300">
            <AlertCircle className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400" />
            FAILED
          </span>
        );
    }
  };

  const toggleExpand = (checkName: string) => {
    setExpandedCheck(expandedCheck === checkName ? null : checkName);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-gray-100 dark:border-gray-700/60 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Pre-Flight Release Readiness Gate
            </h2>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                isReady
                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                  : 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300'
              }`}
            >
              {isReady ? 'Ready for Deployment' : 'Deployment Blocked'}
            </span>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Automated verification across persistence, cache cluster, vector index, AI models, and cybersecurity compliance.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onRefresh}
            disabled={loading}
            aria-label="Refresh Readiness Probe"
            className="inline-flex items-center gap-2 px-3.5 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh Probe
          </button>

          {onOpenReleaseModal && (
            <button
              onClick={onOpenReleaseModal}
              disabled={!isReady || !canDeploy}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Zap className="w-4 h-4" />
              Deploy Release v{readiness?.target_version || '1.0.0'}
            </button>
          )}
        </div>
      </div>

      {/* Main Readiness Gauge and Meta Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
        {/* Radial Meter Card */}
        <div className="flex flex-col items-center justify-center p-6 bg-gradient-to-b from-gray-50 to-white dark:from-gray-900/50 dark:to-gray-800 rounded-xl border border-gray-100 dark:border-gray-700">
          <div className="relative w-36 h-36 flex items-center justify-center">
            {/* Background Circle */}
            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="40"
                stroke="currentColor"
                strokeWidth="10"
                className="text-gray-200 dark:text-gray-700"
                fill="none"
              />
              <circle
                cx="50"
                cy="50"
                r="40"
                stroke="currentColor"
                strokeWidth="10"
                strokeDasharray={`${2 * Math.PI * 40}`}
                strokeDashoffset={`${2 * Math.PI * 40 * (1 - (readiness?.overall_score ?? 0))}`}
                strokeLinecap="round"
                className={
                  isReady
                    ? 'text-emerald-500 transition-all duration-1000 ease-out'
                    : 'text-amber-500 transition-all duration-1000 ease-out'
                }
                fill="none"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-3xl font-extrabold text-gray-900 dark:text-white">
                {score}%
              </span>
              <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Score
              </span>
            </div>
          </div>
          <p className="mt-3 text-xs font-medium text-gray-500 dark:text-gray-400">
            SLA Threshold: 90% Required
          </p>
        </div>

        {/* Release Metadata */}
        <div className="col-span-2 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <span className="text-xs text-gray-500 dark:text-gray-400 block font-medium">Target Version</span>
            <span className="text-lg font-bold text-gray-900 dark:text-white mt-0.5 block font-mono">
              v{readiness?.target_version ?? '1.0.0'}
            </span>
          </div>

          <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <span className="text-xs text-gray-500 dark:text-gray-400 block font-medium">Git Commit</span>
            <span className="text-lg font-bold text-gray-900 dark:text-white mt-0.5 block font-mono truncate">
              {readiness?.git_commit ?? '8767c08'}
            </span>
          </div>

          <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <span className="text-xs text-gray-500 dark:text-gray-400 block font-medium">Evaluated Subsystems</span>
            <span className="text-lg font-bold text-gray-900 dark:text-white mt-0.5 block">
              {readiness?.checks.length ?? 7} Subsystems
            </span>
          </div>

          <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <span className="text-xs text-gray-500 dark:text-gray-400 block font-medium">Failing Gates</span>
            <span
              className={`text-lg font-bold mt-0.5 block ${
                (readiness?.failing_checks.length ?? 0) === 0
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-rose-600 dark:text-rose-400'
              }`}
            >
              {readiness?.failing_checks.length ?? 0} Critical
            </span>
          </div>
        </div>
      </div>

      {/* Granular Subsystem Check Cards */}
      <div className="space-y-3 pt-2">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider">
          Subsystem Checkpoints
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {readiness?.checks.map((chk: PreflightCheckDetail) => {
            const isExpanded = expandedCheck === chk.check_name;
            return (
              <div
                key={chk.check_name}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-3.5 bg-gray-50/50 dark:bg-gray-800/80 hover:border-indigo-300 dark:hover:border-indigo-600 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-white dark:bg-gray-700 rounded-md shadow-2xs">
                      {getCheckIcon(chk.check_name)}
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white capitalize">
                        {chk.check_name.replace(/_/g, ' ')}
                      </h4>
                      <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                        {chk.category}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {getStatusBadge(chk.status)}
                    <button
                      onClick={() => toggleExpand(chk.check_name)}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"
                      aria-label="Toggle Check Details"
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {isExpanded && chk.details && (
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 text-xs font-mono bg-white dark:bg-gray-900 p-2.5 rounded text-gray-700 dark:text-gray-300 overflow-x-auto">
                    <pre className="whitespace-pre-wrap">{JSON.stringify(chk.details, null, 2)}</pre>
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

