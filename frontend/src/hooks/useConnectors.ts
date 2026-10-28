/**
 * Phase 3.1 Enterprise Integrations & Connector Framework Custom Hook.
 * Manages connector lifecycle state, filters, active polling, registration,
 * authentication, synchronization, and telemetry inspection.
 *
 * Specification: docs/api/api-contract.md Section 13 & devdocs/p3/p3.1.txt
 * Author: Member 3 (Frontend & UI Lead)
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { connectorService } from '@/services/connectorService';
import type {
  ConnectorListItem,
  ConnectorStatusResponse,
  ConnectorSyncLogItem,
  ConnectorRegisterRequest,
  ConnectorAuthenticateRequest,
} from '@/types/connector';

export interface UseConnectorsReturn {
  connectors: ConnectorListItem[];
  filteredConnectors: ConnectorListItem[];
  selectedConnector: ConnectorListItem | null;
  activeStatus: ConnectorStatusResponse | null;
  logs: ConnectorSyncLogItem[];
  categoryFilter: string;
  statusFilter: string;
  searchQuery: string;
  isLoading: boolean;
  isSyncing: boolean;
  isRegisterModalOpen: boolean;
  isAuthModalOpen: boolean;
  isDrawerOpen: boolean;
  error: string | null;
  metrics: {
    totalConnectors: number;
    healthyCount: number;
    syncingCount: number;
    errorCount: number;
    totalDocsSynced: number;
  };
  setCategoryFilter: (category: string) => void;
  setStatusFilter: (status: string) => void;
  setSearchQuery: (query: string) => void;
  setSelectedConnector: (connector: ConnectorListItem | null) => void;
  setIsRegisterModalOpen: (open: boolean) => void;
  setIsAuthModalOpen: (open: boolean) => void;
  setIsDrawerOpen: (open: boolean) => void;
  refreshConnectors: () => Promise<void>;
  registerConnector: (req: ConnectorRegisterRequest) => Promise<boolean>;
  authenticateConnector: (req: ConnectorAuthenticateRequest) => Promise<boolean>;
  triggerSync: (connectorId: string, mode?: string) => Promise<boolean>;
  removeConnector: (connectorId: string) => Promise<boolean>;
  inspectConnectorStatus: (connectorId: string) => Promise<void>;
  fetchLogs: (connectorId?: string) => Promise<void>;
}

export function useConnectors(initialPollInterval: number = 5000): UseConnectorsReturn {
  const [connectors, setConnectors] = useState<ConnectorListItem[]>([]);
  const [selectedConnector, setSelectedConnector] = useState<ConnectorListItem | null>(null);
  const [activeStatus, setActiveStatus] = useState<ConnectorStatusResponse | null>(null);
  const [logs, setLogs] = useState<ConnectorSyncLogItem[]>([]);

  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState<boolean>(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // 1. Fetch connectors
  const fetchConnectors = useCallback(async () => {
    try {
      const res = await connectorService.list(
        categoryFilter !== 'ALL' ? categoryFilter : undefined,
        statusFilter !== 'ALL' ? statusFilter : undefined
      );
      if (res.success && res.data) {
        setConnectors(res.data.connectors);
        setError(null);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve connectors.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [categoryFilter, statusFilter]);

  // 2. Fetch logs
  const fetchLogs = useCallback(async (connectorId?: string) => {
    try {
      const res = await connectorService.getLogs(connectorId, 50);
      if (res.success && res.data) {
        setLogs(res.data.logs);
      }
    } catch (err: unknown) {
      console.error('Failed to load sync logs:', err);
    }
  }, []);

  // 3. Inspect Status
  const inspectConnectorStatus = useCallback(async (connectorId: string) => {
    try {
      const res = await connectorService.getStatus(connectorId);
      if (res.success && res.data) {
        setActiveStatus(res.data);
        setIsDrawerOpen(true);
      }
    } catch (err: unknown) {
      console.error('Failed to inspect connector status:', err);
    }
  }, []);

  // 4. Register
  const registerConnector = useCallback(
    async (req: ConnectorRegisterRequest): Promise<boolean> => {
      try {
        const res = await connectorService.register(req);
        if (res.success) {
          await fetchConnectors();
          setIsRegisterModalOpen(false);
          return true;
        }
        return false;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Registration failed.';
        setError(msg);
        return false;
      }
    },
    [fetchConnectors]
  );

  // 5. Authenticate
  const authenticateConnector = useCallback(
    async (req: ConnectorAuthenticateRequest): Promise<boolean> => {
      try {
        const res = await connectorService.authenticate(req);
        if (res.success) {
          await fetchConnectors();
          setIsAuthModalOpen(false);
          return true;
        }
        return false;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Authentication failed.';
        setError(msg);
        return false;
      }
    },
    [fetchConnectors]
  );

  // 6. Trigger Sync
  const triggerSync = useCallback(
    async (connectorId: string, mode: string = 'INCREMENTAL'): Promise<boolean> => {
      try {
        setIsSyncing(true);
        const res = await connectorService.sync({
          connector_id: connectorId,
          sync_mode: mode,
        });
        if (res.success) {
          await fetchConnectors();
          await fetchLogs(connectorId);
          return true;
        }
        return false;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Sync trigger failed.';
        setError(msg);
        return false;
      } finally {
        setIsSyncing(false);
      }
    },
    [fetchConnectors, fetchLogs]
  );

  // 7. Remove
  const removeConnector = useCallback(
    async (connectorId: string): Promise<boolean> => {
      try {
        const res = await connectorService.remove(connectorId);
        if (res.success) {
          await fetchConnectors();
          if (selectedConnector?.id === connectorId) {
            setSelectedConnector(null);
            setIsDrawerOpen(false);
          }
          return true;
        }
        return false;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Removal failed.';
        setError(msg);
        return false;
      }
    },
    [fetchConnectors, selectedConnector]
  );

  // Initial load
  useEffect(() => {
    fetchConnectors();
    fetchLogs();
  }, [fetchConnectors, fetchLogs]);

  // Polling when active sync is detected
  useEffect(() => {
    const hasSyncing = connectors.some((c) => c.status === 'SYNCING');
    if (!hasSyncing) return;

    const interval = setInterval(() => {
      fetchConnectors();
      fetchLogs();
    }, initialPollInterval);

    return () => clearInterval(interval);
  }, [connectors, initialPollInterval, fetchConnectors, fetchLogs]);

  // Computed metrics
  const metrics = useMemo(() => {
    const totalConnectors = connectors.length;
    const healthyCount = connectors.filter((c) => c.status === 'HEALTHY' || c.status === 'CONNECTED').length;
    const syncingCount = connectors.filter((c) => c.status === 'SYNCING').length;
    const errorCount = connectors.filter((c) => c.status === 'ERROR' || c.status === 'DEGRADED').length;
    const totalDocsSynced = connectors.reduce((acc, c) => acc + (c.total_documents_synced || 0), 0);

    return {
      totalConnectors,
      healthyCount,
      syncingCount,
      errorCount,
      totalDocsSynced,
    };
  }, [connectors]);

  // Filtered connectors by search
  const filteredConnectors = useMemo(() => {
    if (!searchQuery.trim()) return connectors;
    const q = searchQuery.toLowerCase();
    return connectors.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.platform_type.toLowerCase().includes(q) ||
        c.platform_category.toLowerCase().includes(q)
    );
  }, [connectors, searchQuery]);

  return {
    connectors,
    filteredConnectors,
    selectedConnector,
    activeStatus,
    logs,
    categoryFilter,
    statusFilter,
    searchQuery,
    isLoading,
    isSyncing,
    isRegisterModalOpen,
    isAuthModalOpen,
    isDrawerOpen,
    error,
    metrics,
    setCategoryFilter,
    setStatusFilter,
    setSearchQuery,
    setSelectedConnector,
    setIsRegisterModalOpen,
    setIsAuthModalOpen,
    setIsDrawerOpen,
    refreshConnectors: fetchConnectors,
    registerConnector,
    authenticateConnector,
    triggerSync,
    removeConnector,
    inspectConnectorStatus,
    fetchLogs,
  };
}
