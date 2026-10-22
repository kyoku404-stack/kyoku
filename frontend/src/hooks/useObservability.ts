import { useState, useEffect, useCallback, useRef } from 'react';
import { observabilityService } from '@/services/observabilityService';
import type {
  CompositeHealthResponse,
  DatabaseHealth,
  StorageHealth,
  ApiHealth,
  AuthHealth,
  SystemTelemetrySummary,
  SystemAlert,
  LatencySample,
} from '@/types/observability';

export interface UseObservabilityOptions {
  pollingInterval?: number; // ms, default 10000
  autoStart?: boolean;
}

export interface DiagnosticResult {
  timestamp: string;
  totalDurationMs: number;
  overallStatus: 'healthy' | 'degraded' | 'unhealthy';
  composite?: CompositeHealthResponse;
  database?: DatabaseHealth;
  storage?: StorageHealth;
  api?: ApiHealth;
  auth?: AuthHealth;
  error?: string | null;
}

export function useObservability(options: UseObservabilityOptions = {}) {
  const { pollingInterval = 10000, autoStart = true } = options;

  const [compositeHealth, setCompositeHealth] = useState<CompositeHealthResponse | null>(null);
  const [dbHealth, setDbHealth] = useState<DatabaseHealth | null>(null);
  const [storageHealth, setStorageHealth] = useState<StorageHealth | null>(null);
  const [apiHealth, setApiHealth] = useState<ApiHealth | null>(null);
  const [authHealth, setAuthHealth] = useState<AuthHealth | null>(null);
  const [telemetry, setTelemetry] = useState<SystemTelemetrySummary | null>(null);

  const [latencyHistory, setLatencyHistory] = useState<LatencySample[]>([]);
  const [acknowledgedAlertIds, setAcknowledgedAlertIds] = useState<Set<string>>(new Set());

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isPolling, setIsPolling] = useState<boolean>(autoStart);

  const isMountedRef = useRef<boolean>(true);

  const refresh = useCallback(async () => {
    const startTime = performance.now();
    try {
      setLoading(true);
      setError(null);

      // Execute composite health and telemetry in parallel
      const [compRes, telRes, dbRes, stRes, apiRes, authRes] = await Promise.allSettled([
        observabilityService.getCompositeHealth(),
        observabilityService.getTelemetrySummary(),
        observabilityService.getDatabaseHealth(),
        observabilityService.getStorageHealth(),
        observabilityService.getApiHealth(),
        observabilityService.getAuthHealth(),
      ]);

      if (!isMountedRef.current) return;

      const elapsed = Math.round(performance.now() - startTime);

      if (compRes.status === 'fulfilled') {
        setCompositeHealth(compRes.value);
      }
      if (telRes.status === 'fulfilled') {
        setTelemetry(telRes.value);
      }
      if (dbRes.status === 'fulfilled') {
        setDbHealth(dbRes.value);
      }
      if (stRes.status === 'fulfilled') {
        setStorageHealth(stRes.value);
      }
      if (apiRes.status === 'fulfilled') {
        setApiHealth(apiRes.value);
      }
      if (authRes.status === 'fulfilled') {
        setAuthHealth(authRes.value);
      }

      // Record latency sample for telemetry trends (keep last 25 samples)
      setLatencyHistory((prev) => {
        const next = [
          ...prev,
          {
            timestamp: new Date().toISOString(),
            latency_ms: elapsed,
          },
        ];
        return next.length > 25 ? next.slice(next.length - 25) : next;
      });

      setLastUpdated(new Date());
    } catch (err) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err.message : 'Failed to retrieve observability telemetry');
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  // Polling loop
  useEffect(() => {
    isMountedRef.current = true;
    refresh();

    if (!isPolling) return;

    const intervalId = setInterval(() => {
      refresh();
    }, pollingInterval);

    return () => {
      isMountedRef.current = false;
      clearInterval(intervalId);
    };
  }, [refresh, isPolling, pollingInterval]);

  const togglePolling = useCallback(() => {
    setIsPolling((prev) => !prev);
  }, []);

  const acknowledgeAlert = useCallback((alertId: string) => {
    setAcknowledgedAlertIds((prev) => {
      const next = new Set(prev);
      next.add(alertId);
      return next;
    });
  }, []);

  const runDiagnostics = useCallback(async (): Promise<DiagnosticResult> => {
    const start = performance.now();
    try {
      const [comp, db, st, api, auth] = await Promise.all([
        observabilityService.getCompositeHealth(),
        observabilityService.getDatabaseHealth(),
        observabilityService.getStorageHealth(),
        observabilityService.getApiHealth(),
        observabilityService.getAuthHealth(),
      ]);

      const duration = Math.round(performance.now() - start);
      return {
        timestamp: new Date().toISOString(),
        totalDurationMs: duration,
        overallStatus: comp.status || 'healthy',
        composite: comp,
        database: db,
        storage: st,
        api,
        auth,
      };
    } catch (err) {
      const duration = Math.round(performance.now() - start);
      return {
        timestamp: new Date().toISOString(),
        totalDurationMs: duration,
        overallStatus: 'unhealthy',
        error: err instanceof Error ? err.message : 'Diagnostic execution encountered an error',
      };
    }
  }, []);

  // Compute active unacknowledged alerts
  const rawAlerts: SystemAlert[] = telemetry?.alerts || [];
  const activeAlerts = rawAlerts.map((alert) => ({
    ...alert,
    acknowledged: acknowledgedAlertIds.has(alert.id),
  }));

  return {
    compositeHealth,
    dbHealth,
    storageHealth,
    apiHealth,
    authHealth,
    telemetry,
    latencyHistory,
    activeAlerts,
    loading,
    error,
    lastUpdated,
    isPolling,
    togglePolling,
    refresh,
    acknowledgeAlert,
    runDiagnostics,
  };
}

export default useObservability;
