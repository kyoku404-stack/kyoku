/**
 * KEEP Enterprise Platform — Phase 4.2 Agent Runtime & Execution Engine React Hook.
 *
 * Manages state and API interactions for registered agents, tenant-scoped execution ledger,
 * runtime telemetry metrics, result inspection, cooperative cancellation, and retries.
 */

import { useCallback, useEffect, useState } from 'react';
import { agentRuntimeService } from '@/services/agentRuntimeService';
import type {
  ExecutionRecordItem,
  ExecutionResultData,
  ExecutionStatus,
  RegisteredAgentItem,
  RetryExecutionRequest,
  RuntimeMetricsData,
  SubmitExecutionRequest,
} from '@/types/agentRuntime';

export type StatusFilter = 'ALL' | ExecutionStatus;

function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'message' in err && typeof (err as { message: unknown }).message === 'string') {
    return (err as { message: string }).message;
  }
  return fallback;
}

export function useAgentRuntime() {
  const [agents, setAgents] = useState<RegisteredAgentItem[]>([]);
  const [executions, setExecutions] = useState<ExecutionRecordItem[]>([]);
  const [metrics, setMetrics] = useState<RuntimeMetricsData | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('ALL');

  const [selectedExecution, setSelectedExecution] = useState<ExecutionRecordItem | null>(null);
  const [selectedResult, setSelectedResult] = useState<ExecutionResultData | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [loadingResult, setLoadingResult] = useState<boolean>(false);
  const [actioningId, setActioningId] = useState<string | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchAll = useCallback(async (filter: StatusFilter = statusFilter) => {
    setLoading(true);
    setError(null);
    try {
      const [agentsRes, execsRes, metricsRes] = await Promise.all([
        agentRuntimeService.listAgents(),
        agentRuntimeService.listExecutions(filter === 'ALL' ? { limit: 50 } : { status: filter, limit: 50 }),
        agentRuntimeService.getMetrics(),
      ]);
      setAgents(agentsRes.data.items);
      setExecutions(execsRes.data.items);
      setMetrics(metricsRes.data);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to load agent runtime telemetry and executions.'));
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    void fetchAll(statusFilter);
  }, [fetchAll, statusFilter]);

  const submitExecution = useCallback(
    async (
      agentId: string,
      payload: SubmitExecutionRequest,
      idempotencyKey?: string
    ): Promise<ExecutionRecordItem | null> => {
      setSubmitting(true);
      setError(null);
      setSuccessMessage(null);
      try {
        const res = await agentRuntimeService.submitExecution(agentId, payload, idempotencyKey);
        const created = res.data;
        setExecutions((prev) => {
          const exists = prev.some((item) => item.execution_id === created.execution_id);
          if (exists) {
            return prev.map((item) => (item.execution_id === created.execution_id ? created : item));
          }
          return [created, ...prev];
        });
        setSuccessMessage(res.message || `Execution '${created.execution_id}' submitted (${created.status}).`);
        // Refresh metrics snapshot in background
        try {
          const m = await agentRuntimeService.getMetrics();
          setMetrics(m.data);
        } catch {
          // non-blocking metrics refresh
        }
        return created;
      } catch (err) {
        setError(extractErrorMessage(err, 'Failed to submit agent execution.'));
        return null;
      } finally {
        setSubmitting(false);
      }
    },
    []
  );

  const inspectResult = useCallback(async (record: ExecutionRecordItem) => {
    setSelectedExecution(record);
    setSelectedResult(null);
    setLoadingResult(true);
    setError(null);
    try {
      const res = await agentRuntimeService.getExecutionResult(record.execution_id);
      setSelectedResult(res.data);
    } catch (err) {
      setError(extractErrorMessage(err, `Failed to load result for execution '${record.execution_id}'.`));
    } finally {
      setLoadingResult(false);
    }
  }, []);

  const closeResultDrawer = useCallback(() => {
    setSelectedExecution(null);
    setSelectedResult(null);
  }, []);

  const cancelExecution = useCallback(async (executionId: string) => {
    setActioningId(executionId);
    setError(null);
    setSuccessMessage(null);
    try {
      const res = await agentRuntimeService.cancelExecution(executionId);
      const updated = res.data;
      setExecutions((prev) =>
        prev.map((item) => (item.execution_id === updated.execution_id ? updated : item))
      );
      setSuccessMessage(res.message || `Cancellation requested for '${executionId}'.`);
      try {
        const m = await agentRuntimeService.getMetrics();
        setMetrics(m.data);
      } catch {
        // non-blocking
      }
    } catch (err) {
      setError(extractErrorMessage(err, `Failed to cancel execution '${executionId}'.`));
    } finally {
      setActioningId(null);
    }
  }, []);

  const retryExecution = useCallback(
    async (executionId: string, payload?: RetryExecutionRequest) => {
      setActioningId(executionId);
      setError(null);
      setSuccessMessage(null);
      try {
        const res = await agentRuntimeService.retryExecution(executionId, payload);
        const created = res.data;
        setExecutions((prev) => [created, ...prev]);
        setSuccessMessage(res.message || `Retry attempt #${created.attempt_number} created.`);
        try {
          const m = await agentRuntimeService.getMetrics();
          setMetrics(m.data);
        } catch {
          // non-blocking
        }
      } catch (err) {
        setError(extractErrorMessage(err, `Failed to retry execution '${executionId}'.`));
      } finally {
        setActioningId(null);
      }
    },
    []
  );

  return {
    agents,
    executions,
    metrics,
    statusFilter,
    selectedExecution,
    selectedResult,
    loading,
    submitting,
    loadingResult,
    actioningId,
    error,
    successMessage,
    setStatusFilter,
    setError,
    setSuccessMessage,
    refreshAll: () => fetchAll(statusFilter),
    submitExecution,
    inspectResult,
    closeResultDrawer,
    cancelExecution,
    retryExecution,
  };
}
