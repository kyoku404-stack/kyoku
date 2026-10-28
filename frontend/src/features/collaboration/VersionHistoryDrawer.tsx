/**
 * Phase 3.2 VersionHistoryDrawer Component.
 * Slide-over drawer inspecting document historical versions with rollback actions.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  X,
  History,
  RotateCcw,
  Clock,
  Plus,
  GitCommit,
} from 'lucide-react';
import type {
  CollaborationVersionItem,
  VersionCreatePayload,
  VersionRollbackPayload,
} from '@/types/collaboration';

interface VersionHistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: string;
  documentTitle: string;
  versions: CollaborationVersionItem[];
  onCreateVersion: (payload: VersionCreatePayload) => Promise<unknown>;
  onRollback: (payload: VersionRollbackPayload) => Promise<unknown>;
}

export const VersionHistoryDrawer: React.FC<VersionHistoryDrawerProps> = ({
  isOpen,
  onClose,
  documentId,
  documentTitle,
  versions,
  onCreateVersion,
  onRollback,
}) => {
  const [showCreate, setShowCreate] = useState(false);
  const [changeSummary, setChangeSummary] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!changeSummary.trim()) return;

    try {
      setLoading(true);
      await onCreateVersion({
        document_id: documentId,
        change_summary: changeSummary.trim(),
        approval_status: 'APPROVED',
      });
      setChangeSummary('');
      setShowCreate(false);
    } catch (err: unknown) {
      console.error('Failed to create version checkpoint:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async (targetVersion: number) => {
    if (!window.confirm(`Are you sure you want to revert to Version ${targetVersion}?`)) {
      return;
    }
    try {
      setLoading(true);
      await onRollback({
        document_id: documentId,
        target_version_number: targetVersion,
      });
    } catch (err: unknown) {
      console.error('Failed to rollback version:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col">
          {/* Header */}
          <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
                <History className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Version History
                </h3>
                <p className="text-xs text-slate-400 line-clamp-1">{documentTitle}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Action Toolbar */}
          <div className="p-4 bg-slate-50/50 dark:bg-slate-950/50 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">
              {versions.length} {versions.length === 1 ? 'version' : 'versions'} recorded
            </span>
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-sm transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              Checkpoint
            </button>
          </div>

          {/* Create Checkpoint Form */}
          {showCreate && (
            <form onSubmit={handleCreateSubmit} className="p-4 bg-indigo-50/40 dark:bg-indigo-950/20 border-b border-indigo-100 dark:border-indigo-900/50">
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                Change Summary *
              </label>
              <input
                type="text"
                required
                placeholder="What changes were introduced in this revision?"
                value={changeSummary}
                onChange={(e) => setChangeSummary(e.target.value)}
                className="w-full px-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 mb-2"
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="px-2.5 py-1 text-xs text-slate-500 hover:text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !changeSummary.trim()}
                  className="px-3 py-1 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-lg shadow-sm"
                >
                  {loading ? 'Saving...' : 'Save Version'}
                </button>
              </div>
            </form>
          )}

          {/* Versions Timeline List */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {versions.length === 0 ? (
              <div className="text-center py-12 text-slate-400 text-xs">
                No version checkpoints recorded yet.
              </div>
            ) : (
              versions.map((v, idx) => {
                const isLatest = idx === 0;
                return (
                  <div
                    key={v.version_id}
                    className={`relative p-4 rounded-2xl border transition-all ${
                      isLatest
                        ? 'border-indigo-500/60 dark:border-indigo-500/50 bg-indigo-50/20 dark:bg-indigo-950/10'
                        : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300">
                          <GitCommit className="w-3 h-3" />
                          v{v.version_number}
                        </span>
                        {isLatest && (
                          <span className="text-[10px] font-semibold px-2 py-0.2 rounded-full bg-emerald-50 dark:bg-emerald-950 text-emerald-600 border border-emerald-200/50">
                            Current
                          </span>
                        )}
                      </div>

                      <span className="text-[10px] text-slate-400 flex items-center gap-1 font-mono">
                        <Clock className="w-3 h-3" />
                        {new Date(v.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    <p className="text-xs text-slate-700 dark:text-slate-300 font-medium leading-relaxed mb-3">
                      {v.change_summary}
                    </p>

                    <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                      <span>Edited by {v.editor_name}</span>
                      {!isLatest && (
                        <button
                          onClick={() => handleRollback(v.version_number)}
                          disabled={loading}
                          className="inline-flex items-center gap-1 font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 transition-colors"
                        >
                          <RotateCcw className="w-3 h-3" />
                          Rollback to this
                        </button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
