/**
 * KEEP Enterprise Platform — Service Deployment Rollout Modal.
 *
 * Phase: 3.6
 * Role: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  ArrowRight,
  GitCommit,
  Loader2,
  Rocket,
  ShieldCheck,
  X,
} from 'lucide-react';
import type { DeploymentStrategy, DeployTriggerRequest } from '@/types/system';

interface DeployServiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialService?: string;
  onDeploy: (request: DeployTriggerRequest) => Promise<unknown>;
  deploying: boolean;
}

export const DeployServiceModal: React.FC<DeployServiceModalProps> = ({
  isOpen,
  onClose,
  initialService = 'keep-backend-api',
  onDeploy,
  deploying,
}) => {
  const [serviceName, setServiceName] = useState(initialService);
  const [version, setVersion] = useState('3.6.1-patch1');
  const [strategy, setStrategy] = useState<DeploymentStrategy>('BLUE_GREEN');
  const [environment, setEnvironment] = useState('production');
  const [autoRollback, setAutoRollback] = useState(true);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onDeploy({
      service_name: serviceName,
      version: version.trim(),
      strategy,
      environment,
      auto_rollback_on_failure: autoRollback,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl animate-in zoom-in-95 duration-150">
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400">
              <Rocket className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">Trigger Service Deployment</h3>
              <p className="text-xs text-slate-400">Declarative zero-downtime release orchestration</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Service Selector */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Target Microservice</label>
            <select
              value={serviceName}
              onChange={(e) => setServiceName(e.target.value)}
              className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="keep-backend-api">keep-backend-api (Core Gateway)</option>
              <option value="keep-frontend">keep-frontend (SPA Bundle)</option>
              <option value="keep-ai-worker">keep-ai-worker (LLM & Context)</option>
              <option value="keep-ingestion-worker">keep-ingestion-worker (Document Parser)</option>
              <option value="keep-embedding-worker">keep-embedding-worker (Vector HNSW)</option>
              <option value="keep-notification-srv">keep-notification-srv (Multi-Channel)</option>
              <option value="all">all (Full Platform Rolling Stack)</option>
            </select>
          </div>

          {/* Version Input */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1.5">
              <GitCommit className="w-3.5 h-3.5 text-indigo-400" />
              Target Version / Image Tag
            </label>
            <input
              type="text"
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              required
              placeholder="e.g. 3.6.1-patch1"
              className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
            />
          </div>

          {/* Strategy Selection */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Rollout Strategy</label>
            <div className="grid grid-cols-3 gap-2">
              {(['BLUE_GREEN', 'ROLLING', 'CANARY'] as DeploymentStrategy[]).map((strat) => (
                <button
                  key={strat}
                  type="button"
                  onClick={() => setStrategy(strat)}
                  className={`px-3 py-2 rounded-xl text-xs font-medium border text-center transition-all ${
                    strategy === strat
                      ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/50 ring-1 ring-indigo-500/30'
                      : 'bg-slate-800/40 text-slate-400 border-slate-700 hover:border-slate-600 hover:text-slate-300'
                  }`}
                >
                  {strat.replace('_', '-')}
                </button>
              ))}
            </div>
          </div>

          {/* Environment */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Deployment Environment</label>
            <select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="production">Production (Live Traffic)</option>
              <option value="staging">Staging (Pre-Flight)</option>
              <option value="dr">Disaster Recovery (Passive Standby)</option>
            </select>
          </div>

          {/* Auto-Rollback Safeguard */}
          <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-3 flex items-start gap-3">
            <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <label className="flex items-center justify-between cursor-pointer">
                <span className="text-xs font-medium text-slate-200">Automated Rollback Safeguard</span>
                <input
                  type="checkbox"
                  checked={autoRollback}
                  onChange={(e) => setAutoRollback(e.target.checked)}
                  className="rounded bg-slate-700 border-slate-600 text-indigo-500 focus:ring-indigo-500 focus:ring-offset-slate-900"
                />
              </label>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Automatically reverts to prior version if error rate exceeds 1.0% within 120s of deployment.
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="pt-2 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={deploying}
              className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={deploying || !version.trim()}
              className="inline-flex items-center gap-2 px-5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl shadow-lg shadow-indigo-600/30 transition-all"
            >
              {deploying ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Dispatching...
                </>
              ) : (
                <>
                  Execute Deployment
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
