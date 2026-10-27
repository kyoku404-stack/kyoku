/**
 * Phase 2.5 Enterprise Intelligence & Predictive Analytics Custom React Hook.
 * Manages executive briefing, Knowledge Health Scoring, predictive forecasting,
 * anomaly detection, and prioritized AI recommendations state.
 *
 * Specification: docs/api/api-contract.md Section 12 & devdocs/p2/p2.5.txt
 * Author: Member 3 (Frontend & UI Lead)
 */

import { useState, useCallback, useEffect } from 'react';
import { intelligenceService } from '@/services/intelligenceService';
import type {
  ExecutiveDashboardResponse,
  KPIsResponse,
  TrendAnalysisResponse,
  PredictionsResponse,
  AnomaliesResponse,
  RecommendationsResponse,
  KnowledgeHealthResponse,
} from '@/types/intelligence';

export type IntelligenceTab =
  | 'OVERVIEW'
  | 'HEALTH'
  | 'FORECASTS'
  | 'ANOMALIES'
  | 'RECOMMENDATIONS'
  | 'TRENDS';

export interface UseEnterpriseIntelligenceOptions {
  autoLoad?: boolean;
  initialTab?: IntelligenceTab;
  initialPeriodDays?: number;
  initialHorizonDays?: number;
}

export function useEnterpriseIntelligence(options: UseEnterpriseIntelligenceOptions = {}) {
  const {
    autoLoad = true,
    initialTab = 'OVERVIEW',
    initialPeriodDays = 30,
    initialHorizonDays = 30,
  } = options;

  // Active view tab
  const [activeTab, setActiveTab] = useState<IntelligenceTab>(initialTab);
  const [periodDays, setPeriodDays] = useState<number>(initialPeriodDays);
  const [horizonDays, setHorizonDays] = useState<number>(initialHorizonDays);

  // Data states
  const [dashboard, setDashboard] = useState<ExecutiveDashboardResponse | null>(null);
  const [kpis, setKPIs] = useState<KPIsResponse | null>(null);
  const [trends, setTrends] = useState<TrendAnalysisResponse | null>(null);
  const [predictions, setPredictions] = useState<PredictionsResponse | null>(null);
  const [anomalies, setAnomalies] = useState<AnomaliesResponse | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationsResponse | null>(null);
  const [healthScore, setHealthScore] = useState<KnowledgeHealthResponse | null>(null);

  // Async states
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    try {
      setError(null);
      const res = await intelligenceService.getExecutiveDashboard();
      if (res.success && res.data) {
        setDashboard(res.data);
        setKPIs(res.data.kpis);
        setHealthScore(res.data.health_score);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch executive dashboard';
      setError(msg);
    }
  }, []);

  const fetchKPIs = useCallback(async () => {
    try {
      const res = await intelligenceService.getKPIs();
      if (res.success && res.data) {
        setKPIs(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch KPIs';
      setError(msg);
    }
  }, []);

  const fetchTrends = useCallback(async (days = periodDays) => {
    try {
      const res = await intelligenceService.getTrends(days);
      if (res.success && res.data) {
        setTrends(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch trends';
      setError(msg);
    }
  }, [periodDays]);

  const fetchPredictions = useCallback(async (horizon = horizonDays) => {
    try {
      const res = await intelligenceService.getPredictions(horizon);
      if (res.success && res.data) {
        setPredictions(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch predictions';
      setError(msg);
    }
  }, [horizonDays]);

  const fetchAnomalies = useCallback(async () => {
    try {
      const res = await intelligenceService.getAnomalies();
      if (res.success && res.data) {
        setAnomalies(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch anomalies';
      setError(msg);
    }
  }, []);

  const fetchRecommendations = useCallback(async (status = 'ACTIVE') => {
    try {
      const res = await intelligenceService.getRecommendations(status);
      if (res.success && res.data) {
        setRecommendations(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch recommendations';
      setError(msg);
    }
  }, []);

  const fetchHealthScore = useCallback(async () => {
    try {
      const res = await intelligenceService.getKnowledgeHealth();
      if (res.success && res.data) {
        setHealthScore(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch knowledge health score';
      setError(msg);
    }
  }, []);

  const refreshAll = useCallback(async () => {
    setIsRefreshing(true);
    setError(null);
    try {
      await Promise.all([
        fetchDashboard(),
        fetchTrends(periodDays),
        fetchPredictions(horizonDays),
        fetchAnomalies(),
        fetchRecommendations(),
      ]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error refreshing intelligence data';
      setError(msg);
    } finally {
      setIsRefreshing(false);
    }
  }, [fetchDashboard, fetchTrends, fetchPredictions, fetchAnomalies, fetchRecommendations, periodDays, horizonDays]);

  // Initial load
  useEffect(() => {
    if (autoLoad) {
      setIsLoading(true);
      refreshAll().finally(() => setIsLoading(false));
    }
  }, [autoLoad, refreshAll]);

  return {
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
    fetchDashboard,
    fetchKPIs,
    fetchTrends,
    fetchPredictions,
    fetchAnomalies,
    fetchRecommendations,
    fetchHealthScore,
  };
}
