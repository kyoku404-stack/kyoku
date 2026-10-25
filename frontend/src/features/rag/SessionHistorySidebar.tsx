/**
 * KEEP Enterprise Platform — SessionHistorySidebar Component (Phase 2.2).
 *
 * Multi-turn conversational session history drawer/sidebar with session
 * switching, search filtering, message counters, and new conversation triggers.
 *
 * Specification: devdocs/p2/p2.2.txt Chapter 12 & docs/api/api-contract.md Section 9
 * Author: Member 3 (Frontend Lead)
 */

import React, { useState } from 'react';
import { Plus, MessageSquare, Search, Clock, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { RAGChatSessionItem } from '@/types/rag';

interface SessionHistorySidebarProps {
  sessions: RAGChatSessionItem[];
  activeSessionId: string | null;
  onSelectSession: (session: RAGChatSessionItem) => void;
  onNewSession: () => void;
  isOpen?: boolean;
}

export const SessionHistorySidebar: React.FC<SessionHistorySidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  isOpen = true,
}) => {
  const [filterQuery, setFilterQuery] = useState('');

  const filteredSessions = sessions.filter((s) =>
    (s.title || 'Conversation').toLowerCase().includes(filterQuery.toLowerCase())
  );

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return '';
    }
  };

  if (!isOpen) return null;

  return (
    <aside
      className="flex flex-col w-72 border-r border-border bg-card/60 backdrop-blur-sm h-full shrink-0"
      data-testid="rag-session-sidebar"
    >
      {/* Top Header & New Conversation Button */}
      <div className="p-3 border-b border-border space-y-2.5">
        <Button
          variant="primary"
          size="sm"
          onClick={onNewSession}
          className="w-full flex items-center justify-center gap-2 text-xs font-semibold shadow-xs"
          data-testid="btn-new-conversation"
        >
          <Plus className="h-4 w-4" />
          <span>New Conversation</span>
        </Button>

        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            className="w-full h-8 pl-8 pr-3 text-xs rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            data-testid="input-search-sessions"
          />
        </div>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {filteredSessions.length === 0 ? (
          <div className="p-4 text-center text-xs text-muted-foreground">
            {sessions.length === 0
              ? 'No conversations yet. Start a new query!'
              : 'No matching sessions found.'}
          </div>
        ) : (
          filteredSessions.map((sess) => {
            const isActive = sess.session_id === activeSessionId;
            return (
              <button
                key={sess.session_id}
                type="button"
                onClick={() => onSelectSession(sess)}
                className={`w-full text-left p-2.5 rounded-lg text-xs transition-all flex items-center justify-between group ${
                  isActive
                    ? 'bg-primary/10 border border-primary/30 text-primary font-medium'
                    : 'hover:bg-muted/60 text-foreground/80 hover:text-foreground'
                }`}
                data-testid={`session-item-${sess.session_id}`}
              >
                <div className="flex items-center gap-2 min-w-0 flex-1 pr-2">
                  <MessageSquare
                    className={`h-3.5 w-3.5 shrink-0 ${
                      isActive ? 'text-primary' : 'text-muted-foreground'
                    }`}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-xs font-medium text-foreground">
                      {sess.title || 'Knowledge Consultation'}
                    </p>
                    <div className="flex items-center gap-2 text-[10px] text-muted-foreground mt-0.5">
                      <span className="flex items-center gap-0.5">
                        <Clock className="h-2.5 w-2.5" />
                        {formatDate(sess.updated_at || sess.created_at)}
                      </span>
                      <span>•</span>
                      <span>{sess.message_count} msgs</span>
                    </div>
                  </div>
                </div>

                <ChevronRight
                  className={`h-3.5 w-3.5 text-muted-foreground transition-transform shrink-0 ${
                    isActive ? 'text-primary opacity-100' : 'opacity-0 group-hover:opacity-100'
                  }`}
                />
              </button>
            );
          })
        )}
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-border text-[11px] text-muted-foreground text-center">
        <span>KEEP Enterprise RAG Memory</span>
      </div>
    </aside>
  );
};
