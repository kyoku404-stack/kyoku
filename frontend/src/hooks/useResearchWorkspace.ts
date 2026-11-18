/**
 * KEEP Phase 4.5 — React Hook managing the Research Agents Workspace state.
 */

import { useCallback, useEffect, useState } from 'react';
import { researchService } from '@/services/researchService';
import type {
  EvidenceItem,
  ResearchReport,
  ResearchRunRecord,
  ResearchStatus,
  StartResearchRequest,
} from '@/types/research';

export interface ResearchWorkspaceState {
  runs: ResearchRunRecord[];
  statusFilter: ResearchStatus | 'all';
  selectedRunId: string | null;
  activeReport: ResearchReport | null;
  evidenceDrawerOpen: boolean;
  evidenceItems: EvidenceItem[];
  evidenceRedactedCount: number;
  highlightedEvidenceId: string | null;
  isLoadingRuns: boolean;
  isSubmitting: boolean;
  isLoadingReport: boolean;
  isLoadingEvidence: boolean;
  error: string | null;
  setStatusFilter: (status: ResearchStatus | 'all') => void;
  refreshRuns: () => Promise<void>;
  launchResearch: (payload: StartResearchRequest, idempotencyKey?: string) => Promise<void>;
  inspectReport: (researchId: string) => Promise<void>;
  openEvidenceDrawer: (researchId: string, highlightEvidenceId?: string) => Promise<void>;
  closeEvidenceDrawer: () => void;
  cancelResearch: (researchId: string) => Promise<void>;
}

export function useResearchWorkspace(): ResearchWorkspaceState {
  const [runs, setRuns] = useState<ResearchRunRecord[]>([]);
  const [statusFilter, setStatusFilter] = useState<ResearchStatus | 'all'>('all');
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [activeReport, setActiveReport] = useState<ResearchReport | null>(null);
  const [evidenceDrawerOpen, setEvidenceDrawerOpen] = useState(false);
  const [evidenceItems, setEvidenceItems] = useState<EvidenceItem[]>([]);
  const [evidenceRedactedCount, setEvidenceRedactedCount] = useState(0);
  const [highlightedEvidenceId, setHighlightedEvidenceId] = useState<string | null>(null);
  const [isLoadingRuns, setIsLoadingRuns] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [isLoadingEvidence, setIsLoadingEvidence] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshRuns = useCallback(async () => {
    setIsLoadingRuns(true);
    setError(null);
    try {
      const response = await researchService.listRuns(
        statusFilter === 'all' ? { limit: 50 } : { status: statusFilter, limit: 50 }
      );
      setRuns(response.data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load research investigations.');
    } finally {
      setIsLoadingRuns(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    void refreshRuns();
  }, [refreshRuns]);

  const inspectReport = useCallback(async (researchId: string) => {
    setSelectedRunId(researchId);
    setIsLoadingReport(true);
    setError(null);
    try {
      const response = await researchService.getReport(researchId);
      setActiveReport(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load research report.');
    } finally {
      setIsLoadingReport(false);
    }
  }, []);

  const openEvidenceDrawer = useCallback(
    async (researchId: string, highlightEvidenceId?: string) => {
      setSelectedRunId(researchId);
      setHighlightedEvidenceId(highlightEvidenceId ?? null);
      setEvidenceDrawerOpen(true);
      setIsLoadingEvidence(true);
      setError(null);
      try {
        const response = await researchService.getEvidence(researchId);
        setEvidenceItems(response.data.items);
        setEvidenceRedactedCount(response.data.redacted_count);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load evidence provenance.');
      } finally {
        setIsLoadingEvidence(false);
      }
    },
    []
  );

  const closeEvidenceDrawer = useCallback(() => {
    setEvidenceDrawerOpen(false);
    setHighlightedEvidenceId(null);
  }, []);

  const launchResearch = useCallback(
    async (payload: StartResearchRequest, idempotencyKey?: string) => {
      setIsSubmitting(true);
      setError(null);
      try {
        const res = await researchService.startResearch(payload, idempotencyKey);
        setSelectedRunId(res.data.research_id);
        if (res.data.report) {
          setActiveReport(res.data.report);
        }
        await refreshRuns();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to start research investigation.');
      } finally {
        setIsSubmitting(false);
      }
    },
    [refreshRuns]
  );

  const cancelResearch = useCallback(
    async (researchId: string) => {
      setError(null);
      try {
        await researchService.cancelRun(researchId);
        await refreshRuns();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to cancel research investigation.');
      }
    },
    [refreshRuns]
  );

  return {
    runs,
    statusFilter,
    selectedRunId,
    activeReport,
    evidenceDrawerOpen,
    evidenceItems,
    evidenceRedactedCount,
    highlightedEvidenceId,
    isLoadingRuns,
    isSubmitting,
    isLoadingReport,
    isLoadingEvidence,
    error,
    setStatusFilter,
    refreshRuns,
    launchResearch,
    inspectReport,
    openEvidenceDrawer,
    closeEvidenceDrawer,
    cancelResearch,
  };
}
