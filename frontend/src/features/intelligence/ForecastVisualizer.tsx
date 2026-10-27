/**
 * Phase 2.5 Predictive Analytics & Forecasting Visualizer.
 * Renders statistical OLS linear projections, confidence intervals,
 * AI query token estimates, and storage exhaustion runway indicators.
 *
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import type { PredictionsResponse } from '@/types/intelligence';
import { AlertCircle, ArrowUpRight, CheckCircle2, Clock, HardDrive, LineChart, TrendingUp } from 'lucide-react';

interface ForecastVisualizerProps {
  predictions: PredictionsResponse | null;
  horizonDays: number;
  onHorizonChange?: (days: number) => void;
  isLoading?: boolean;
}

export const ForecastVisualizer: React.FC<ForecastVisualizerProps> = ({
  predictions,
  horizonDays,
  onHorizonChange,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 animate-pulse">
        <div className="h-6 bg-slate-800 rounded w-1/4 mb-4" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="h-48 bg-slate-800 rounded" />
          <div className="h-48 bg-slate-800 rounded" />
          <div className="h-48 bg-slate-800 rounded" />
        </div>
      </div>
    );
  }

  if (!predictions) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center text-slate-400">
        No predictive forecasts available.
      </div>
    );
  }

  const { document_forecast, storage_runway, query_volume_forecast } = predictions;

  const formatBytes = (bytes: number) => {
    if (bytes >= 1024 * 1024 * 1024) {
      return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl" data-testid="forecast-visualizer">
      {/* Header with Horizon Selector */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-slate-800 mb-6 gap-4">
        <div>
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <LineChart className="w-5 h-5 text-indigo-400" />
            Predictive Analytics & Capacity Forecasting
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Statistical Ordinary Least Squares (OLS) regression model with 95% confidence intervals
          </p>
        </div>

        {onHorizonChange && (
          <div className="flex items-center gap-2 bg-slate-950 p-1 rounded-lg border border-slate-800">
            <span className="text-xs text-slate-400 pl-2">Horizon:</span>
            {[30, 60, 90].map((days) => (
              <button
                key={days}
                onClick={() => onHorizonChange(days)}
                className={`px-3 py-1 rounded text-xs font-medium transition-all ${
                  horizonDays === days
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

      {/* Forecast Projections Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Document Ingestion Growth Card */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4 text-indigo-400" />
                Document Growth Projection
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 flex items-center gap-1">
                <ArrowUpRight className="w-3 h-3" />
                +{document_forecast.growth_rate_pct.toFixed(1)}%
              </span>
            </div>

            <div className="flex items-baseline gap-2 mb-2">
              <span className="text-3xl font-bold text-white">
                {Math.round(document_forecast.projected_value)}
              </span>
              <span className="text-xs text-slate-400">
                projected (from {Math.round(document_forecast.current_value)})
              </span>
            </div>

            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-xs text-slate-300 space-y-1 mt-4">
              <div className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">
                95% Confidence Interval Envelope
              </div>
              <div className="flex justify-between font-mono">
                <span>Lower: {Math.round(document_forecast.confidence_lower)} docs</span>
                <span>Upper: {Math.round(document_forecast.confidence_upper)} docs</span>
              </div>
            </div>
          </div>
          <p className="text-[11px] text-slate-500 mt-4">
            Estimated using standard error bounds (&sigma;) over {horizonDays}-day historical volume.
          </p>
        </div>

        {/* AI Query & Token Volume Card */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <LineChart className="w-4 h-4 text-blue-400" />
                AI Query Adoption
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30">
                Tokens & Load
              </span>
            </div>

            <div className="flex items-baseline gap-2 mb-2">
              <span className="text-3xl font-bold text-white">
                {query_volume_forecast.projected_daily_avg.toFixed(1)}
              </span>
              <span className="text-xs text-slate-400">
                queries/day (current: {query_volume_forecast.current_daily_avg.toFixed(1)})
              </span>
            </div>

            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-xs text-slate-300 space-y-1 mt-4">
              <div className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">
                Projected Monthly Tokens
              </div>
              <div className="text-sm font-bold text-blue-400">
                {(query_volume_forecast.monthly_tokens_projected / 1000000).toFixed(2)}M Tokens
              </div>
            </div>
          </div>
          <p className="text-[11px] text-slate-500 mt-4">
            Supports infrastructure capacity sizing and API token quota provisioning.
          </p>
        </div>

        {/* Storage Capacity Runway Card */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <HardDrive className="w-4 h-4 text-cyan-400" />
                Storage Runway
              </span>
              {storage_runway.is_critical ? (
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  Critical
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  Optimal
                </span>
              )}
            </div>

            <div className="flex items-baseline gap-2 mb-2">
              <span className="text-3xl font-bold text-white">
                {storage_runway.days_to_85_pct}
              </span>
              <span className="text-xs text-slate-400">
                days to 85% capacity threshold
              </span>
            </div>

            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-xs text-slate-300 space-y-1 mt-4">
              <div className="flex justify-between">
                <span className="text-slate-400">Days to Full (100%):</span>
                <span className="font-semibold text-white">{storage_runway.days_to_full} days</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Current vs Capacity:</span>
                <span className="font-semibold text-cyan-400">
                  {formatBytes(storage_runway.current_usage_bytes)} / {formatBytes(storage_runway.capacity_bytes)}
                </span>
              </div>
            </div>
          </div>
          <p className="text-[11px] text-slate-500 mt-4 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Alert triggers if threshold runway falls below 14 days.
          </p>
        </div>
      </div>
    </div>
  );
};
