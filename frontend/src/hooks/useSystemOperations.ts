/**
 * KEEP Enterprise Platform — Production Infrastructure & Operations Custom React Hook.
 *
 * Phase: 3.6
 * Specification: devdocs/p3/p3.6.txt & docs/api/api-contract.md (Section 18)
 * Role: Member 3 (Frontend & UI Lead)
 */

import { useCallback, useEffect, useState } from 'react';
import {
  systemService,
  type SystemLogsQueryParams,
} from '@/services/systemService';
import type {
  CacheFlushRequest,
  CreateBackupRequest,
  DeployTriggerData,
  DeployTriggerRequest,
  MicroserviceStatusData,
  SystemBackupsData,
  SystemHealthData,
  SystemLogEntryData,
  SystemMetricsData,
  SystemVersionData,
} from '@/types/system';

export function useSystemOperations() {
  const [health, setHealth] = useState<SystemHealthData | null>(null);
  const [metrics, setMetrics] = useState<SystemMetricsData | null>(null);
  const [services, setServices] = useState<MicroserviceStatusData[]>([]);
  const [logs, setLogs] = useState<SystemLogEntryData[]>([]);
  const [backups, setBackups] = useState<SystemBackupsData | null>(null);
  const [version, setVersion] = useState<SystemVersionData | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [deploying, setDeploying] = useState<boolean>(false);
  const [creatingBackup, setCreatingBackup] = useState<boolean>(false);
  const [flushingCache, setFlushingCache] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // ==========================================================================
  // Fetchers
  // ==========================================================================

  const fetchHealth = useCallback(async () => {
    try {
      const res = await systemService.getHealth();
      if (res.success && res.data) {
        setHealth(res.data);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch platform health';
      setError(message);
    }
  }, []);

  const fetchMetrics = useCallback(async () => {
    try {
      const res = await systemService.getMetrics();
      if (res.success && res.data) {
        setMetrics(res.data);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch performance telemetry';
      setError(message);
    }
  }, []);

  const fetchServices = useCallback(async () => {
    try {
      const res = await systemService.getStatus();
      if (res.success && res.data) {
        setServices(res.data);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch microservices status';
      setError(message);
    }
  }, []);

  const fetchLogs = useCallback(async (params?: SystemLogsQueryParams) => {
    try {
      const res = await systemService.getLogs(params);
      if (res.success && res.data) {
        setLogs(res.data);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch system logs';
      setError(message);
    }
  }, []);

  const fetchBackups = useCallback(async () => {
    try {
      const res = await systemService.getBackups();
      if (res.success && res.data) {
        setBackups(res.data);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch backup inventory';
      setError(message);
    }
  }, []);

  const fetchVersion = useCallback(async () => {
    try {
      const res = await systemService.getVersion();
      if (res.success && res.data) {
        setVersion(res.data);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch release metadata';
      setError(message);
    }
  }, []);

  const fetchAll = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      await Promise.all([
        fetchHealth(),
        fetchMetrics(),
        fetchServices(),
        fetchLogs({ limit: 50 }),
        fetchBackups(),
        fetchVersion(),
      ]);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to synchronize system operations data';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [fetchHealth, fetchMetrics, fetchServices, fetchLogs, fetchBackups, fetchVersion]);

  // ==========================================================================
  // Mutations
  // ==========================================================================

  const triggerDeploy = useCallback(async (payload: DeployTriggerRequest): Promise<DeployTriggerData | null> => {
    try {
      setDeploying(true);
      setError(null);
      setSuccessMessage(null);
      const res = await systemService.triggerDeploy(payload);
      if (res.success && res.data) {
        setSuccessMessage(`Deployment for ${res.data.service_name} (${res.data.version}) initiated: ${res.data.status}`);
        await Promise.all([fetchServices(), fetchLogs()]);
        return res.data;
      }
      return null;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Deployment rollout failed';
      setError(message);
      return null;
    } finally {
      setDeploying(false);
    }
  }, [fetchServices, fetchLogs]);

  const createBackup = useCallback(async (payload: CreateBackupRequest) => {
    try {
      setCreatingBackup(true);
      setError(null);
      setSuccessMessage(null);
      const res = await systemService.createBackup(payload);
      if (res.success && res.data) {
        setSuccessMessage(`Backup snapshot created: ${res.data.backup_name}`);
        await fetchBackups();
        return res.data;
      }
      return null;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to initiate backup snapshot';
      setError(message);
      return null;
    } finally {
      setCreatingBackup(false);
    }
  }, [fetchBackups]);

  const flushCache = useCallback(async (payload: CacheFlushRequest) => {
    try {
      setFlushingCache(true);
      setError(null);
      setSuccessMessage(null);
      const res = await systemService.flushCache(payload);
      if (res.success && res.data) {
        setSuccessMessage(`Flushed ${res.data.flushed_namespaces.length} cache namespaces (~${res.data.keys_removed} keys purged).`);
        await fetchMetrics();
        return res.data;
      }
      return null;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to flush cache';
      setError(message);
      return null;
    } finally {
      setFlushingCache(false);
    }
  }, [fetchMetrics]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return {
    health,
    metrics,
    services,
    logs,
    backups,
    version,
    loading,
    deploying,
    creatingBackup,
    flushingCache,
    error,
    successMessage,
    clearError: () => setError(null),
    clearSuccess: () => setSuccessMessage(null),
    fetchAll,
    fetchHealth,
    fetchMetrics,
    fetchServices,
    fetchLogs,
    fetchBackups,
    fetchVersion,
    triggerDeploy,
    createBackup,
    flushCache,
  };
}

