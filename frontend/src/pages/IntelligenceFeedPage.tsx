import React from 'react';
import { IntelligenceDetailPanel } from '@/components/intelligence/IntelligenceDetailPanel';
import { IntelligenceFeedList } from '@/components/intelligence/IntelligenceFeedList';
import { IntelligenceMetricsBar } from '@/components/intelligence/IntelligenceMetricsBar';
import { IntelligenceScanPanel } from '@/components/intelligence/IntelligenceScanPanel';
import { useIntelligence } from '@/hooks/useIntelligence';

export const IntelligenceFeedPage: React.FC = () => {
  const {
    insights,
    selectedInsight,
    metrics,
    categoryFilter,
    setCategoryFilter,
    statusFilter,
    setStatusFilter,
    loading,
    actionLoading,
    error,
    feedbackNotice,
    selectInsight,
    runScan,
    submitFeedback,
    dismissInsight,
    resolveInsight,
    investigateInsight,
  } = useIntelligence();

  return (
    <main className="mx-auto max-w-7xl space-y-5 p-4 sm:p-6" aria-label="Proactive Intelligence Feed">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Proactive Intelligence Feed
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Evidence-backed change detection, knowledge gaps, contradictions, and emerging trends.
          </p>
        </div>
      </header>

      {error && (
        <div
          role="alert"
          className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-800 dark:bg-red-950/40 dark:text-red-200"
        >
          {error}
        </div>
      )}

      <IntelligenceMetricsBar metrics={metrics} />

      <IntelligenceScanPanel actionLoading={actionLoading} onRunScan={runScan} />

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        <div className="lg:col-span-5">
          <IntelligenceFeedList
            insights={insights}
            selectedId={selectedInsight?.insight_id}
            categoryFilter={categoryFilter}
            statusFilter={statusFilter}
            loading={loading}
            onSelect={selectInsight}
            onCategoryChange={setCategoryFilter}
            onStatusChange={setStatusFilter}
          />
        </div>
        <div className="lg:col-span-7">
          <IntelligenceDetailPanel
            insight={selectedInsight}
            actionLoading={actionLoading}
            feedbackNotice={feedbackNotice}
            onFeedback={submitFeedback}
            onDismiss={dismissInsight}
            onResolve={resolveInsight}
            onInvestigate={investigateInsight}
          />
        </div>
      </div>
    </main>
  );
};
