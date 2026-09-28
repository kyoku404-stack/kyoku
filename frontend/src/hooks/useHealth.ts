import { useState, useEffect, useCallback } from 'react';
import { healthService } from '@/services/healthService';
import type { HealthCheckResponse } from '@/types/health';

interface UseHealthReturn {
  health: HealthCheckResponse | null;
  loading: boolean;
  error: string | null;
  latencyMs: number | null;
  refresh: () => Promise<void>;
}

export function useHealth(autoPollIntervalMs: number = 0): UseHealthReturn {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);

  const fetchHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    const startTime = performance.now();

    try {
      const data = await healthService.checkHealth();
      const elapsed = Math.round(performance.now() - startTime);
      setHealth(data);
      setLatencyMs(elapsed);
    } catch (err: unknown) {
      const message =
        err && typeof err === 'object' && 'message' in err
          ? (err as { message: string }).message
          : 'Failed to connect to backend engine';
      setError(message);
      setHealth(null);
      setLatencyMs(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();

    if (autoPollIntervalMs > 0) {
      const timer = setInterval(fetchHealth, autoPollIntervalMs);
      return () => clearInterval(timer);
    }
  }, [fetchHealth, autoPollIntervalMs]);

  return { health, loading, error, latencyMs, refresh: fetchHealth };
}
