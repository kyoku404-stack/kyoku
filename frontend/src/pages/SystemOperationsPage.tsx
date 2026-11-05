/**
 * KEEP Enterprise Platform — Production Infrastructure, Scalability & Observability Master Page.
 *
 * Phase: 3.6
 * Specification: devdocs/p3/p3.6.txt & docs/api/api-contract.md (Section 18)
 * Role: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Flame,
  RefreshCw,
  Rocket,
  Server,
  ShieldCheck,
  Terminal,
} from 'lucide-react';
import { useSystemOperations } from '@/hooks/useSystemOperations';
import {
  CacheFlushModal,
  DeployServiceModal,
  DisasterRecoveryPanel,
  MicroservicesGrid,
  SystemHealthDrawer,
  SystemLogsViewer,
  SystemMetricsBanner,
} from '@/features/system';

export const SystemOperationsPage: React.FC = () => {
  const {
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
    clearError,
    clearSuccess,
    fetchAll,
    fetchLogs,
    triggerDeploy,
    createBackup,
    flushCache,
  } = useSystemOperations();

  const [activeTab, setActiveTab] = useState<'overview' | 'dr' | 'logs'>('overview');
  const [isHealthDrawerOpen, setIsHealthDrawerOpen] = useState(false);
  const [isDeployModalOpen, setIsDeployModalOpen] = useState(false);
  const [selectedServiceToDeploy, setSelectedServiceToDeploy] = useState('keep-backend-api');
  const [isCacheModalOpen, setIsCacheModalOpen] = useState(false);

  const handleOpenDeploy = (serviceName?: string) => {
    setSelectedServiceToDeploy(serviceName || 'keep-backend-api');
    setIsDeployModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-tr from-indigo-500 to-cyan-500 rounded-xl text-white shadow-lg shadow-indigo-500/20">
              <Server className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-white tracking-tight">System Operations</h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Phase 3.6
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-slate-800 text-slate-400">
                  v{version?.version ?? '3.6.0'} ({version?.git_commit ?? '599b185'})
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Cloud-native Kubernetes infrastructure, high availability, telemetry, and disaster recovery.
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={() => setIsHealthDrawerOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-medium border border-slate-700 transition-colors"
          >
            <Activity className="w-4 h-4 text-emerald-400" />
            Diagnostics
          </button>

          <button
            type="button"
            onClick={() => setIsCacheModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-medium border border-slate-700 transition-colors"
          >
            <Flame className="w-4 h-4 text-rose-400" />
            Flush Cache
          </button>

          <button
            type="button"
            onClick={() => handleOpenDeploy()}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-indigo-600/30 transition-all"
          >
            <Rocket className="w-4 h-4" />
            Deploy Service
          </button>

          <button
            type="button"
            onClick={fetchAll}
            disabled={loading}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-xl border border-slate-700 transition-colors"
            title="Refresh All Operations Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center justify-between text-xs animate-in fade-in">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
          <button type="button" onClick={clearError} className="hover:text-white text-rose-400">
            Dismiss
          </button>
        </div>
      )}

      {successMessage && (
        <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 flex items-center justify-between text-xs animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMessage}</span>
          </div>
          <button type="button" onClick={clearSuccess} className="hover:text-white text-emerald-400">
            Dismiss
          </button>
        </div>
      )}

      {/* Master KPI Telemetry Banner */}
      <SystemMetricsBanner
        health={health}
        metrics={metrics}
        onViewSubsystems={() => setIsHealthDrawerOpen(true)}
      />

      {/* Primary Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 mb-6 pb-2">
        <button
          type="button"
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'overview'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
          }`}
        >
          <Server className="w-4 h-4" />
          Microservices Topology ({services.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('dr')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'dr'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          Disaster Recovery & Backups ({backups?.backups.length ?? 0})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('logs')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'logs'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
          }`}
        >
          <Terminal className="w-4 h-4" />
          Operational Logs ({logs.length})
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === 'overview' && (
        <MicroservicesGrid
          services={services}
          onDeployService={(name) => handleOpenDeploy(name)}
        />
      )}

      {activeTab === 'dr' && (
        <DisasterRecoveryPanel
          backupsData={backups}
          onCreateBackup={createBackup}
          creatingBackup={creatingBackup}
        />
      )}

      {activeTab === 'logs' && (
        <SystemLogsViewer
          logs={logs}
          onRefresh={fetchLogs}
          loading={loading}
        />
      )}

      {/* Drawers and Modals */}
      <SystemHealthDrawer
        isOpen={isHealthDrawerOpen}
        onClose={() => setIsHealthDrawerOpen(false)}
        health={health}
      />

      <DeployServiceModal
        isOpen={isDeployModalOpen}
        onClose={() => setIsDeployModalOpen(false)}
        initialService={selectedServiceToDeploy}
        onDeploy={triggerDeploy}
        deploying={deploying}
      />

      <CacheFlushModal
        isOpen={isCacheModalOpen}
        onClose={() => setIsCacheModalOpen(false)}
        onFlush={flushCache}
        flushing={flushingCache}
      />
    </div>
  );
};
