/**
 * Phase 3.2 CommentBox Component.
 * Input box with @mention detection, optional page/highlight anchors, and keyboard submit.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import { Send, Bookmark, Hash } from 'lucide-react';
import { MentionSuggestions } from './MentionSuggestions';

interface CommentBoxProps {
  placeholder?: string;
  isReply?: boolean;
  onSubmit: (content: string, pageNumber?: number, highlightText?: string) => Promise<unknown>;
}

export const CommentBox: React.FC<CommentBoxProps> = ({
  placeholder = 'Add a comment...',
  isReply = false,
  onSubmit,
}) => {
  const [content, setContent] = useState('');
  const [pageNumber, setPageNumber] = useState<number | ''>('');
  const [highlightText, setHighlightText] = useState('');
  const [showAnchors, setShowAnchors] = useState(false);
  const [loading, setLoading] = useState(false);

  // Mention suggestions state
  const [mentionQuery, setMentionQuery] = useState<string | null>(null);

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setContent(val);

    // Check if user is typing an @mention
    const match = val.match(/@([a-zA-Z0-9_.]*)$/);
    if (match) {
      setMentionQuery(match[1]);
    } else {
      setMentionQuery(null);
    }
  };

  const handleSelectMention = (username: string) => {
    if (mentionQuery !== null) {
      const replaced = content.replace(/@([a-zA-Z0-9_.]*)$/, `@${username} `);
      setContent(replaced);
      setMentionQuery(null);
    }
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!content.trim()) return;

    try {
      setLoading(true);
      await onSubmit(
        content.trim(),
        typeof pageNumber === 'number' ? pageNumber : undefined,
        highlightText.trim() || undefined
      );
      setContent('');
      setPageNumber('');
      setHighlightText('');
      setShowAnchors(false);
    } catch (err: unknown) {
      console.error('Failed to submit comment:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="relative rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm p-3.5 focus-within:ring-2 focus-within:ring-indigo-500/20 focus-within:border-indigo-500 transition-all">
      {/* Mention Auto-Complete Popover */}
      {mentionQuery !== null && (
        <div className="absolute bottom-full left-4 mb-2 z-30">
          <MentionSuggestions
            query={mentionQuery}
            onSelect={handleSelectMention}
            onClose={() => setMentionQuery(null)}
          />
        </div>
      )}

      {/* Anchor controls if expanded */}
      {showAnchors && !isReply && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-3 pb-3 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
            <Hash className="w-3.5 h-3.5 text-slate-400" />
            <input
              type="number"
              placeholder="Page #"
              value={pageNumber}
              onChange={(e) =>
                setPageNumber(e.target.value ? parseInt(e.target.value, 10) : '')
              }
              className="w-full text-xs bg-transparent focus:outline-none text-slate-800 dark:text-slate-200"
            />
          </div>
          <div className="sm:col-span-2 flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
            <Bookmark className="w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Highlight text reference..."
              value={highlightText}
              onChange={(e) => setHighlightText(e.target.value)}
              className="w-full text-xs bg-transparent focus:outline-none text-slate-800 dark:text-slate-200"
            />
          </div>
        </div>
      )}

      {/* Input Textarea */}
      <textarea
        rows={isReply ? 2 : 3}
        placeholder={placeholder}
        value={content}
        onChange={handleTextChange}
        onKeyDown={handleKeyDown}
        className="w-full text-sm bg-transparent text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none resize-none leading-relaxed"
      />

      {/* Footer bar with actions */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800/80">
        <div className="flex items-center gap-2">
          {!isReply && (
            <button
              type="button"
              onClick={() => setShowAnchors(!showAnchors)}
              className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-lg transition-colors ${
                showAnchors
                  ? 'bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400'
                  : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
              }`}
            >
              <Bookmark className="w-3.5 h-3.5" />
              {showAnchors ? 'Hide Anchors' : 'Anchor to Page'}
            </button>
          )}
          <span className="text-[11px] text-slate-400 hidden sm:inline">
            Type <kbd className="font-mono bg-slate-100 dark:bg-slate-800 px-1 rounded">@</kbd> to mention · <kbd className="font-mono bg-slate-100 dark:bg-slate-800 px-1 rounded">Ctrl+Enter</kbd> to send
          </span>
        </div>

        <button
          type="button"
          onClick={() => handleSubmit()}
          disabled={loading || !content.trim()}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 rounded-xl shadow-sm transition-all"
        >
          {loading ? (
            'Sending...'
          ) : (
            <>
              <Send className="w-3.5 h-3.5" />
              {isReply ? 'Reply' : 'Post Comment'}
            </>
          )}
        </button>
      </div>
    </div>
  );
};
