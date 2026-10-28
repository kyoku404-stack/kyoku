/**
 * KEEP Enterprise Platform — Enterprise Integrations & Connector Framework Master Page (Phase 3.1).
 *
 * Centralized integration command center connecting external enterprise platforms
 * (Google Drive, SharePoint, OneDrive, GitHub, Slack, Notion, Jira, Confluence)
 * to KEEP's unified RAG search and knowledge pipelines.
 *
 * Specification: docs/api/api-contract.md Section 13 & devdocs/p3/p3.1.txt
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import { useConnectors } from '@/hooks/useConnectors';
import {
  ConnectorMetricsBanner,
  ConnectorGrid,
  RegisterConnectorModal,
  AuthenticateModal,
  ConnectorStatusDrawer,
  SyncHistoryTable,
} from '@/features/connectors';
import {
  Layers,
  History,
  AlertCircle,
} from 'lucide-react';
import type { ConnectorListItem } from '@/types/connector';

export const IntegrationsPage: React.FC = () => {
  const {
    filteredConnectors,
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
    refreshConnectors,
    registerConnector,
    authenticateConnector,
    triggerSync,
    removeConnector,
    inspectConnectorStatus,
    fetchLogs,
  } = useConnectors(5000);

  const [activeTab, setActiveTab] = useState<'CONNECTORS' | 'HISTORY'>('CONNECTORS');
  const [authTargetConnector, setAuthTargetConnector] = useState<ConnectorListItem | null>(null);

  const handleOpenAuth = (connector: ConnectorListItem) => {
    setAuthTargetConnector(connector);
    setIsAuthModalOpen(true);
  };

  return (
    <div className="flex-1 space-y-6 p-6 md:p-8 max-w-7xl mx-auto w-full">
      {/* Top Banner & KPI Counters */}
      <ConnectorMetricsBanner
        metrics={metrics}
        onRegisterClick={() => setIsRegisterModalOpen(true)}
        onRefreshClick={refreshConnectors}
        isLoading={isLoading}
      />

      {/* Error alert if any */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-xl border border-rose-200 dark:border-rose-800 bg-rose-50 dark:bg-rose-950/60 text-sm text-rose-700 dark:text-rose-300 shadow-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span className="flex-1">{error}</span>
          <button
            type="button"
            onClick={refreshConnectors}
            className="text-xs font-semibold underline hover:no-underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* View Switcher Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
        <button
          type="button"
          onClick={() => setActiveTab('CONNECTORS')}
          className={`inline-flex items-center gap-2 px-3.5 py-2 text-sm font-semibold rounded-lg transition-colors ${
            activeTab === 'CONNECTORS'
              ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/70 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800'
          }`}
        >
          <Layers className="w-4 h-4" />
          Configured Connectors ({filteredConnectors.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('HISTORY')}
          className={`inline-flex items-center gap-2 px-3.5 py-2 text-sm font-semibold rounded-lg transition-colors ${
            activeTab === 'HISTORY'
              ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/70 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800'
          }`}
        >
          <History className="w-4 h-4" />
          Synchronization History
        </button>
      </div>

      {/* Main Content Area */}
      {activeTab === 'CONNECTORS' ? (
        <ConnectorGrid
          connectors={filteredConnectors}
          isLoading={isLoading}
          categoryFilter={categoryFilter}
          statusFilter={statusFilter}
          searchQuery={searchQuery}
          onCategoryChange={setCategoryFilter}
          onStatusChange={setStatusFilter}
          onSearchChange={setSearchQuery}
          onSync={(id) => triggerSync(id)}
          onInspectStatus={inspectConnectorStatus}
          onAuthenticate={handleOpenAuth}
          onRemove={removeConnector}
          onRegisterClick={() => setIsRegisterModalOpen(true)}
        />
      ) : (
        <SyncHistoryTable
          logs={logs}
          isLoading={isLoading}
          onRefresh={() => fetchLogs()}
        />
      )}

      {/* Registration Modal */}
      <RegisterConnectorModal
        isOpen={isRegisterModalOpen}
        onClose={() => setIsRegisterModalOpen(false)}
        onSubmit={registerConnector}
      />

      {/* Authentication Modal */}
      <AuthenticateModal
        isOpen={isAuthModalOpen}
        connector={authTargetConnector}
        onClose={() => {
          setIsAuthModalOpen(false);
          setAuthTargetConnector(null);
        }}
        onSubmit={authenticateConnector}
      />

      {/* Status & Telemetry Detail Drawer */}
      <ConnectorStatusDrawer
        isOpen={isDrawerOpen}
        status={activeStatus}
        onClose={() => {
          setIsDrawerOpen(false);
          setSelectedConnector(null);
        }}
        onTriggerSync={(id) => triggerSync(id)}
        isSyncing={isSyncing}
      />
    </div>
  );
};

export default IntegrationsPage;
