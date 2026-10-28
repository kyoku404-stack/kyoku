/**
 * Phase 3.2 DocumentDiscussionThread Component.
 * Threaded discussion viewer with nested replies, mention highlights, resolution states,
 * and AI-assisted discussion summarization cards.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  MessageSquare,
  Sparkles,
  CheckCircle2,
  CornerDownRight,
  Clock,
  Check,
  FileText,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import type {
  AIDiscussionSummary,
  CommentCreatePayload,
  CommentReplyPayload,
  DocumentComment,
} from '@/types/collaboration';
import { CommentBox } from './CommentBox';

interface DiscussionThreadProps {
  documentId: string;
  documentTitle: string;
  workspaceId?: string;
  comments: DocumentComment[];
  aiSummary: AIDiscussionSummary | null;
  isSummarizing: boolean;
  onAddComment: (payload: CommentCreatePayload) => Promise<unknown>;
  onReplyComment: (documentId: string, payload: CommentReplyPayload) => Promise<unknown>;
  onResolveComment: (documentId: string, commentId: string) => Promise<unknown>;
  onSummarizeClick: (documentId: string) => void;
}

export const DocumentDiscussionThread: React.FC<DiscussionThreadProps> = ({
  documentId,
  documentTitle,
  workspaceId,
  comments,
  aiSummary,
  isSummarizing,
  onAddComment,
  onReplyComment,
  onResolveComment,
  onSummarizeClick,
}) => {
  const [activeReplyId, setActiveReplyId] = useState<string | null>(null);

  // Helper to render mention handles with styling
  const renderFormattedContent = (content: string) => {
    const parts = content.split(/((?<!\w)@[a-zA-Z0-9_.+-]+)/g);
    return parts.map((part, i) => {
      if (part.startsWith('@')) {
        return (
          <span
            key={i}
            className="inline-flex items-center px-1.5 py-0.2 rounded-md bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 font-semibold text-xs border border-indigo-200/50 dark:border-indigo-800/50 mx-0.5"
          >
            {part}
          </span>
        );
      }
      return part;
    });
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Discussion Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
            <MessageSquare className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Discussion: {documentTitle}
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {comments.length} {comments.length === 1 ? 'thread' : 'threads'} · Real-time team annotations
            </p>
          </div>
        </div>

        <button
          onClick={() => onSummarizeClick(documentId)}
          disabled={isSummarizing || comments.length === 0}
          className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 text-white shadow-sm transition-all"
        >
          <Sparkles className={`w-3.5 h-3.5 ${isSummarizing ? 'animate-spin' : ''}`} />
          {isSummarizing ? 'Synthesizing...' : 'AI Summarize Thread'}
        </button>
      </div>

      {/* AI Discussion Summary Card */}
      {aiSummary && (
        <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-50/70 via-purple-50/30 to-white dark:from-indigo-950/30 dark:via-purple-950/10 dark:to-slate-900 border border-indigo-200/60 dark:border-indigo-800/40 shadow-sm animate-in fade-in duration-200">
          <div className="flex items-center justify-between mb-3">
            <span className="inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300">
              <Sparkles className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
              AI Executive Briefing
            </span>
            <span className="text-[11px] text-slate-400">
              Processed in {aiSummary.processing_time_ms}ms
            </span>
          </div>

          <p className="text-sm font-medium text-slate-800 dark:text-slate-200 leading-relaxed mb-4">
            {aiSummary.executive_summary}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-indigo-100 dark:border-indigo-900/50">
            {/* Key Decisions */}
            {aiSummary.key_decisions.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5 mb-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  Key Decisions ({aiSummary.key_decisions.length})
                </h4>
                <ul className="space-y-1.5">
                  {aiSummary.key_decisions.map((kd, idx) => (
                    <li
                      key={idx}
                      className="text-xs text-slate-600 dark:text-slate-400 bg-white/70 dark:bg-slate-900/60 p-2 rounded-xl border border-slate-100 dark:border-slate-800"
                    >
                      <span className="font-semibold text-slate-800 dark:text-slate-200">
                        {kd.decision}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Action Items */}
            {aiSummary.action_items.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5 mb-2">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
                  Action Items ({aiSummary.action_items.length})
                </h4>
                <ul className="space-y-1.5">
                  {aiSummary.action_items.map((ai, idx) => (
                    <li
                      key={idx}
                      className="text-xs text-slate-600 dark:text-slate-400 bg-white/70 dark:bg-slate-900/60 p-2 rounded-xl border border-slate-100 dark:border-slate-800 flex items-center justify-between"
                    >
                      <span>{ai.action}</span>
                      {ai.assignee && (
                        <span className="text-[10px] font-semibold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950 px-1.5 py-0.5 rounded">
                          @{ai.assignee}
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Unresolved Questions */}
          {aiSummary.unresolved_questions.length > 0 && (
            <div className="mt-4 pt-3 border-t border-indigo-100 dark:border-indigo-900/50">
              <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5 mb-2">
                <HelpCircle className="w-3.5 h-3.5 text-blue-500" />
                Unresolved Questions
              </h4>
              <ul className="space-y-1">
                {aiSummary.unresolved_questions.map((uq, idx) => (
                  <li key={idx} className="text-xs text-slate-600 dark:text-slate-400 italic">
                    "{uq}"
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Suggested Related Resources */}
          {aiSummary.suggested_documents.length > 0 && (
            <div className="mt-4 pt-3 border-t border-indigo-100 dark:border-indigo-900/50">
              <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5 mb-2">
                <FileText className="w-3.5 h-3.5 text-purple-500" />
                Related Knowledge Assets
              </h4>
              <div className="flex flex-wrap gap-2">
                {aiSummary.suggested_documents.map((sd) => (
                  <div
                    key={sd.document_id}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-lg bg-white/80 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300"
                  >
                    <span className="font-semibold">{sd.title}</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300">
                      {Math.round(sd.relevance_score * 100)}% match
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Main Comment Box for posting new thread */}
      <CommentBox
        placeholder="Write a comment or question... Type @ to mention a teammate"
        onSubmit={async (content, pageNum, highlight) => {
          await onAddComment({
            document_id: documentId,
            workspace_id: workspaceId,
            content,
            page_number: pageNum,
            highlight_text: highlight,
          });
        }}
      />

      {/* Comments List */}
      <div className="space-y-4">
        {comments.map((c) => {
          const isResolved = c.status === 'RESOLVED';
          return (
            <div
              key={c.id}
              className={`p-4 rounded-2xl bg-white dark:bg-slate-900 border transition-all ${
                isResolved
                  ? 'border-emerald-200/60 dark:border-emerald-950/50 bg-emerald-50/20'
                  : 'border-slate-200/80 dark:border-slate-800'
              }`}
            >
              {/* Comment Header */}
              <div className="flex items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 font-bold text-xs flex items-center justify-center">
                    {c.author_name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-900 dark:text-white">
                      {c.author_name}
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
                      <Clock className="w-3 h-3" />
                      {new Date(c.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                      {c.page_number && (
                        <span className="px-1.5 py-0.2 bg-slate-100 dark:bg-slate-800 rounded font-mono text-[10px]">
                          p.{c.page_number}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {isResolved ? (
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200/50">
                    <Check className="w-3 h-3" /> Resolved
                  </span>
                ) : (
                  <button
                    onClick={() => onResolveComment(documentId, c.id)}
                    className="text-xs font-semibold text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-1"
                  >
                    <Check className="w-3.5 h-3.5" /> Resolve
                  </button>
                )}
              </div>

              {/* Highlight Quote if applicable */}
              {c.highlight_text && (
                <div className="my-2 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border-l-2 border-indigo-500 text-xs italic text-slate-600 dark:text-slate-400">
                  "{c.highlight_text}"
                </div>
              )}

              {/* Comment Content */}
              <div className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed mb-3">
                {renderFormattedContent(c.content)}
              </div>

              {/* Reply Button */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800/80">
                <button
                  onClick={() =>
                    setActiveReplyId(activeReplyId === c.id ? null : c.id)
                  }
                  className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 transition-colors"
                >
                  <CornerDownRight className="w-3.5 h-3.5" />
                  {activeReplyId === c.id ? 'Cancel Reply' : 'Reply'}
                </button>
                <span className="text-[11px] text-slate-400">
                  {c.replies.length} {c.replies.length === 1 ? 'reply' : 'replies'}
                </span>
              </div>

              {/* Inline Reply Input */}
              {activeReplyId === c.id && (
                <div className="mt-3 pl-4 border-l-2 border-indigo-200 dark:border-indigo-900">
                  <CommentBox
                    isReply
                    placeholder="Write a reply..."
                    onSubmit={async (content) => {
                      await onReplyComment(documentId, {
                        parent_comment_id: c.id,
                        content,
                      });
                      setActiveReplyId(null);
                    }}
                  />
                </div>
              )}

              {/* Nested Replies */}
              {c.replies.length > 0 && (
                <div className="mt-3 space-y-2.5 pl-4 border-l-2 border-slate-100 dark:border-slate-800">
                  {c.replies.map((r) => (
                    <div
                      key={r.id}
                      className="p-3 rounded-xl bg-slate-50/70 dark:bg-slate-950/70 border border-slate-100 dark:border-slate-800/60"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded-full bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 font-bold text-[10px] flex items-center justify-center">
                            {r.author_name.charAt(0).toUpperCase()}
                          </div>
                          <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                            {r.author_name}
                          </span>
                        </div>
                        <span className="text-[10px] text-slate-400">
                          {new Date(r.created_at).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                      <div className="text-xs text-slate-700 dark:text-slate-300 pl-8">
                        {renderFormattedContent(r.content)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
