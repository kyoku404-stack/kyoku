import React, { useState } from 'react';
import { Play, Sparkles } from 'lucide-react';
import type { RequiredOutputType, StartResearchRequest } from '@/types/research';

interface ResearchLaunchFormProps {
  isSubmitting: boolean;
  canInvoke: boolean;
  onSubmit: (payload: StartResearchRequest) => Promise<void>;
}

const DEMO_QUESTION =
  'Why did customer complaints increase last quarter and which internal teams were affected?';
const DEMO_SCOPE = 'Internal customer feedback and support records';

export const ResearchLaunchForm: React.FC<ResearchLaunchFormProps> = ({
  isSubmitting,
  canInvoke,
  onSubmit,
}) => {
  const [question, setQuestion] = useState('');
  const [scope, setScope] = useState('');
  const [maxSources, setMaxSources] = useState<number>(12);
  const [requiredOutput, setRequiredOutput] = useState<RequiredOutputType>('detailed_report');
  const [mode, setMode] = useState<'sync' | 'async'>('sync');
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleLoadDemo = () => {
    setQuestion(DEMO_QUESTION);
    setScope(DEMO_SCOPE);
    setRequiredOutput('detailed_report');
    setMaxSources(12);
    setMode('sync');
    setValidationError(null);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const cleanedQuestion = question.trim();
    if (cleanedQuestion.length < 3) {
      setValidationError('Please enter a research question with at least 3 characters.');
      return;
    }
    setValidationError(null);
    await onSubmit({
      question: cleanedQuestion,
      scope: scope.trim() || undefined,
      max_sources: maxSources,
      required_output: requiredOutput,
      mode,
    });
  };

  return (
    <section
      aria-label="Launch Research Investigation"
      className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
            New Research Investigation
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Queries authorized KEEP knowledge sources and produces citation-verified findings.
          </p>
        </div>
        <button
          type="button"
          onClick={handleLoadDemo}
          className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-100 dark:border-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300"
        >
          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
          Load Q4 Complaints Demo
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="research-question"
            className="mb-1 block text-xs font-medium text-slate-700 dark:text-slate-300"
          >
            Research Question
          </label>
          <textarea
            id="research-question"
            rows={2}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. Why did customer complaints increase last quarter and which internal teams were affected?"
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            disabled={!canInvoke || isSubmitting}
          />
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="sm:col-span-2 lg:col-span-1">
            <label
              htmlFor="research-scope"
              className="mb-1 block text-xs font-medium text-slate-700 dark:text-slate-300"
            >
              Scope (Optional)
            </label>
            <input
              id="research-scope"
              type="text"
              value={scope}
              onChange={(e) => setScope(e.target.value)}
              placeholder="Internal support & feedback"
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              disabled={!canInvoke || isSubmitting}
            />
          </div>

          <div>
            <label
              htmlFor="research-output-format"
              className="mb-1 block text-xs font-medium text-slate-700 dark:text-slate-300"
            >
              Output Format
            </label>
            <select
              id="research-output-format"
              value={requiredOutput}
              onChange={(e) => setRequiredOutput(e.target.value as RequiredOutputType)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              disabled={!canInvoke || isSubmitting}
            >
              <option value="detailed_report">Detailed Report</option>
              <option value="comparison">Comparison</option>
              <option value="summary">Executive Summary</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="research-max-sources"
              className="mb-1 block text-xs font-medium text-slate-700 dark:text-slate-300"
            >
              Max Sources (1–30)
            </label>
            <input
              id="research-max-sources"
              type="number"
              min={1}
              max={30}
              value={maxSources}
              onChange={(e) =>
                setMaxSources(Math.max(1, Math.min(30, Number(e.target.value) || 12)))
              }
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              disabled={!canInvoke || isSubmitting}
            />
          </div>

          <div>
            <label
              htmlFor="research-mode"
              className="mb-1 block text-xs font-medium text-slate-700 dark:text-slate-300"
            >
              Execution Mode
            </label>
            <select
              id="research-mode"
              value={mode}
              onChange={(e) => setMode(e.target.value as 'sync' | 'async')}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              disabled={!canInvoke || isSubmitting}
            >
              <option value="sync">Synchronous (Immediate)</option>
              <option value="async">Asynchronous (Background)</option>
            </select>
          </div>
        </div>

        {validationError && (
          <p role="alert" className="text-xs font-medium text-rose-600 dark:text-rose-400">
            {validationError}
          </p>
        )}

        <div className="flex items-center justify-end gap-3">
          {!canInvoke && (
            <span className="text-xs text-amber-600 dark:text-amber-400">
              Read-only access: `agent.invoke` permission required to launch investigations.
            </span>
          )}
          <button
            type="submit"
            disabled={!canInvoke || isSubmitting}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Play className="h-4 w-4" aria-hidden="true" />
            {isSubmitting ? 'Investigating...' : 'Run Investigation'}
          </button>
        </div>
      </form>
    </section>
  );
};
