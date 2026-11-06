/**
 * KEEP Enterprise Platform — Phase 3.7 Release & Quality Assurance Custom React Hook.
 *
 * Specification: devdocs/p3/p3.7.txt Chapters 1-20 & docs/api/api-contract.md (Section 19)
 * Author: Member 3 (Frontend & UI Lead)
 */

import { useCallback, useEffect, useState } from 'react';
import { releaseService } from '@/services/releaseService';
import type {
  ReleaseDeployData,
  ReleaseDeployRequest,
  ReleaseHistoryItemData,
  SecurityAuditData,
  SystemReadinessData,
} from '@/types/release';

export function useReleaseManagement(autoPollIntervalMs: number = 0) {
  const [readiness, setReadiness] = useState<SystemReadinessData | null>(null);
  const [releases, setReleases] = useState<ReleaseHistoryItemData[]>([]);
  const [securityAudit, setSecurityAudit] = useState<SecurityAuditData | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [deploying, setDeploying] = useState<boolean>(false);
  const [auditing, setAuditing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // ==========================================================================
  // Fetchers
  // ==========================================================================

  const fetchReadiness = useCallback(async (version: string = '1.0.0') => {
    try {
      const res = await releaseService.getReadiness(version);
      if (res.success && res.data) {
        setReadiness(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch pre-flight readiness';
      setError(msg);
    }
  }, []);

  const fetchReleases = useCallback(async (limit: number = 50) => {
    try {
      const res = await releaseService.getReleaseHistory(limit);
      if (res.success && res.data) {
        setReleases(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch release history';
      setError(msg);
    }
  }, []);

  const fetchSecurityAudit = useCallback(async () => {
    setAuditing(true);
    try {
      const res = await releaseService.getSecurityAudit();
      if (res.success && res.data) {
        setSecurityAudit(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to execute security audit';
      setError(msg);
    } finally {
      setAuditing(false);
    }
  }, []);

  const refreshAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await Promise.allSettled([
        fetchReadiness(),
        fetchReleases(),
        fetchSecurityAudit(),
      ]);
    } finally {
      setLoading(false);
    }
  }, [fetchReadiness, fetchReleases, fetchSecurityAudit]);

  // ==========================================================================
  // Mutators
  // ==========================================================================

  const triggerRelease = useCallback(
    async (request: ReleaseDeployRequest): Promise<ReleaseDeployData | null> => {
      setDeploying(true);
      setError(null);
      setSuccessMessage(null);
      try {
        const res = await releaseService.triggerRelease(request);
        if (res.success && res.data) {
          setSuccessMessage(`Release ${res.data.version} (${res.data.release_tag}) deployed successfully!`);
          await fetchReleases();
          await fetchReadiness(request.version);
          return res.data;
        }
        return null;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Release deployment failed';
        setError(msg);
        return null;
      } finally {
        setDeploying(false);
      }
    },
    [fetchReadiness, fetchReleases]
  );

  // ==========================================================================
  // Effects
  // ==========================================================================

  useEffect(() => {
    void refreshAll();
  }, [refreshAll]);

  useEffect(() => {
    if (autoPollIntervalMs <= 0) return;
    const timer = setInterval(() => {
      void fetchReadiness();
    }, autoPollIntervalMs);
    return () => clearInterval(timer);
  }, [autoPollIntervalMs, fetchReadiness]);

  return {
    readiness,
    releases,
    securityAudit,
    loading,
    deploying,
    auditing,
    error,
    successMessage,
    setError,
    setSuccessMessage,
    fetchReadiness,
    fetchReleases,
    fetchSecurityAudit,
    triggerRelease,
    refreshAll,
  };
}
