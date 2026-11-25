/**
 * KEEP Enterprise Platform — Phase 4.11 Proactive Intelligence React Hook.
 */

import { useCallback, useEffect, useState } from 'react';
import { proactiveIntelligenceService as intelligenceService } from '@/services/proactiveIntelligenceService';
import type {
  FeedbackType,
  InsightCategory,
  InsightStatus,
  IntelligenceInsight,
  OperationalMetrics,
  ScanRequest,
} from '@/types/proactiveIntelligence';

export function useIntelligence() {
  const [insights, setInsights] = useState<IntelligenceInsight[]>([]);
  const [selectedInsight, setSelectedInsight] = useState<IntelligenceInsight | null>(null);
  const [metrics, setMetrics] = useState<OperationalMetrics | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<InsightCategory | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<InsightStatus>('published');
  const [loading, setLoading] = useState<boolean>(false);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [feedbackNotice, setFeedbackNotice] = useState<string | null>(null);

  const refresh = useCallback(async (forceSelectFirst = false) => {
    setLoading(true);
    setError(null);
    try {
      const [feedRes, metricsRes] = await Promise.all([
        intelligenceService.listInsights({
          category: categoryFilter === 'all' ? undefined : categoryFilter,
          status: statusFilter,
        }),
        intelligenceService.getMetrics(),
      ]);
      const items = feedRes.data ?? [];
      setInsights(items);
      setMetrics(metricsRes.data ?? null);
      if (items.length > 0 && (forceSelectFirst || !selectedInsight)) {
        const detail = await intelligenceService.getInsight(items[0].insight_id);
        setSelectedInsight(detail.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load intelligence feed.');
    } finally {
      setLoading(false);
    }
  }, [categoryFilter, statusFilter, selectedInsight]);

  useEffect(() => {
    void refresh();
  }, [categoryFilter, statusFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  const selectInsight = useCallback(async (insightId: string) => {
    setError(null);
    try {
      const detail = await intelligenceService.getInsight(insightId);
      setSelectedInsight(detail.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load insight details.');
    }
  }, []);

  const runScan = useCallback(
    async (payload: ScanRequest) => {
      setActionLoading(true);
      setError(null);
      try {
        await intelligenceService.requestScan(payload);
        setSelectedInsight(null);
        await refresh(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Scan execution failed.');
      } finally {
        setActionLoading(false);
      }
    },
    [refresh]
  );

  const submitFeedback = useCallback(
    async (insightId: string, feedback: FeedbackType, comment?: string) => {
      setActionLoading(true);
      try {
        await intelligenceService.submitFeedback(insightId, feedback, comment);
        setFeedbackNotice(`Feedback '${feedback}' recorded.`);
        await refresh();
      } finally {
        setActionLoading(false);
      }
    },
    [refresh]
  );

  const dismissInsight = useCallback(
    async (insightId: string) => {
      setActionLoading(true);
      try {
        await intelligenceService.dismissInsight(insightId, 'user', 'Dismissed from feed');
        setSelectedInsight(null);
        await refresh();
      } finally {
        setActionLoading(false);
      }
    },
    [refresh]
  );

  const resolveInsight = useCallback(
    async (insightId: string) => {
      setActionLoading(true);
      try {
        const res = await intelligenceService.resolveInsight(insightId, 'Resolved via Intelligence Feed');
        setSelectedInsight(res.data);
        await refresh();
      } finally {
        setActionLoading(false);
      }
    },
    [refresh]
  );

  const investigateInsight = useCallback(
    async (insightId: string) => {
      setActionLoading(true);
      try {
        const res = await intelligenceService.investigateInsight(insightId, 'knowledge_analysis');
        setSelectedInsight(res.data);
        await refresh();
      } finally {
        setActionLoading(false);
      }
    },
    [refresh]
  );

  return {
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
    refresh,
    selectInsight,
    runScan,
    submitFeedback,
    dismissInsight,
    resolveInsight,
    investigateInsight,
  };
}
