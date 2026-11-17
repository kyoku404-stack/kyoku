/**
 * KEEP Enterprise Platform — Phase 4.2 Execute Agent Modal.
 *
 * Allows authorized users (`agent.invoke`) to submit sync or async executions against
 * registered KEEP agents with optional timeout bounds and Idempotency-Key deduplication.
 */

import React, { useEffect, useState } from 'react';
import { Play, X } from 'lucide-react';
import type {
  ExecutionMode,
  RegisteredAgentItem,
  SubmitExecutionRequest,
} from '@/types/agentRuntime';

interface ExecuteAgentModalProps {
  isOpen: boolean;
  agents: RegisteredAgentItem[];
  initialAgentId?: string;
  submitting?: boolean;
  onClose: () => void;
  onSubmit: (
    agentId: string,
    payload: SubmitExecutionRequest,
    idempotencyKey?: string
  ) => Promise<unknown>;
}

export const ExecuteAgentModal: React.FC<ExecuteAgentModalProps> = ({
  isOpen,
  agents,
  initialAgentId,
  submitting = false,
  onClose,
  onSubmit,
}) => {
  const [agentId, setAgentId] = useState<string>(initialAgentId || '');
  const [goal, setGoal] = useState<string>('');
  const [inputJson, setInputJson] = useState<string>('{"topic": "Q4 compliance review"}');
  const [mode, setMode] = useState<ExecutionMode>('sync');
  const [timeoutSeconds, setTimeoutSeconds] = useState<string>('30');
  const [idempotencyKey, setIdempotencyKey] = useState<string>('');
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      if (initialAgentId) {
        setAgentId(initialAgentId);
      } else if (agents.length > 0 && !agentId) {
        setAgentId(agents[0].agent_id);
      }
      setValidationError(null);
    }
  }, [isOpen, initialAgentId, agents, agentId]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    const selectedAgent = agentId || agents[0]?.agent_id;
    if (!selectedAgent) {
      setValidationError('Please select a registered agent to execute.');
      return;
    }

    if (!goal.trim()) {
      setValidationError('Execution goal is required.');
      return;
    }

    let parsedInput: Record<string, unknown> = {};
    if (inputJson.trim()) {
      try {
        const parsed = JSON.parse(inputJson);
        if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
          setValidationError('Structured input must be a valid JSON object.');
          return;
        }
        parsedInput = parsed as Record<string, unknown>;
      } catch {
        setValidationError('Structured input must be valid JSON.');
        return;
      }
    }

    const parsedTimeout = timeoutSeconds.trim() ? Number(timeoutSeconds) : undefined;
    if (parsedTimeout !== undefined && (Number.isNaN(parsedTimeout) || parsedTimeout <= 0)) {
      setValidationError('Timeout seconds must be a positive number.');
      return;
    }

    const payload: SubmitExecutionRequest = {
      goal: goal.trim(),
      input: parsedInput,
      mode,
      ...(parsedTimeout !== undefined ? { timeout_seconds: parsedTimeout } : {}),
    };

    const result = await onSubmit(selectedAgent, payload, idempotencyKey.trim() || undefined);
    if (result) {
      setGoal('');
      setIdempotencyKey('');
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="execute-agent-modal-title"
    >
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl shadow-xl w-full max-w-lg overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2
              id="execute-agent-modal-title"
              className="text-lg font-bold text-gray-900 dark:text-white"
            >
              Submit Agent Execution
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Trusted identity & tenant context are derived automatically from your KEEP session.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close Modal"
            className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleFormSubmit} className="p-6 space-y-4">
          {validationError && (
            <div
              role="alert"
              className="p-3 rounded-lg bg-rose-50 dark:bg-rose-900/30 border border-rose-200 dark:border-rose-700 text-xs text-rose-700 dark:text-rose-200"
            >
              {validationError}
            </div>
          )}

          <div>
            <label
              htmlFor="agent-select"
              className="block text-xs font-semibold uppercase tracking-wider text-gray-600 dark:text-gray-300 mb-1.5"
            >
              Target Agent
            </label>
            <select
              id="agent-select"
              value={agentId}
              onChange={(e) => setAgentId(e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {agents.map((agent) => (
                <option key={agent.agent_id} value={agent.agent_id}>
                  {agent.name} ({agent.agent_id} v{agent.version})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="execution-goal"
              className="block text-xs font-semibold uppercase tracking-wider text-gray-600 dark:text-gray-300 mb-1.5"
            >
              Execution Goal
            </label>
            <input
              id="execution-goal"
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g. Synthesize Q4 enterprise security posture"
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="execution-mode"
                className="block text-xs font-semibold uppercase tracking-wider text-gray-600 dark:text-gray-300 mb-1.5"
              >
                Execution Mode
              </label>
              <select
                id="execution-mode"
                value={mode}
                onChange={(e) => setMode(e.target.value as ExecutionMode)}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="sync">Synchronous (200 OK)</option>
                <option value="async">Asynchronous Background (202 Accepted)</option>
              </select>
            </div>

            <div>
              <label
                htmlFor="execution-timeout"
                className="block text-xs font-semibold uppercase tracking-wider text-gray-600 dark:text-gray-300 mb-1.5"
              >
                Timeout (Seconds)
              </label>
              <input
                id="execution-timeout"
                type="number"
                min={1}
                max={300}
                step="1"
                value={timeoutSeconds}
                onChange={(e) => setTimeoutSeconds(e.target.value)}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="execution-idempotency-key"
              className="block text-xs font-semibold uppercase tracking-wider text-gray-600 dark:text-gray-300 mb-1.5"
            >
              Idempotency Key (Optional)
            </label>
            <input
              id="execution-idempotency-key"
              type="text"
              value={idempotencyKey}
              onChange={(e) => setIdempotencyKey(e.target.value)}
              placeholder="e.g. demo-run-2026-001"
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label
              htmlFor="execution-input-json"
              className="block text-xs font-semibold uppercase tracking-wider text-gray-600 dark:text-gray-300 mb-1.5"
            >
              Structured Input Payload (JSON)
            </label>
            <textarea
              id="execution-input-json"
              rows={3}
              value={inputJson}
              onChange={(e) => setInputJson(e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-xs font-mono text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-2 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              {submitting ? 'Submitting...' : 'Execute Agent'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
