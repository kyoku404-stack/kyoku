/**
 * Phase 2.5 Strategic AI Recommendations Panel.
 * Displays prioritized optimization actions ranked by Priority Index ($PI = \frac{Impact \times 1.5}{Effort}$).
 *
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import type { RecommendationResponseItem, RecommendationsResponse } from '@/types/intelligence';
import { Archive, ArrowRight, CheckCircle2, Copy, FileText, Lightbulb, Shield, Users } from 'lucide-react';

interface RecommendationPanelProps {
  recommendationsData: RecommendationsResponse | null;
  isLoading?: boolean;
}

export const RecommendationPanel: React.FC<RecommendationPanelProps> = ({
  recommendationsData,
  isLoading = false,
}) => {
  const [appliedIds, setAppliedIds] = useState<Set<string>>(new Set());

  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 animate-pulse">
        <div className="h-6 bg-slate-800 rounded w-1/4 mb-4" />
        <div className="space-y-4">
          <div className="h-24 bg-slate-800 rounded" />
          <div className="h-24 bg-slate-800 rounded" />
        </div>
      </div>
    );
  }

  const recs = recommendationsData?.recommendations || [];

  const handleApply = (id: string) => {
    setAppliedIds((prev) => new Set([...prev, id]));
  };

  const getCategoryIcon = (category: string) => {
    switch (category.toUpperCase()) {
      case 'ARCHIVE':
        return <Archive className="w-4 h-4 text-amber-400" />;
      case 'DEDUPLICATE':
        return <Copy className="w-4 h-4 text-purple-400" />;
      case 'COVERAGE':
        return <FileText className="w-4 h-4 text-blue-400" />;
      case 'SECURITY':
        return <Shield className="w-4 h-4 text-rose-400" />;
      case 'COLLABORATION':
        return <Users className="w-4 h-4 text-emerald-400" />;
      default:
        return <Lightbulb className="w-4 h-4 text-indigo-400" />;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl" data-testid="recommendation-panel">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800 mb-6">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-amber-400" />
          Strategic AI Recommendations & Decision Support
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          Prioritized actionable intelligence ranked by Priority Index: PI = (Impact &times; 1.5) / Effort
        </p>
      </div>

      {recs.length === 0 ? (
        <div className="p-8 text-center bg-slate-950/40 rounded-xl border border-slate-800/60">
          <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
          <div className="text-sm font-medium text-white">All recommendations addressed</div>
          <div className="text-xs text-slate-400 mt-1">
            Institutional knowledge hygiene is operating at peak efficiency.
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {recs.map((rec: RecommendationResponseItem) => {
            const isApplied = appliedIds.has(rec.id);
            return (
              <div
                key={rec.id}
                className="p-5 bg-slate-950/60 border border-slate-800/80 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-all hover:border-slate-700"
              >
                <div className="flex items-start gap-4">
                  <div className="p-2.5 bg-slate-900 rounded-xl border border-slate-800 mt-0.5">
                    {getCategoryIcon(rec.category)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className="text-sm font-bold text-white">{rec.title}</span>
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {rec.category}
                      </span>
                      <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 font-bold">
                        PI: {rec.priority_index.toFixed(1)}
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
                      {rec.description}
                    </p>

                    <div className="flex items-center gap-4 mt-2 text-[11px] text-slate-400">
                      <span>Impact: <strong className="text-white">{rec.impact_score.toFixed(1)}/10</strong></span>
                      <span>•</span>
                      <span>Effort: <strong className="text-white">{rec.effort_score.toFixed(1)}/10</strong></span>
                    </div>
                  </div>
                </div>

                <div className="self-end sm:self-center">
                  {isApplied ? (
                    <span className="px-3 py-1.5 bg-emerald-500/10 text-emerald-400 text-xs font-semibold rounded-lg border border-emerald-500/30 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Applied
                    </span>
                  ) : (
                    <button
                      onClick={() => handleApply(rec.id)}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg transition-all shadow-md shadow-indigo-600/20 flex items-center gap-1.5"
                    >
                      <span>Execute</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
