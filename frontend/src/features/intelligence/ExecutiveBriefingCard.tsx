/**
 * Phase 2.5 Executive Briefing Card & Core KPIs.
 * Displays synthetic AI intelligence narrative and primary enterprise metrics.
 *
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import type { KPIsResponse } from '@/types/intelligence';
import { Database, FileText, Sparkles, Users, Zap } from 'lucide-react';

interface ExecutiveBriefingCardProps {
  summary: string;
  kpis: KPIsResponse | null;
  isLoading?: boolean;
}

export const ExecutiveBriefingCard: React.FC<ExecutiveBriefingCardProps> = ({
  summary,
  kpis,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 animate-pulse mb-6">
        <div className="h-20 bg-slate-800 rounded mb-4" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="h-20 bg-slate-800 rounded" />
          <div className="h-20 bg-slate-800 rounded" />
          <div className="h-20 bg-slate-800 rounded" />
          <div className="h-20 bg-slate-800 rounded" />
        </div>
      </div>
    );
  }

  const formatStorage = (bytes: number) => {
    if (bytes >= 1024 * 1024 * 1024) {
      return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6 mb-6" data-testid="executive-briefing-card">
      {/* AI Synthesis Briefing Card */}
      <div className="relative overflow-hidden bg-gradient-to-r from-indigo-950/60 via-slate-900 to-slate-900 border border-indigo-500/30 rounded-xl p-6 shadow-xl">
        <div className="absolute top-0 right-0 p-8 opacity-10">
          <Sparkles className="w-32 h-32 text-indigo-400" />
        </div>
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider">
            <Sparkles className="w-4 h-4" />
            Executive AI Intelligence Briefing
          </div>
          <p className="text-sm md:text-base text-slate-200 leading-relaxed max-w-4xl" data-testid="executive-briefing-text">
            {summary || 'Analyzing enterprise documents, queries, and team adoption...'}
          </p>
        </div>
      </div>

      {/* KPI Cards Grid */}
      {kpis && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4" data-testid="kpis-indicator-grid">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-lg">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-slate-400 font-medium">Active Contributors</div>
              <div className="text-xl font-bold text-white mt-0.5">{kpis.active_users}</div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-slate-400 font-medium">Indexed Knowledge</div>
              <div className="text-xl font-bold text-white mt-0.5">{kpis.documents_uploaded} docs</div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-slate-400 font-medium">AI Queries Processed</div>
              <div className="text-xl font-bold text-white mt-0.5">{kpis.ai_queries}</div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-cyan-500/10 text-cyan-400 rounded-lg">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-slate-400 font-medium">Storage Utilized</div>
              <div className="text-xl font-bold text-white mt-0.5">
                {formatStorage(kpis.storage_used_bytes)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
