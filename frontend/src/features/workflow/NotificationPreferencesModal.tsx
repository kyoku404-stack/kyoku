/**
 * Phase 3.4 NotificationPreferencesModal Component.
 * Multi-channel matrix editor for routing notifications across In-App, Email, Slack, and Microsoft Teams.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  X,
  Sliders,
} from 'lucide-react';
import type {
  NotificationCategory,
  NotificationPreferenceItem,
  NotificationPreferenceUpdatePayload,
} from '@/types/workflow';

interface NotificationPreferencesModalProps {
  isOpen: boolean;
  onClose: () => void;
  preferences: NotificationPreferenceItem[];
  onUpdatePreference: (payload: NotificationPreferenceUpdatePayload) => Promise<unknown>;
}

const categoryLabels: Record<NotificationCategory, { title: string; desc: string }> = {
  workflow: {
    title: 'Workflow Automation',
    desc: 'Pipeline completions, human approval gates, step retries, and errors.',
  },
  security: {
    title: 'Security & Governance',
    desc: 'Anomalies, unauthorized access, DLP policy violations, and MFA prompts.',
  },
  system: {
    title: 'System & Maintenance',
    desc: 'Scheduled platform downtime, storage quota alerts, and API token expiration.',
  },
  task: {
    title: 'Collaborative Tasks',
    desc: 'Task assignments, meeting summaries, mentions, and shared documents.',
  },
};

export const NotificationPreferencesModal: React.FC<NotificationPreferencesModalProps> = ({
  isOpen,
  onClose,
  preferences,
  onUpdatePreference,
}) => {
  const [updatingCategory, setUpdatingCategory] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleToggle = async (
    category: NotificationCategory,
    channel: 'in_app' | 'email' | 'slack' | 'teams',
    currentVal: boolean
  ) => {
    try {
      setUpdatingCategory(`${category}-${channel}`);
      await onUpdatePreference({
        category,
        [channel]: !currentVal,
      });
    } catch {
      // Error handled by hook
    } finally {
      setUpdatingCategory(null);
    }
  };

  const categories: NotificationCategory[] = ['workflow', 'security', 'system', 'task'];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
      <div className="w-full max-w-2xl bg-white dark:bg-slate-850 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Notification Delivery Preferences
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Configure which channels receive alerts for each category.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Matrix Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 dark:border-slate-800 text-xs font-semibold text-slate-500 dark:text-slate-400">
                <th className="py-2.5 px-3">Alert Category</th>
                <th className="py-2.5 px-3 text-center">In-App</th>
                <th className="py-2.5 px-3 text-center">Email</th>
                <th className="py-2.5 px-3 text-center">Slack</th>
                <th className="py-2.5 px-3 text-center">MS Teams</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {categories.map((cat) => {
                const info = categoryLabels[cat];
                const pref = preferences.find((p) => p.category === cat) || {
                  category: cat,
                  in_app: true,
                  email: cat === 'security',
                  slack: false,
                  teams: false,
                };

                return (
                  <tr key={cat} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="py-3 px-3">
                      <div className="text-xs font-bold text-slate-800 dark:text-slate-200">
                        {info.title}
                      </div>
                      <div className="text-[11px] text-slate-400">{info.desc}</div>
                    </td>

                    {/* In-App */}
                    <td className="py-3 px-3 text-center">
                      <input
                        type="checkbox"
                        checked={pref.in_app}
                        onChange={() => handleToggle(cat, 'in_app', pref.in_app)}
                        disabled={updatingCategory === `${cat}-in_app`}
                        className="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500 cursor-pointer"
                      />
                    </td>

                    {/* Email */}
                    <td className="py-3 px-3 text-center">
                      <input
                        type="checkbox"
                        checked={pref.email}
                        onChange={() => handleToggle(cat, 'email', pref.email)}
                        disabled={updatingCategory === `${cat}-email`}
                        className="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500 cursor-pointer"
                      />
                    </td>

                    {/* Slack */}
                    <td className="py-3 px-3 text-center">
                      <input
                        type="checkbox"
                        checked={pref.slack}
                        onChange={() => handleToggle(cat, 'slack', pref.slack)}
                        disabled={updatingCategory === `${cat}-slack`}
                        className="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500 cursor-pointer"
                      />
                    </td>

                    {/* Teams */}
                    <td className="py-3 px-3 text-center">
                      <input
                        type="checkbox"
                        checked={pref.teams}
                        onChange={() => handleToggle(cat, 'teams', pref.teams)}
                        disabled={updatingCategory === `${cat}-teams`}
                        className="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500 cursor-pointer"
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-4 border-t border-slate-100 dark:border-slate-800">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
