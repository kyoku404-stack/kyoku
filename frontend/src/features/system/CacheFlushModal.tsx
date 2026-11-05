/**
 * KEEP Enterprise Platform — Redis Cache Flush & Administration Modal.
 *
 * Phase: 3.6
 * Role: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckSquare,
  Flame,
  Loader2,
  Square,
  X,
} from 'lucide-react';
import type { CacheFlushRequest } from '@/types/system';

interface CacheFlushModalProps {
  isOpen: boolean;
  onClose: () => void;
  onFlush: (request: CacheFlushRequest) => Promise<unknown>;
  flushing: boolean;
}

export const CacheFlushModal: React.FC<CacheFlushModalProps> = ({
  isOpen,
  onClose,
  onFlush,
  flushing,
}) => {
  const [selectedNamespaces, setSelectedNamespaces] = useState<string[]>([
    'ai_response',
    'vector_query',
    'dashboard',
  ]);
  const [flushAll, setFlushAll] = useState(false);

  if (!isOpen) return null;

  const namespaces = [
    { id: 'ai_response', label: 'AI Response Cache', prefix: 'keep:ai:resp:', desc: 'Cached LLM prompt completions and synthesis' },
    { id: 'vector_query', label: 'Vector Query Cache', prefix: 'keep:vector:q:', desc: 'Semantic search embeddings and top-k results' },
    { id: 'dashboard', label: 'Dashboard & KPI Cache', prefix: 'keep:dashboard:', desc: 'Aggregated analytics and operational summaries' },
    { id: 'session', label: 'Web Session Cache', prefix: 'keep:session:', desc: 'Active browser session states (forces re-auth)' },
    { id: 'rate_limit', label: 'Rate Limiting Windows', prefix: 'keep:rate_limit:', desc: 'Sliding window request counters' },
  ];

  const toggleNamespace = (id: string) => {
    if (selectedNamespaces.includes(id)) {
      setSelectedNamespaces(selectedNamespaces.filter((ns) => ns !== id));
    } else {
      setSelectedNamespaces([...selectedNamespaces, id]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onFlush({
      namespaces: flushAll ? [] : selectedNamespaces,
      flush_all: flushAll,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl animate-in zoom-in-95 duration-150">
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-rose-500/10 rounded-lg text-rose-400">
              <Flame className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">Flush Redis Cache</h3>
              <p className="text-xs text-slate-400">Selective namespace eviction & memory reclamation</p>
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
          <div className="space-y-2.5">
            <label className="block text-xs font-medium text-slate-300">Select Cache Namespaces</label>
            {namespaces.map((ns) => {
              const checked = selectedNamespaces.includes(ns.id) && !flushAll;
              return (
                <div
                  key={ns.id}
                  onClick={() => !flushAll && toggleNamespace(ns.id)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer flex items-start gap-3 ${
                    flushAll
                      ? 'opacity-40 pointer-events-none border-slate-800 bg-slate-900/40'
                      : checked
                      ? 'bg-rose-500/10 border-rose-500/30'
                      : 'bg-slate-800/40 border-slate-700/60 hover:border-slate-600'
                  }`}
                >
                  <div className="mt-0.5 text-rose-400">
                    {checked ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4 text-slate-500" />}
                  </div>
                  <div className="flex-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-white">{ns.label}</span>
                      <span className="font-mono text-[10px] text-slate-500">{ns.prefix}</span>
                    </div>
                    <p className="text-slate-400 mt-0.5 text-[11px]">{ns.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Flush All Toggle */}
          <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-3 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <label className="flex items-center justify-between cursor-pointer">
                <span className="text-xs font-semibold text-white">Flush Entire Cluster (Flush All)</span>
                <input
                  type="checkbox"
                  checked={flushAll}
                  onChange={(e) => setFlushAll(e.target.checked)}
                  className="rounded bg-slate-700 border-slate-600 text-rose-500 focus:ring-rose-500 focus:ring-offset-slate-900"
                />
              </label>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Clears all Redis keys across all partitions. Active user sessions will be invalidated.
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="pt-2 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={flushing}
              className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={flushing || (!flushAll && selectedNamespaces.length === 0)}
              className="inline-flex items-center gap-2 px-5 py-2 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl shadow-lg shadow-rose-600/30 transition-all"
            >
              {flushing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Purging...
                </>
              ) : (
                <>
                  <Flame className="w-3.5 h-3.5" />
                  Flush Cache
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
