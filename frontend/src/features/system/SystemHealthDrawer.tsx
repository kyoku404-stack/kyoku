/**
 * KEEP Enterprise Platform — Subsystem Diagnostics Slide-Over Drawer.
 *
 * Phase: 3.6
 * Role: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import {
  Activity,
  CheckCircle2,
  Clock,
  Database,
  HardDrive,
  Layers,
  Sparkles,
  X,
} from 'lucide-react';
import type { SystemHealthData } from '@/types/system';

interface SystemHealthDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  health: SystemHealthData | null;
}

export const SystemHealthDrawer: React.FC<SystemHealthDrawerProps> = ({
  isOpen,
  onClose,
  health,
}) => {
  if (!isOpen) return null;

  const subsystems = health?.subsystems ?? {};

  const getSubsystemIcon = (key: string) => {
    switch (key) {
      case 'database':
        return <Database className="w-5 h-5 text-indigo-400" />;
      case 'redis':
        return <Layers className="w-5 h-5 text-rose-400" />;
      case 'vector_database':
        return <Activity className="w-5 h-5 text-emerald-400" />;
      case 'storage':
        return <HardDrive className="w-5 h-5 text-blue-400" />;
      case 'ai_workers':
        return <Sparkles className="w-5 h-5 text-amber-400" />;
      default:
        return <Database className="w-5 h-5 text-slate-400" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/70 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-lg bg-slate-900 border-l border-slate-800 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
        {/* Drawer Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">Subsystem Diagnostics</h3>
              <p className="text-xs text-slate-400">
                Composite Rating: {Math.round((health?.overall_score ?? 1.0) * 100)}% | Platform {health?.status}
              </p>
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

        {/* Drawer Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {Object.entries(subsystems).map(([key, sub]) => {
            const probe = sub as {
              status: string;
              latency_ms?: number;
              [k: string]: unknown;
            };
            const isHealthy = probe.status === 'HEALTHY';

            return (
              <div
                key={key}
                className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4 hover:border-slate-600 transition-all"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    {getSubsystemIcon(key)}
                    <span className="text-sm font-semibold text-white capitalize">
                      {key.replace('_', ' ')}
                    </span>
                  </div>
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      isHealthy
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}
                  >
                    <CheckCircle2 className="w-3 h-3" />
                    {probe.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-slate-900/40 p-2 rounded-lg border border-slate-800/60">
                    <span className="text-slate-400 block mb-0.5">Probe Latency</span>
                    <span className="text-slate-200 font-mono font-medium">
                      {probe.latency_ms ?? 0} ms
                    </span>
                  </div>

                  {Object.entries(probe)
                    .filter(([k]) => !['status', 'latency_ms'].includes(k))
                    .map(([attrKey, attrVal]) => (
                      <div
                        key={attrKey}
                        className="bg-slate-900/40 p-2 rounded-lg border border-slate-800/60 truncate"
                      >
                        <span className="text-slate-400 block mb-0.5 capitalize">
                          {attrKey.replace('_', ' ')}
                        </span>
                        <span className="text-slate-200 font-medium truncate block">
                          {String(attrVal)}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Drawer Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/90 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span>Uptime: {Math.round((health?.uptime_seconds ?? 0) / 3600)} hours</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors font-medium text-xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

