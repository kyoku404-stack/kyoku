/**
 * KEEP Enterprise Platform — Plugin Execution Logs & Action Runner Drawer.
 *
 * Phase: 3.5
 * Role: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  X,
  Play,
  Terminal,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Zap,
} from 'lucide-react';
import type {
  PluginExecutionLog,
  PluginItem,
  PluginExecutionResponse,
  PluginExecutePayload,
} from '@/types/plugin';

interface PluginExecutionLogsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  logs: PluginExecutionLog[];
  selectedPlugin: PluginItem | null;
  onExecute: (pluginId: string, payload: PluginExecutePayload) => Promise<PluginExecutionResponse | null>;
  executing: boolean;
  lastExecution: PluginExecutionResponse | null;
  onRefreshLogs: () => void;
}

export const PluginExecutionLogsDrawer: React.FC<PluginExecutionLogsDrawerProps> = ({
  isOpen,
  onClose,
  logs,
  selectedPlugin,
  onExecute,
  executing,
  lastExecution,
  onRefreshLogs,
}) => {
  const [activeTab, setActiveTab] = useState<'logs' | 'tester'>('logs');
  const [actionName, setActionName] = useState<string>('sync_data');
  const [paramsJson, setParamsJson] = useState<string>('{\n  "limit": 10\n}');
  const [executionError, setExecutionError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleRunAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPlugin) return;
    try {
      setExecutionError(null);
      let parsed = {};
      try {
        parsed = JSON.parse(paramsJson);
      } catch {
        throw new Error('Parameters must be a valid JSON dictionary');
      }

      await onExecute(selectedPlugin.plugin_id, {
        action: actionName,
        parameters: parsed,
        timeout_seconds: 20.0,
      });
    } catch (err: unknown) {
      setExecutionError(err instanceof Error ? err.message : 'Execution failed');
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm animate-in fade-in">
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-xl bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col">
          {/* Header */}
          <div className="p-6 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20">
                <Terminal className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-white tracking-tight">
                  Sandbox Execution Telemetry
                </h3>
                <p className="text-xs text-slate-400">
                  {selectedPlugin ? selectedPlugin.name : 'All Extension Invocations'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={onRefreshLogs}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
                title="Refresh Logs"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
              <button
                onClick={onClose}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800 px-6 gap-6 bg-slate-950/40">
            <button
              onClick={() => setActiveTab('logs')}
              className={`py-3 text-xs font-semibold tracking-wider uppercase border-b-2 transition-all ${
                activeTab === 'logs'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Invocation Logs ({logs.length})
            </button>
            {selectedPlugin && (
              <button
                onClick={() => setActiveTab('tester')}
                className={`py-3 text-xs font-semibold tracking-wider uppercase border-b-2 transition-all ${
                  activeTab === 'tester'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Sandbox Action Tester
              </button>
            )}
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeTab === 'logs' ? (
              logs.length === 0 ? (
                <div className="text-center py-16 text-slate-500 text-sm">
                  No execution logs recorded yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {logs.map((log) => (
                    <div
                      key={log.id}
                      className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4 text-xs font-mono"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-indigo-400 font-semibold">{log.action}</span>
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold ${
                            log.status === 'SUCCESS'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}
                        >
                          {log.status === 'SUCCESS' ? (
                            <CheckCircle2 className="w-3 h-3" />
                          ) : (
                            <AlertTriangle className="w-3 h-3" />
                          )}
                          {log.status}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-slate-400 text-[11px] mb-1">
                        <div>Plugin: <span className="text-slate-300">{log.plugin_id}</span></div>
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          <span>{log.duration_ms} ms</span>
                        </div>
                      </div>

                      <div className="text-[10px] text-slate-500">
                        Triggered by {log.triggered_by} • {new Date(log.created_at).toLocaleTimeString()}
                      </div>

                      {log.error_message && (
                        <div className="mt-2 p-2 bg-rose-950/40 border border-rose-900/50 rounded text-rose-300 text-[11px]">
                          {log.error_message}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )
            ) : (
              /* Action Tester */
              <form onSubmit={handleRunAction} className="space-y-4">
                {executionError && (
                  <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-xs">
                    {executionError}
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                    Action / Method Name
                  </label>
                  <input
                    type="text"
                    value={actionName}
                    onChange={(e) => setActionName(e.target.value)}
                    required
                    className="w-full bg-slate-950/70 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/50"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
                    Input Parameters (JSON)
                  </label>
                  <textarea
                    rows={5}
                    value={paramsJson}
                    onChange={(e) => setParamsJson(e.target.value)}
                    className="w-full bg-slate-950/70 border border-slate-800 rounded-xl p-3 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500/50"
                  />
                </div>

                <button
                  type="submit"
                  disabled={executing}
                  className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-medium transition-colors inline-flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 disabled:opacity-50"
                >
                  <Play className="w-4 h-4" />
                  {executing ? 'Executing in sandbox...' : 'Invoke Sandboxed Action'}
                </button>

                {/* Last Execution Result Output */}
                {lastExecution && (
                  <div className="mt-6 border-t border-slate-800 pt-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                        <Zap className="w-3.5 h-3.5 text-amber-400" /> Execution Result
                      </span>
                      <span className="text-xs text-slate-400">{lastExecution.duration_ms} ms</span>
                    </div>
                    <pre className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs font-mono text-slate-200 overflow-x-auto max-h-60">
                      {JSON.stringify(lastExecution.result, null, 2)}
                    </pre>
                  </div>
                )}
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
