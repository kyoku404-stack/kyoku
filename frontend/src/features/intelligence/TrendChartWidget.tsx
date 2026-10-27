/**
 * Phase 2.5 Historical Multi-Series Trend Visualizer.
 * Renders document growth curves, AI query volume trends, and department activity.
 *
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import type { TrendAnalysisResponse } from '@/types/intelligence';
import { BarChart2, Calendar, FileText, Zap } from 'lucide-react';

interface TrendChartWidgetProps {
  trends: TrendAnalysisResponse | null;
  periodDays: number;
  onPeriodChange?: (days: number) => void;
  isLoading?: boolean;
}

export const TrendChartWidget: React.FC<TrendChartWidgetProps> = ({
  trends,
  periodDays,
  onPeriodChange,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 animate-pulse">
        <div className="h-6 bg-slate-800 rounded w-1/4 mb-4" />
        <div className="h-48 bg-slate-800 rounded" />
      </div>
    );
  }

  if (!trends) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center text-slate-400">
        No trend data available.
      </div>
    );
  }

  const { document_growth, ai_query_volume, department_activity } = trends;

  const maxDoc = Math.max(...document_growth.map((p) => p.value), 1);
  const maxAi = Math.max(...ai_query_volume.map((p) => p.value), 1);
  const maxDept = Math.max(...department_activity.map((d) => d.query_count), 1);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl" data-testid="trend-chart-widget">
      {/* Header & Window Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-slate-800 mb-6 gap-4">
        <div>
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-indigo-400" />
            Historical Multi-Series Trend Analysis
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Aggregated institutional knowledge growth and AI adoption trends
          </p>
        </div>

        {onPeriodChange && (
          <div className="flex items-center gap-2 bg-slate-950 p-1 rounded-lg border border-slate-800">
            <Calendar className="w-3.5 h-3.5 text-slate-400 ml-2" />
            {[14, 30, 60, 90].map((days) => (
              <button
                key={days}
                onClick={() => onPeriodChange(days)}
                className={`px-3 py-1 rounded text-xs font-medium transition-all ${
                  periodDays === days
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {days}d
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Document Growth Curve */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-indigo-400" />
              Document Upload Growth
            </span>
            <span className="text-xs text-indigo-400 font-bold font-mono">
              {document_growth[document_growth.length - 1]?.value || 0} total docs
            </span>
          </div>

          <div className="h-32 flex items-end gap-2 pt-4 px-2">
            {document_growth.map((point, idx) => {
              const heightPct = (point.value / maxDoc) * 100;
              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-1.5 group relative">
                  <div
                    className="w-full bg-indigo-500/80 group-hover:bg-indigo-400 rounded-t transition-all duration-300"
                    style={{ height: `${heightPct}%` }}
                  />
                  <span className="text-[9px] text-slate-500 truncate max-w-[40px]">
                    {point.date.slice(5)}
                  </span>
                  <div className="absolute -top-7 opacity-0 group-hover:opacity-100 bg-slate-800 text-white text-[10px] px-1.5 py-0.5 rounded shadow pointer-events-none transition-opacity">
                    {point.value}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* AI Query Volume Trend */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Zap className="w-4 h-4 text-emerald-400" />
              AI Queries & Search Volume
            </span>
            <span className="text-xs text-emerald-400 font-bold font-mono">
              {ai_query_volume[ai_query_volume.length - 1]?.value || 0} queries
            </span>
          </div>

          <div className="h-32 flex items-end gap-2 pt-4 px-2">
            {ai_query_volume.map((point, idx) => {
              const heightPct = (point.value / maxAi) * 100;
              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-1.5 group relative">
                  <div
                    className="w-full bg-emerald-500/80 group-hover:bg-emerald-400 rounded-t transition-all duration-300"
                    style={{ height: `${heightPct}%` }}
                  />
                  <span className="text-[9px] text-slate-500 truncate max-w-[40px]">
                    {point.date.slice(5)}
                  </span>
                  <div className="absolute -top-7 opacity-0 group-hover:opacity-100 bg-slate-800 text-white text-[10px] px-1.5 py-0.5 rounded shadow pointer-events-none transition-opacity">
                    {point.value}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Department Activity Comparative Bars */}
      {department_activity && department_activity.length > 0 && (
        <div className="pt-4 border-t border-slate-800">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4">
            Departmental Utilization & Knowledge Activity
          </h4>
          <div className="space-y-3">
            {department_activity.map((dept) => {
              const barWidth = (dept.query_count / maxDept) * 100;
              return (
                <div key={dept.department} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-white font-medium">{dept.department}</span>
                    <span className="text-slate-400">
                      {dept.document_count} docs • <strong className="text-cyan-400">{dept.query_count} queries</strong>
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-indigo-500 to-cyan-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.max(5, barWidth)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
