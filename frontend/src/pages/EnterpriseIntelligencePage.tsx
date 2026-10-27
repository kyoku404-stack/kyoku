/**
 * KEEP Enterprise Platform — Enterprise Intelligence & Predictive Analytics Master Page (Phase 2.5).
 *
 * Integrated decision-support center providing multi-dimensional Knowledge Health Scoring (KHS),
 * OLS linear capacity forecasting, statistical Z-score operational anomaly detection,
 * and Priority Index-ranked strategic AI recommendations.
 *
 * Specification: docs/api/api-contract.md Section 12 & devdocs/p2/p2.5.txt
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import { useEnterpriseIntelligence, type IntelligenceTab } from '@/hooks/useEnterpriseIntelligence';
import {
  KnowledgeHealthGauge,
  ExecutiveBriefingCard,
  ForecastVisualizer,
  AnomalyAlertFeed,
  RecommendationPanel,
  TrendChartWidget,
} from '@/features/intelligence';
import {
  Activity,
  AlertTriangle,
  BarChart2,
  BrainCircuit,
  Compass,
  Lightbulb,
  LineChart,
  RefreshCw,
} from 'lucide-react';

export const EnterpriseIntelligencePage: React.FC = () => {
  const {
    activeTab,
    setActiveTab,
    periodDays,
    setPeriodDays,
    horizonDays,
    setHorizonDays,
    dashboard,
    kpis,
    trends,
    predictions,
    anomalies,
    recommendations,
    healthScore,
    isLoading,
    isRefreshing,
    error,
    refreshAll,
  } = useEnterpriseIntelligence({ autoLoad: true });

  const tabs: Array<{ id: IntelligenceTab; label: string; icon: React.ReactNode }> = [
    { id: 'OVERVIEW', label: 'Executive Briefing', icon: <Compass className="w-4 h-4" /> },
    { id: 'HEALTH', label: 'Knowledge Health', icon: <Activity className="w-4 h-4" /> },
    { id: 'FORECASTS', label: 'Capacity Forecasts', icon: <LineChart className="w-4 h-4" /> },
    { id: 'ANOMALIES', label: 'Anomaly Detection', icon: <AlertTriangle className="w-4 h-4" /> },
    { id: 'RECOMMENDATIONS', label: 'AI Recommendations', icon: <Lightbulb className="w-4 h-4" /> },
    { id: 'TRENDS', label: 'Trend Analysis', icon: <BarChart2 className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-8 space-y-6" data-testid="enterprise-intelligence-page">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20">
              <BrainCircuit className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Enterprise Intelligence & Predictive Analytics
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                  Phase 2.5
                </span>
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Real-time institutional knowledge health, capacity runways, and AI decision support
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => refreshAll()}
            disabled={isRefreshing || isLoading}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 rounded-lg text-xs font-medium flex items-center gap-2 transition-all disabled:opacity-50"
            data-testid="refresh-intelligence-btn"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>{isRefreshing ? 'Refreshing...' : 'Refresh Insights'}</span>
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-800/80">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-lg text-xs font-medium flex items-center gap-2 transition-all whitespace-nowrap ${
              activeTab === tab.id
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
            data-testid={`tab-${tab.id.toLowerCase()}`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Contents */}
      {activeTab === 'OVERVIEW' && (
        <div className="space-y-6">
          <ExecutiveBriefingCard
            summary={dashboard?.executive_summary || ''}
            kpis={kpis}
            isLoading={isLoading}
          />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <KnowledgeHealthGauge health={healthScore} isLoading={isLoading} />
            <ForecastVisualizer
              predictions={predictions}
              horizonDays={horizonDays}
              onHorizonChange={setHorizonDays}
              isLoading={isLoading}
            />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <AnomalyAlertFeed anomaliesData={anomalies} isLoading={isLoading} />
            <RecommendationPanel recommendationsData={recommendations} isLoading={isLoading} />
          </div>
        </div>
      )}

      {activeTab === 'HEALTH' && (
        <div className="space-y-6">
          <KnowledgeHealthGauge health={healthScore} isLoading={isLoading} />
        </div>
      )}

      {activeTab === 'FORECASTS' && (
        <div className="space-y-6">
          <ForecastVisualizer
            predictions={predictions}
            horizonDays={horizonDays}
            onHorizonChange={setHorizonDays}
            isLoading={isLoading}
          />
        </div>
      )}

      {activeTab === 'ANOMALIES' && (
        <div className="space-y-6">
          <AnomalyAlertFeed anomaliesData={anomalies} isLoading={isLoading} />
        </div>
      )}

      {activeTab === 'RECOMMENDATIONS' && (
        <div className="space-y-6">
          <RecommendationPanel recommendationsData={recommendations} isLoading={isLoading} />
        </div>
      )}

      {activeTab === 'TRENDS' && (
        <div className="space-y-6">
          <TrendChartWidget
            trends={trends}
            periodDays={periodDays}
            onPeriodChange={setPeriodDays}
            isLoading={isLoading}
          />
        </div>
      )}
    </div>
  );
};
