/**
 * KEEP Enterprise Platform — useIngestion Custom Hook (Phase 2.1).
 *
 * Provides real-time polling, pagination, filtering, state management,
 * and mutations for the AI Knowledge Ingestion Pipeline.
 *
 * Author: Member 3 (Frontend Lead)
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { ingestionService } from '@/services/ingestionService';
import type {
  IngestionJobListItem,
  IngestionJobStatusResponseData,
  IngestionStatisticsResponseData,
  StartIngestionRequest,
} from '@/types/ingestion';

export interface UseIngestionOptions {
  pollingInterval?: number; // ms, default 5000
  autoStart?: boolean;
  initialPageSize?: number;
}

export function useIngestion(options: UseIngestionOptions = {}) {
  const {
    pollingInterval = 5000,
    autoStart = true,
    initialPageSize = 10,
  } = options;

  const [jobs, setJobs] = useState<IngestionJobListItem[]>([]);
  const [statistics, setStatistics] = useState<IngestionStatisticsResponseData | null>(null);
  const [selectedJobStatus, setSelectedJobStatus] = useState<IngestionJobStatusResponseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isPolling, setIsPolling] = useState<boolean>(autoStart);

  // Pagination & Filtering state
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(initialPageSize);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalJobs, setTotalJobs] = useState<number>(0);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [documentIdFilter, setDocumentIdFilter] = useState<string | null>(null);

  const isMountedRef = useRef<boolean>(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  /**
   * Refreshes the jobs list and overall pipeline statistics.
   */
  const refresh = useCallback(async () => {
    try {
      setError(null);
      const [jobsRes, statsRes] = await Promise.allSettled([
        ingestionService.listIngestionJobs({
          page,
          page_size: pageSize,
          status: statusFilter || undefined,
          document_id: documentIdFilter || undefined,
        }),
        ingestionService.getIngestionStatistics(),
      ]);

      if (!isMountedRef.current) return;

      if (jobsRes.status === 'fulfilled' && jobsRes.value.success) {
        setJobs(jobsRes.value.data.items);
        setTotalJobs(jobsRes.value.data.total);
        setTotalPages(jobsRes.value.data.total_pages || 1);
      } else if (jobsRes.status === 'rejected') {
        const errMsg = jobsRes.reason?.response?.data?.message || jobsRes.reason?.message || 'Failed to fetch ingestion jobs';
        setError(errMsg);
      }

      if (statsRes.status === 'fulfilled' && statsRes.value.success) {
        setStatistics(statsRes.value.data);
      }

      setLastUpdated(new Date());
    } catch (err: unknown) {
      if (!isMountedRef.current) return;
      const e = err as { message?: string };
      setError(e.message || 'Error refreshing ingestion pipeline');
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [page, pageSize, statusFilter, documentIdFilter]);

  // Initial load
  useEffect(() => {
    refresh();
  }, [refresh]);

  // Auto-polling interval
  useEffect(() => {
    if (!isPolling) return;

    const timer = setInterval(() => {
      refresh();
    }, pollingInterval);

    return () => clearInterval(timer);
  }, [isPolling, pollingInterval, refresh]);

  /**
   * Poll active selected job if it is open and in a processing state
   */
  const fetchJobStatus = useCallback(async (id: string) => {
    try {
      const res = await ingestionService.getIngestionStatus(id);
      if (isMountedRef.current && res.success) {
        setSelectedJobStatus(res.data);
        return res.data;
      }
    } catch (err: unknown) {
      if (isMountedRef.current) {
        const e = err as { message?: string };
        setError(e.message || 'Failed to fetch job progress');
      }
    }
    return null;
  }, []);

  /**
   * Trigger new ingestion job on a document
   */
  const startIngestion = useCallback(
    async (payload: StartIngestionRequest) => {
      setActionLoading(true);
      setError(null);
      try {
        const res = await ingestionService.startIngestion(payload);
        if (res.success) {
          await refresh();
          // Immediately fetch the created job's status
          if (res.data.job_id) {
            await fetchJobStatus(res.data.job_id);
          }
          return res.data;
        }
      } catch (err: unknown) {
        const e = err as { response?: { data?: { message?: string } }; message?: string };
        const msg = e.response?.data?.message || e.message || 'Failed to start ingestion job';
        setError(msg);
        throw new Error(msg);
      } finally {
        if (isMountedRef.current) {
          setActionLoading(false);
        }
      }
      return null;
    },
    [refresh, fetchJobStatus]
  );

  /**
   * Retry a failed ingestion job
   */
  const retryJob = useCallback(
    async (jobId: string) => {
      setActionLoading(true);
      setError(null);
      try {
        const res = await ingestionService.retryIngestionJob(jobId);
        if (res.success) {
          await refresh();
          await fetchJobStatus(jobId);
          return res.data;
        }
      } catch (err: unknown) {
        const e = err as { response?: { data?: { message?: string } }; message?: string };
        const msg = e.response?.data?.message || e.message || 'Failed to retry ingestion job';
        setError(msg);
        throw new Error(msg);
      } finally {
        if (isMountedRef.current) {
          setActionLoading(false);
        }
      }
      return null;
    },
    [refresh, fetchJobStatus]
  );

  const togglePolling = useCallback(() => {
    setIsPolling((prev) => !prev);
  }, []);

  return {
    jobs,
    statistics,
    selectedJobStatus,
    loading,
    actionLoading,
    error,
    lastUpdated,
    isPolling,
    page,
    pageSize,
    totalPages,
    totalJobs,
    statusFilter,
    documentIdFilter,
    refresh,
    fetchJobStatus,
    startIngestion,
    retryJob,
    setPage,
    setPageSize,
    setStatusFilter,
    setDocumentIdFilter,
    setSelectedJobStatus,
    togglePolling,
    setError,
  };
}

export default useIngestion;
