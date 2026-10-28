/**
 * Phase 3.4 WorkflowListTable Component.
 * Displays interactive tabular list of configured workflows with execution triggers and controls.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  Play,
  Trash2,
  Layers,
  ChevronDown,
  ChevronRight,
  ToggleLeft,
  ToggleRight,
  Filter,
} from 'lucide-react';
import type { WorkflowItem, WorkflowTriggerType } from '@/types/workflow';

interface WorkflowListTableProps {
  workflows: WorkflowItem[];
  onExecute: (id: string) => void;
  onToggleActive: (id: string, currentActive: boolean) => void;
  onDelete: (id: string) => void;
  onSelectWorkflow: (workflow: WorkflowItem) => void;
  isExecutingId: string | null;
}

const triggerLabels: Record<WorkflowTriggerType, { label: string; color: string }> = {
  document_created: { label: 'Document Created', color: 'bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300' },
  document_updated: { label: 'Document Updated', color: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300' },
  security_anomaly: { label: 'Security Anomaly', color: 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300' },
  connector_synced: { label: 'Connector Synced', color: 'bg-purple-50 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300' },
  meeting_completed: { label: 'Meeting Completed', color: 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300' },
  manual: { label: 'Manual Trigger', color: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300' },
  scheduled: { label: 'Scheduled Cron', color: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300' },
};

export const WorkflowListTable: React.FC<WorkflowListTableProps> = ({
  workflows,
  onExecute,
  onToggleActive,
  onDelete,
  onSelectWorkflow,
  isExecutingId,
}) => {
  const [filterTrigger, setFilterTrigger] = useState<string>('all');
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null);

  const filteredWorkflows = workflows.filter((w) => {
    if (filterTrigger === 'all') return true;
    return w.trigger_type === filterTrigger;
  });

  const toggleExpand = (id: string) => {
    setExpandedRowId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="bg-white dark:bg-slate-850 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
      {/* Table Header & Filter Bar */}
      <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          <h2 className="text-base font-semibold text-slate-900 dark:text-white">
            Configured Workflows
          </h2>
          <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
            {filteredWorkflows.length}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={filterTrigger}
            onChange={(e) => setFilterTrigger(e.target.value)}
            className="text-xs font-medium bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All Triggers</option>
            <option value="document_created">Document Created</option>
            <option value="document_updated">Document Updated</option>
            <option value="security_anomaly">Security Anomaly</option>
            <option value="connector_synced">Connector Synced</option>
            <option value="meeting_completed">Meeting Completed</option>
            <option value="manual">Manual Trigger</option>
            <option value="scheduled">Scheduled Cron</option>
          </select>
        </div>
      </div>

      {/* Table Body */}
      {filteredWorkflows.length === 0 ? (
        <div className="py-12 text-center text-slate-500 dark:text-slate-400">
          <Layers className="w-8 h-8 mx-auto mb-2 text-slate-300 dark:text-slate-600" />
          <p className="text-sm font-medium">No workflows found</p>
          <p className="text-xs text-slate-400 mt-1">Create a new workflow or select a pre-built template below.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 dark:border-slate-800 text-xs font-semibold text-slate-500 dark:text-slate-400 bg-slate-50/50 dark:bg-slate-800/30">
                <th className="py-3 px-4 w-8"></th>
                <th className="py-3 px-4">Workflow Name</th>
                <th className="py-3 px-4">Trigger</th>
                <th className="py-3 px-4">Steps</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Executions</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-sm">
              {filteredWorkflows.map((workflow) => {
                const triggerConfig = triggerLabels[workflow.trigger_type] || {
                  label: workflow.trigger_type,
                  color: 'bg-slate-100 text-slate-700',
                };
                const isExpanded = expandedRowId === workflow.id;
                const isExecuting = isExecutingId === workflow.id;

                return (
                  <React.Fragment key={workflow.id}>
                    <tr className="hover:bg-slate-50/70 dark:hover:bg-slate-800/50 transition-colors">
                      <td className="py-3.5 px-4">
                        <button
                          type="button"
                          onClick={() => toggleExpand(workflow.id)}
                          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                        >
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </button>
                      </td>
                      <td className="py-3.5 px-4">
                        <button
                          type="button"
                          onClick={() => onSelectWorkflow(workflow)}
                          className="text-left font-medium text-slate-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                        >
                          {workflow.name}
                        </button>
                        {workflow.description && (
                          <p className="text-xs text-slate-500 dark:text-slate-400 truncate max-w-sm">
                            {workflow.description}
                          </p>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${triggerConfig.color}`}>
                          {triggerConfig.label}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-600 dark:text-slate-300 font-mono text-xs">
                        {workflow.steps?.length ?? 0} actions
                      </td>
                      <td className="py-3.5 px-4">
                        <button
                          type="button"
                          onClick={() => onToggleActive(workflow.id, workflow.is_active)}
                          className="flex items-center gap-1.5 text-xs font-medium transition-colors"
                        >
                          {workflow.is_active ? (
                            <>
                              <ToggleRight className="w-5 h-5 text-emerald-500" />
                              <span className="text-emerald-700 dark:text-emerald-400">Active</span>
                            </>
                          ) : (
                            <>
                              <ToggleLeft className="w-5 h-5 text-slate-400" />
                              <span className="text-slate-500 dark:text-slate-400">Inactive</span>
                            </>
                          )}
                        </button>
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1.5 text-xs text-slate-700 dark:text-slate-300">
                          <span className="font-semibold">{workflow.execution_count}</span>
                          <span className="text-slate-400">({workflow.success_count} ok)</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            type="button"
                            onClick={() => onExecute(workflow.id)}
                            disabled={isExecuting}
                            title="Execute Workflow Now"
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-950/60 rounded-md hover:bg-indigo-100 dark:hover:bg-indigo-900/60 transition-colors disabled:opacity-50"
                          >
                            <Play className={`w-3.5 h-3.5 ${isExecuting ? 'animate-pulse' : ''}`} />
                            <span>Run</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => onDelete(workflow.id)}
                            title="Delete Workflow"
                            className="p-1 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 rounded transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>

                    {/* Expanded Steps View */}
                    {isExpanded && (
                      <tr className="bg-slate-50/40 dark:bg-slate-900/40">
                        <td colSpan={7} className="px-8 py-3.5">
                          <div className="space-y-2">
                            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                              Execution Pipeline DAG ({workflow.steps?.length ?? 0} Steps)
                            </span>
                            <div className="flex flex-wrap items-center gap-2 pt-1">
                              {workflow.steps?.map((step, idx) => (
                                <React.Fragment key={step.id || idx}>
                                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs shadow-xs">
                                    <span className="w-4 h-4 rounded-full bg-indigo-100 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 flex items-center justify-center font-bold text-[10px]">
                                      {step.step_order}
                                    </span>
                                    <span className="font-medium text-slate-800 dark:text-slate-200">
                                      {step.name}
                                    </span>
                                    <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400 px-1 rounded bg-slate-100 dark:bg-slate-750">
                                      {step.action_type}
                                    </span>
                                  </div>
                                  {idx < (workflow.steps?.length ?? 0) - 1 && (
                                    <span className="text-slate-400 text-xs font-bold">→</span>
                                  )}
                                </React.Fragment>
                              ))}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
