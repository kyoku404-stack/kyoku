/**
 * Phase 2.5 Knowledge Health Gauge & Decomposition Visualizer.
 * Displays overall KHS (0-100), categorical performance tiers, factor bars,
 * department health breakdown, and identified operational gaps.
 *
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import type { HealthScoreBreakdown } from '@/types/intelligence';
import { Activity, AlertTriangle, CheckCircle, ShieldAlert, Sparkles } from 'lucide-react';

interface KnowledgeHealthGaugeProps {
  health: HealthScoreBreakdown | null;
  isLoading?: boolean;
}

export const KnowledgeHealthGauge: React.FC<KnowledgeHealthGaugeProps> = ({
  health,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 animate-pulse">
        <div className="h-6 bg-slate-800 rounded w-1/3 mb-4" />
        <div className="h-40 bg-slate-800 rounded mb-4" />
        <div className="h-20 bg-slate-800 rounded" />
      </div>
    );
  }

  if (!health) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center text-slate-400">
        No Knowledge Health Score available.
      </div>
    );
  }

  const getRatingBadge = (rating: string) => {
    switch (rating.toUpperCase()) {
      case 'EXCELLENT':
        return {
          bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          icon: <CheckCircle className="w-4 h-4 mr-1 text-emerald-400" />,
        };
      case 'GOOD':
        return {
          bg: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
          icon: <Activity className="w-4 h-4 mr-1 text-blue-400" />,
        };
      case 'FAIR':
        return {
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          icon: <AlertTriangle className="w-4 h-4 mr-1 text-amber-400" />,
        };
      default:
        return {
          bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
          icon: <ShieldAlert className="w-4 h-4 mr-1 text-rose-400" />,
        };
    }
  };

  const badge = getRatingBadge(health.rating);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl" data-testid="knowledge-health-gauge">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-400" />
            Knowledge Health Score (KHS)
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Multi-dimensional institutional knowledge evaluation model (ADR-044)
          </p>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-medium border flex items-center ${badge.bg}`}>
          {badge.icon}
          {health.rating}
        </div>
      </div>

      {/* Main Score & Arc Display */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center mb-6">
        <div className="flex flex-col items-center justify-center p-4 bg-slate-950/60 rounded-xl border border-slate-800/80">
          <div className="relative flex items-center justify-center">
            {/* SVG Circular Ring */}
            <svg className="w-32 h-32 transform -rotate-90">
              <circle
                cx="64"
                cy="64"
                r="52"
                stroke="currentColor"
                strokeWidth="10"
                className="text-slate-800"
                fill="transparent"
              />
              <circle
                cx="64"
                cy="64"
                r="52"
                stroke="currentColor"
                strokeWidth="10"
                strokeDasharray={2 * Math.PI * 52}
                strokeDashoffset={2 * Math.PI * 52 * (1 - health.overall_score / 100)}
                strokeLinecap="round"
                className={
                  health.overall_score >= 85
                    ? 'text-emerald-500'
                    : health.overall_score >= 70
                    ? 'text-blue-500'
                    : health.overall_score >= 50
                    ? 'text-amber-500'
                    : 'text-rose-500'
                }
                fill="transparent"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-3xl font-bold text-white tracking-tight" data-testid="khs-score-value">
                {health.overall_score}
              </span>
              <span className="text-[10px] uppercase tracking-wider text-slate-400">/ 100</span>
            </div>
          </div>
          <span className="text-xs text-slate-400 font-medium mt-2">Composite Health Index</span>
        </div>

        {/* Factor Breakdown Bars */}
        <div className="md:col-span-2 space-y-3">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300">Coverage Factor (30% weight)</span>
              <span className="text-indigo-400 font-medium">{health.coverage_score.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2">
              <div
                className="bg-indigo-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, health.coverage_score)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300">Freshness Factor (25% weight)</span>
              <span className="text-blue-400 font-medium">{health.freshness_score.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, health.freshness_score)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300">Quality Factor (25% weight)</span>
              <span className="text-emerald-400 font-medium">{health.quality_score.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2">
              <div
                className="bg-emerald-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, health.quality_score)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300">Retrieval Effectiveness (20% weight)</span>
              <span className="text-cyan-400 font-medium">{health.retrieval_score.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2">
              <div
                className="bg-cyan-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, health.retrieval_score)}%` }}
              />
            </div>
          </div>

          {health.duplicate_penalty > 0 && (
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-rose-400">Duplicate Content Penalty</span>
                <span className="text-rose-400 font-medium">-{health.duplicate_penalty.toFixed(1)} pts</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2">
                <div
                  className="bg-rose-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, health.duplicate_penalty * 5)}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Department Breakdown */}
      {health.department_breakdown && health.department_breakdown.length > 0 && (
        <div className="mt-6 pt-4 border-t border-slate-800">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
            Departmental Health Breakdown
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {health.department_breakdown.map((dept) => (
              <div
                key={dept.department}
                className="p-3 bg-slate-950/40 rounded-lg border border-slate-800/60 flex items-center justify-between"
              >
                <div>
                  <div className="text-sm font-medium text-white">{dept.department}</div>
                  <div className="text-xs text-slate-400">{dept.document_count} indexed docs</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-indigo-400">{dept.score}/100</div>
                  <div className="text-[10px] text-slate-400 uppercase">{dept.rating}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Identified Gaps Alert Box */}
      {health.identified_gaps && health.identified_gaps.length > 0 && (
        <div className="mt-6 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <div className="flex items-center gap-2 text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2">
            <Sparkles className="w-4 h-4 text-amber-400" />
            AI Identified Knowledge Gaps
          </div>
          <ul className="space-y-1">
            {health.identified_gaps.map((gap, idx) => (
              <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                <span className="text-amber-400 font-bold">•</span>
                <span>{gap}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
