/**
 * Phase 2.5 Operational Anomaly Alert Feed.
 * Displays statistical Z-score anomalies with severity classifications.
 *
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import type { AnomaliesResponse, AnomalyResponseItem } from '@/types/intelligence';
import { AlertCircle, AlertTriangle, CheckCircle, Info, ShieldAlert } from 'lucide-react';

interface AnomalyAlertFeedProps {
  anomaliesData: AnomaliesResponse | null;
  isLoading?: boolean;
}

export const AnomalyAlertFeed: React.FC<AnomalyAlertFeedProps> = ({
  anomaliesData,
  isLoading = false,
}) => {
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');

  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 animate-pulse">
        <div className="h-6 bg-slate-800 rounded w-1/4 mb-4" />
        <div className="space-y-3">
          <div className="h-16 bg-slate-800 rounded" />
          <div className="h-16 bg-slate-800 rounded" />
        </div>
      </div>
    );
  }

  const anomalies = anomaliesData?.anomalies || [];
  const filtered = severityFilter === 'ALL'
    ? anomalies
    : anomalies.filter((a) => a.severity.toUpperCase() === severityFilter);

  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
        return {
          bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
          icon: <ShieldAlert className="w-4 h-4 text-rose-400" />,
        };
      case 'HIGH':
        return {
          bg: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
          icon: <AlertTriangle className="w-4 h-4 text-orange-400" />,
        };
      case 'MEDIUM':
        return {
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          icon: <AlertCircle className="w-4 h-4 text-amber-400" />,
        };
      default:
        return {
          bg: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
          icon: <Info className="w-4 h-4 text-blue-400" />,
        };
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl" data-testid="anomaly-alert-feed">
      {/* Header & Filter Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-slate-800 mb-6 gap-4">
        <div>
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            Operational Anomaly Detection Feed
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Statistical Z-score deviation monitoring across activity, auth, and retrieval layers
          </p>
        </div>

        <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800">
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-2.5 py-1 rounded text-[11px] font-medium transition-all ${
                severityFilter === sev
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Anomalies List */}
      {filtered.length === 0 ? (
        <div className="p-8 text-center bg-slate-950/40 rounded-xl border border-slate-800/60">
          <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
          <div className="text-sm font-medium text-white">No active anomalies detected</div>
          <div className="text-xs text-slate-400 mt-1">
            All system metrics are operating within the &plusmn;2.0&sigma; nominal threshold.
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((anomaly: AnomalyResponseItem) => {
            const badge = getSeverityBadge(anomaly.severity);
            return (
              <div
                key={anomaly.id}
                className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-all hover:border-slate-700"
              >
                <div className="flex items-start gap-3.5">
                  <div className="p-2 bg-slate-900 rounded-lg border border-slate-800 mt-0.5">
                    {badge.icon}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-semibold text-white">
                        {anomaly.metric_name.replace(/_/g, ' ')}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${badge.bg}`}>
                        {anomaly.severity}
                      </span>
                      <span className="text-[11px] font-mono text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                        Z = {anomaly.deviation_score.toFixed(2)}σ
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-1">{anomaly.description}</p>
                    <span className="text-[10px] text-slate-500 mt-1 block">
                      Detected: {formatDate(anomaly.detected_at)}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center">
                  <button
                    onClick={() => {}}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg transition-colors border border-slate-700"
                  >
                    Investigate
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
