/**
 * KEEP Enterprise Platform — Phase 4.2 Agent Runtime & Execution Engine Master Page.
 *
 * Operations command center for inspecting registered KEEP agents, dispatching sync/async
 * executions, monitoring live runtime telemetry, inspecting grounded results & evidence,
 * and issuing cooperative cancellations or bounded retries.
 */

import React, { useState } from 'react';
import {
  AlertCircle,
  Bot,
  CheckCircle2,
  Cpu,
  Play,
  RefreshCw,
} from 'lucide-react';
import { useAgentRuntime } from '@/hooks/useAgentRuntime';
import { useAuthorization } from '@/hooks/useAuthorization';
import { Permission } from '@/types/permission';
import {
  ExecuteAgentModal,
  ExecutionListTable,
  ExecutionResultDrawer,
  RuntimeMetricsBanner,
} from '@/features/agents';

export const AgentRuntimePage: React.FC = () => {
  const {
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
    refreshAll,
    submitExecution,
    inspectResult,
    closeResultDrawer,
    cancelExecution,
    retryExecution,
  } = useAgentRuntime();

  const { can } = useAuthorization();
  const canInvoke = can(Permission.AGENT_INVOKE);

  const [isExecuteModalOpen, setIsExecuteModalOpen] = useState(false);
  const [preselectedAgentId, setPreselectedAgentId] = useState<string | undefined>(undefined);

  const openModalForAgent = (agentId?: string) => {
    setPreselectedAgentId(agentId);
    setIsExecuteModalOpen(true);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-xs border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-xl">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Agent Runtime &amp; Execution Engine
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
                Phase 4.2
              </span>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Durable agent execution lifecycle, bounded retries, cooperative cancellation, and LangGraph checkpointing.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => void refreshAll()}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>

          {canInvoke && (
            <button
              type="button"
              onClick={() => openModalForAgent(agents[0]?.agent_id)}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-xs transition-colors"
            >
              <Play className="w-4 h-4" />
              Run Agent
            </button>
          )}
        </div>
      </div>

      {/* Success Banner */}
      {successMessage && (
        <div
          role="status"
          className="p-4 bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-700/50 rounded-xl flex items-center justify-between text-xs text-emerald-800 dark:text-emerald-200"
        >
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <span>{successMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => setSuccessMessage(null)}
            className="text-emerald-700 dark:text-emerald-400 hover:underline font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div
          role="alert"
          className="p-4 bg-rose-50 dark:bg-rose-900/30 border border-rose-200 dark:border-rose-700/50 rounded-xl flex items-center justify-between text-xs text-rose-800 dark:text-rose-200"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={() => setError(null)}
            className="text-rose-700 dark:text-rose-400 hover:underline font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Live Telemetry KPI Banner */}
      <RuntimeMetricsBanner metrics={metrics} loading={loading} />

      {/* Registered Agents Strip */}
      <section aria-label="Registered Agents" className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-600 dark:text-gray-300">
            Registered Agents ({agents.length})
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <div
              key={agent.agent_id}
              className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-xs flex flex-col justify-between gap-3"
            >
              <div>
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Bot className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                    <h3 className="font-bold text-gray-900 dark:text-white text-sm">
                      {agent.name}
                    </h3>
                  </div>
                  <span className="px-2 py-0.5 rounded-full text-[11px] font-mono bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                    v{agent.version}
                  </span>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1.5">
                  {agent.description}
                </p>
                {agent.capabilities && agent.capabilities.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {agent.capabilities.map((cap) => (
                      <span
                        key={cap.name}
                        className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300"
                      >
                        {cap.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-gray-700/60">
                <span className="text-[11px] font-mono text-gray-500 dark:text-gray-400">
                  {agent.agent_id}
                </span>
                {canInvoke && (
                  <button
                    type="button"
                    onClick={() => openModalForAgent(agent.agent_id)}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
                  >
                    <Play className="w-3.5 h-3.5" />
                    Launch
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Durable Execution Ledger */}
      <ExecutionListTable
        executions={executions}
        statusFilter={statusFilter}
        loading={loading}
        actioningId={actioningId}
        canInvoke={canInvoke}
        onFilterChange={setStatusFilter}
        onInspect={(record) => void inspectResult(record)}
        onCancel={(id) => void cancelExecution(id)}
        onRetry={(id) => void retryExecution(id)}
      />

      {/* Submit Execution Modal */}
      <ExecuteAgentModal
        isOpen={isExecuteModalOpen}
        agents={agents}
        initialAgentId={preselectedAgentId}
        submitting={submitting}
        onClose={() => setIsExecuteModalOpen(false)}
        onSubmit={submitExecution}
      />

      {/* Result & Evidence Inspection Drawer */}
      <ExecutionResultDrawer
        execution={selectedExecution}
        result={selectedResult}
        loading={loadingResult}
        onClose={closeResultDrawer}
      />
    </div>
  );
};

export default AgentRuntimePage;
