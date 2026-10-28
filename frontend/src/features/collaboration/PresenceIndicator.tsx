/**
 * Phase 3.2 PresenceIndicator Component.
 * Visual status pill and interactive presence state switcher for collaborators.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { PresenceStatus } from '@/types/collaboration';

interface PresenceIndicatorProps {
  currentStatus: PresenceStatus;
  onStatusChange?: (newStatus: PresenceStatus) => void;
  interactive?: boolean;
}

export const PresenceIndicator: React.FC<PresenceIndicatorProps> = ({
  currentStatus,
  onStatusChange,
  interactive = false,
}) => {
  const [open, setOpen] = useState(false);

  const getStatusColor = (status: PresenceStatus) => {
    switch (status) {
      case 'ONLINE':
        return 'bg-emerald-500 ring-emerald-500/20';
      case 'EDITING':
        return 'bg-blue-500 ring-blue-500/20';
      case 'VIEWING':
        return 'bg-indigo-500 ring-indigo-500/20';
      case 'AWAY':
        return 'bg-amber-400 ring-amber-400/20';
      default:
        return 'bg-slate-400 ring-slate-400/20';
    }
  };

  return (
    <div className="relative inline-block text-left">
      <button
        type="button"
        disabled={!interactive}
        onClick={() => interactive && setOpen(!open)}
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm ${
          interactive ? 'cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800' : 'cursor-default'
        }`}
      >
        <span className={`w-2 h-2 rounded-full ring-2 ${getStatusColor(currentStatus)}`} />
        <span className="capitalize text-slate-700 dark:text-slate-200">
          {currentStatus.toLowerCase()}
        </span>
        {interactive && <ChevronDown className="w-3 h-3 text-slate-400" />}
      </button>

      {open && interactive && (
        <div className="absolute right-0 mt-1 w-36 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-lg z-30 p-1">
          {Object.values(PresenceStatus).map((s) => (
            <button
              key={s}
              onClick={() => {
                onStatusChange?.(s);
                setOpen(false);
              }}
              className="w-full text-left px-2.5 py-1.5 text-xs font-medium rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center gap-2"
            >
              <span className={`w-2 h-2 rounded-full ${getStatusColor(s)}`} />
              <span className="capitalize">{s.toLowerCase()}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
