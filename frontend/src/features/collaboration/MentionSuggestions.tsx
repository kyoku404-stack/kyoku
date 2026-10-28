/**
 * Phase 3.2 MentionSuggestions Component.
 * Autocomplete popover for @mention queries in discussion comment threads.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import { AtSign } from 'lucide-react';

interface MentionSuggestionsProps {
  query: string;
  onSelect: (username: string) => void;
  onClose: () => void;
}

const COLLABORATOR_SUGGESTIONS = [
  { username: 'john.doe', name: 'John Doe', role: 'Engineering Lead' },
  { username: 'sarah.connor', name: 'Sarah Connor', role: 'Security & Compliance' },
  { username: 'alice.smith', name: 'Alice Smith', role: 'Product Manager' },
  { username: 'bob.architect', name: 'Bob Architect', role: 'AI Systems' },
  { username: 'david.hr', name: 'David Miller', role: 'HR Operations' },
];

export const MentionSuggestions: React.FC<MentionSuggestionsProps> = ({
  query,
  onSelect,
}) => {
  const filtered = COLLABORATOR_SUGGESTIONS.filter(
    (c) =>
      c.username.toLowerCase().includes(query.toLowerCase()) ||
      c.name.toLowerCase().includes(query.toLowerCase())
  );

  if (filtered.length === 0) return null;

  return (
    <div className="w-64 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl overflow-hidden p-1.5 animate-in fade-in zoom-in-95 duration-100">
      <div className="px-2.5 py-1 text-[10px] font-bold tracking-wider text-slate-400 uppercase flex items-center gap-1">
        <AtSign className="w-3 h-3 text-indigo-500" />
        Mention Collaborator
      </div>
      <div className="mt-1 space-y-0.5">
        {filtered.map((c) => (
          <button
            key={c.username}
            type="button"
            onClick={() => onSelect(c.username)}
            className="w-full text-left px-2.5 py-1.5 rounded-xl hover:bg-indigo-50 dark:hover:bg-indigo-950/60 transition-colors flex items-center justify-between group"
          >
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 text-[10px] font-bold flex items-center justify-center">
                {c.name.charAt(0)}
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                  {c.name}
                </div>
                <div className="text-[10px] text-slate-400">@{c.username}</div>
              </div>
            </div>
            <span className="text-[10px] text-slate-400 font-mono hidden group-hover:inline">
              ↵ Select
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};
