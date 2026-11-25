import { useCallback, useEffect, useState } from 'react';
import { autonomousWorkflowService } from '@/services/autonomousWorkflowService';
import type {
  AutonomousStepRecord,
  AutonomousWorkflowRecord,
  AutonomousWorkflowRequest,
  AutonomyStatus,
  AutonomyTimelineResponse,
} from '@/types/autonomy';

export function useAutonomousWorkflows() {
  const [workflows, setWorkflows] = useState<AutonomousWorkflowRecord[]>([]);
  const [statusFilter, setStatusFilter] = useState<AutonomyStatus | 'all'>('all');
  const [selectedWorkflow, setSelectedWorkflow] = useState<AutonomousWorkflowRecord | null>(null);
  const [steps, setSteps] = useState<AutonomousStepRecord[]>([]);
  const [timeline, setTimeline] = useState<AutonomyTimelineResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isUpdatingAction, setIsUpdatingAction] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const inspectWorkflow = useCallback(async (executionId: string) => {
    setError(null);
    try {
      const [wfRes, stepsRes, eventsRes] = await Promise.all([
        autonomousWorkflowService.getWorkflow(executionId),
        autonomousWorkflowService.listSteps(executionId),
        autonomousWorkflowService.getEvents(executionId),
      ]);
      setSelectedWorkflow(wfRes.data);
      setSteps(stepsRes.data ?? []);
      setTimeline(eventsRes.data ?? { execution_id: executionId, decisions: [], events: [] });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load workflow details.');
    }
  }, []);

  const refreshWorkflows = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = statusFilter === 'all' ? { limit: 50 } : { status: statusFilter, limit: 50 };
      const res = await autonomousWorkflowService.listWorkflows(params);
      const list = res.data ?? [];
      setWorkflows(list);
      if (selectedWorkflow) {
        const updated = list.find((w) => w.execution_id === selectedWorkflow.execution_id);
        if (updated) {
          setSelectedWorkflow(updated);
        }
      } else if (list.length > 0) {
        await inspectWorkflow(list[0].execution_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load autonomous workflows.');
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter, selectedWorkflow, inspectWorkflow]);

  useEffect(() => {
    void refreshWorkflows();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  const startWorkflow = useCallback(
    async (payload: AutonomousWorkflowRequest) => {
      setIsSubmitting(true);
      setError(null);
      try {
        const res = await autonomousWorkflowService.startWorkflow(payload);
        const created = res.data;
        setWorkflows((prev) => [
          created,
          ...prev.filter((w) => w.execution_id !== created.execution_id),
        ]);
        await inspectWorkflow(created.execution_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to start autonomous workflow.');
      } finally {
        setIsSubmitting(false);
      }
    },
    [inspectWorkflow]
  );

  const resumeWorkflow = useCallback(
    async (executionId: string, approve: boolean, reason: string) => {
      setIsUpdatingAction(true);
      setError(null);
      try {
        const res = await autonomousWorkflowService.resumeWorkflow(executionId, { approve, reason });
        setWorkflows((prev) =>
          prev.map((w) => (w.execution_id === executionId ? res.data : w))
        );
        await inspectWorkflow(executionId);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to resume autonomous workflow.');
      } finally {
        setIsUpdatingAction(false);
      }
    },
    [inspectWorkflow]
  );

  const cancelWorkflow = useCallback(
    async (executionId: string, reason: string) => {
      setIsUpdatingAction(true);
      setError(null);
      try {
        const res = await autonomousWorkflowService.cancelWorkflow(executionId, { reason });
        setWorkflows((prev) =>
          prev.map((w) => (w.execution_id === executionId ? res.data : w))
        );
        await inspectWorkflow(executionId);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to cancel autonomous workflow.');
      } finally {
        setIsUpdatingAction(false);
      }
    },
    [inspectWorkflow]
  );

  return {
    workflows,
    statusFilter,
    selectedWorkflow,
    steps,
    timeline,
    isLoading,
    isSubmitting,
    isUpdatingAction,
    error,
    setStatusFilter,
    refreshWorkflows,
    startWorkflow,
    inspectWorkflow,
    resumeWorkflow,
    cancelWorkflow,
  };
}
