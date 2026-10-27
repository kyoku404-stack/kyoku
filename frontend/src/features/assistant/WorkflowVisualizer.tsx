import React, { useState } from 'react';
import {
  GitCommit,
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  ChevronDown,
  ChevronUp,
  Cpu,
  Layers,
} from 'lucide-react';
import type { TaskExecuteResponseData, TaskStepResponse, WorkflowStatus } from '@/types/assistant';

interface WorkflowVisualizerProps {
  workflow: TaskExecuteResponseData | null;
  onOpenApproval?: () => void;
}

export const WorkflowVisualizer: React.FC<WorkflowVisualizerProps> = ({
  workflow,
  onOpenApproval,
}) => {
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  if (!workflow) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 text-center text-slate-400">
        <Layers className="w-8 h-8 mx-auto mb-2 text-slate-600" />
        <h3 className="text-sm font-semibold text-slate-300">No Active Workflow</h3>
        <p className="text-xs text-slate-500 mt-1">
          Instruct the assistant to execute an automated task or plan to visualize its DAG pipeline.
        </p>
      </div>
    );
  }

  const getStatusBadge = (status: WorkflowStatus | TaskStepResponse['status']) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" /> Completed
          </span>
        );
      case 'WAITING_APPROVAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <AlertTriangle className="w-3.5 h-3.5" /> Approval Required
          </span>
        );
      case 'RUNNING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
            <Clock className="w-3.5 h-3.5 animate-spin" /> In Progress
          </span>
        );
      case 'FAILED':
      case 'CANCELLED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <XCircle className="w-3.5 h-3.5" /> {status}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400">
            <Clock className="w-3.5 h-3.5" /> Pending
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 backdrop-blur-md">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
        <div>
          <div className="flex items-center space-x-2">
            <GitCommit className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-bold text-white tracking-wide">{workflow.title}</h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Progress: {workflow.completed_steps} of {workflow.total_steps} steps finished
          </p>
        </div>
        <div>{getStatusBadge(workflow.status)}</div>
      </div>

      {workflow.pending_approval && (
        <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
            <span className="text-xs text-amber-200">
              Action requires human approval: <strong>{workflow.pending_approval.action_type}</strong>
            </span>
          </div>
          {onOpenApproval && (
            <button
              onClick={onOpenApproval}
              className="px-3 py-1 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs rounded-md transition-colors"
            >
              Review Action
            </button>
          )}
        </div>
      )}

      {/* DAG Step Pipeline */}
      <div className="space-y-3">
        {workflow.steps.map((step) => {
          const isExpanded = expandedStep === step.step_number;
          return (
            <div
              key={step.step_number}
              className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-3 transition-colors hover:border-slate-700"
            >
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setExpandedStep(isExpanded ? null : step.step_number)}
              >
                <div className="flex items-center space-x-3">
                  <div className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-300">
                    {step.step_number}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                      <span className="text-xs font-semibold text-slate-200">{step.tool_name}</span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">{step.description}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  {step.latency_ms > 0 && (
                    <span className="text-[10px] text-slate-500">{step.latency_ms.toFixed(1)} ms</span>
                  )}
                  {getStatusBadge(step.status)}
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-slate-500" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-slate-500" />
                  )}
                </div>
              </div>

              {isExpanded && (
                <div className="mt-3 pt-3 border-t border-slate-800/60 text-xs text-slate-300 space-y-2">
                  {step.output && (
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-slate-500">
                        Step Output Data:
                      </span>
                      <pre className="mt-1 p-2 bg-slate-900 rounded border border-slate-800/60 text-[11px] text-emerald-400 overflow-x-auto font-mono">
                        {JSON.stringify(step.output, null, 2)}
                      </pre>
                    </div>
                  )}
                  {step.error && (
                    <div className="p-2 bg-rose-500/10 border border-rose-500/20 rounded text-rose-400 text-xs">
                      {step.error}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {workflow.result_summary && (
        <div className="mt-4 pt-3 border-t border-slate-800 text-xs text-slate-400">
          <strong>Summary:</strong> {workflow.result_summary}
        </div>
      )}
    </div>
  );
};
