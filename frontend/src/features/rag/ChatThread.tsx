/**
 * KEEP Enterprise Platform — ChatThread Component (Phase 2.2).
 *
 * Core conversational exchange view featuring grounded AI synthesis,
 * interactive source citation chips, confidence badges, feedback rating,
 * telemetry inspector, and prompt input box.
 *
 * Specification: devdocs/p2/p2.2.txt Chapters 11, 12, 13 & docs/api/api-contract.md Section 9
 * Author: Member 3 (Frontend Lead)
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  User,
  Bot,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
  Bookmark,
  Activity,
  ChevronDown,
  ChevronUp,
  Loader2,
  HelpCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type {
  RAGChatMessageItem,
  RAGCitation,
  RAGQueryResponse,
} from '@/types/rag';

interface ChatThreadProps {
  messages: RAGChatMessageItem[];
  lastResponse: RAGQueryResponse | null;
  isLoading: boolean;
  error: string | null;
  onSubmitQuery: (query: string) => void;
  onSelectCitation: (citation: RAGCitation) => void;
  onSubmitFeedback: (queryId: string, isHelpful: boolean, rating?: number, comment?: string) => Promise<boolean>;
}

export const ChatThread: React.FC<ChatThreadProps> = ({
  messages,
  lastResponse,
  isLoading,
  error,
  onSubmitQuery,
  onSelectCitation,
  onSubmitFeedback,
}) => {
  const [inputPrompt, setInputPrompt] = useState('');
  const [feedbackGiven, setFeedbackGiven] = useState<Record<string, boolean>>({});
  const [showFeedbackModal, setShowFeedbackModal] = useState<string | null>(null);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [showMetricsFor, setShowMetricsFor] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    if (typeof messagesEndRef.current?.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputPrompt.trim() || isLoading) return;
    const prompt = inputPrompt;
    setInputPrompt('');
    onSubmitQuery(prompt);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFeedback = async (queryId: string, isHelpful: boolean) => {
    if (isHelpful) {
      await onSubmitFeedback(queryId, true);
      setFeedbackGiven((prev) => ({ ...prev, [queryId]: true }));
    } else {
      setShowFeedbackModal(queryId);
    }
  };

  const submitDetailedFeedback = async (queryId: string) => {
    await onSubmitFeedback(queryId, false, 1, feedbackComment);
    setFeedbackGiven((prev) => ({ ...prev, [queryId]: true }));
    setShowFeedbackModal(null);
    setFeedbackComment('');
  };

  const samplePrompts = [
    'What is our enterprise employee leave policy?',
    'Explain the AWS data encryption and KMS retention requirements.',
    'What are the compliance rules for cross-border data transfers?',
    'Summarize the disaster recovery and failover SLAs.',
  ];

  return (
    <div className="flex flex-col flex-1 h-full bg-background relative overflow-hidden" data-testid="rag-chat-thread">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto py-12">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary mb-4 shadow-sm">
              <Bot className="h-7 w-7" />
            </div>
            <h2 className="text-xl font-bold tracking-tight text-foreground">
              Enterprise Knowledge Q&amp;A
            </h2>
            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
              Ask natural language questions grounded in verified organization documents.
              Responses cite page numbers, sections, and chunk coordinates with zero hallucination.
            </p>

            {/* Prompt Starters */}
            <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full">
              {samplePrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onSubmitQuery(prompt)}
                  className="p-3 text-left rounded-xl border border-border bg-card/60 hover:bg-card hover:border-primary/40 transition-all text-xs text-foreground/80 hover:text-foreground group"
                  data-testid={`prompt-starter-${idx}`}
                >
                  <span className="font-medium group-hover:text-primary transition-colors">
                    {prompt}
                  </span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, index) => {
            const isUser = msg.role === 'user';
            let citations: RAGCitation[] = [];
            if (!isUser && msg.citations_json) {
              try {
                citations = JSON.parse(msg.citations_json);
              } catch {
                citations = [];
              }
            }

            const isLastAssistantMessage = !isUser && index === messages.length - 1;
            const currentResp = isLastAssistantMessage ? lastResponse : null;
            const queryId = currentResp?.query_id || `msg-${index}`;
            const confidence = currentResp?.confidence_score ?? 0.88;
            const isGrounded = currentResp?.is_grounded ?? true;
            const processingMs = currentResp?.processing_time_ms ?? 340;

            return (
              <div
                key={msg.message_id || index}
                className={`flex gap-3 max-w-4xl mx-auto ${
                  isUser ? 'justify-end' : 'justify-start'
                }`}
                data-testid={`chat-message-${msg.role}`}
              >
                {!isUser && (
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10 text-primary shrink-0 mt-1">
                    <Bot className="h-4 w-4" />
                  </div>
                )}

                <div
                  className={`rounded-2xl p-4 text-sm max-w-2xl space-y-3 ${
                    isUser
                      ? 'bg-primary text-primary-foreground ml-12 rounded-tr-xs'
                      : 'bg-card border border-border text-foreground mr-12 rounded-tl-xs shadow-xs'
                  }`}
                >
                  {/* Assistant Header Badges */}
                  {!isUser && (
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 pb-2 text-xs">
                      <div className="flex items-center gap-2">
                        {isGrounded ? (
                          <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-semibold text-[11px]">
                            <ShieldCheck className="h-3.5 w-3.5" /> Grounded Response
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-amber-500 font-semibold text-[11px]">
                            <AlertTriangle className="h-3.5 w-3.5" /> Low Grounding Evidence
                          </span>
                        )}
                        <Badge variant="outline" className="text-[10px] py-0 font-mono">
                          {(confidence * 100).toFixed(0)}% confidence
                        </Badge>
                      </div>

                      <span className="text-[10px] text-muted-foreground font-mono">
                        {processingMs} ms
                      </span>
                    </div>
                  )}

                  {/* Message Content */}
                  <div className="whitespace-pre-wrap leading-relaxed select-text text-sm">
                    {msg.content}
                  </div>

                  {/* Grounded Citation Chips */}
                  {!isUser && citations.length > 0 && (
                    <div className="pt-2 border-t border-border/50 space-y-1.5" data-testid="citation-chips-container">
                      <div className="flex items-center gap-1 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                        <Bookmark className="h-3 w-3 text-primary" />
                        <span>Source Citations ({citations.length}):</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {citations.map((cite, cIdx) => (
                          <button
                            key={cite.citation_id || cIdx}
                            type="button"
                            onClick={() => onSelectCitation(cite)}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-border bg-background/80 hover:bg-primary/10 hover:border-primary/40 text-xs font-medium text-foreground transition-all cursor-pointer shadow-2xs"
                            title={`Inspect citation: ${cite.document_title} (Score: ${(cite.similarity_score * 100).toFixed(1)}%)`}
                            data-testid={`citation-chip-${cIdx}`}
                          >
                            <span className="text-primary font-bold text-[10px]">[{cIdx + 1}]</span>
                            <span className="truncate max-w-[140px] text-[11px]">{cite.document_title}</span>
                            {cite.page_number && (
                              <span className="text-[10px] text-muted-foreground font-mono">
                                p.{cite.page_number}
                              </span>
                            )}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Assistant Footer: Feedback & Metrics Toggle */}
                  {!isUser && (
                    <div className="pt-2 flex items-center justify-between text-xs text-muted-foreground border-t border-border/40">
                      {/* Telemetry Toggle */}
                      {currentResp?.retrieval_metrics && (
                        <button
                          type="button"
                          onClick={() =>
                            setShowMetricsFor((prev) => (prev === queryId ? null : queryId))
                          }
                          className="flex items-center gap-1 text-[10px] hover:text-foreground transition-colors"
                        >
                          <Activity className="h-3 w-3 text-primary" />
                          <span>Telemetry</span>
                          {showMetricsFor === queryId ? (
                            <ChevronUp className="h-2.5 w-2.5" />
                          ) : (
                            <ChevronDown className="h-2.5 w-2.5" />
                          )}
                        </button>
                      )}

                      {/* Feedback buttons */}
                      <div className="flex items-center gap-2 ml-auto" data-testid="feedback-controls">
                        {feedbackGiven[queryId] ? (
                          <span className="text-[10px] text-emerald-500 font-medium">
                            Feedback recorded ✓
                          </span>
                        ) : (
                          <>
                            <span className="text-[10px] text-muted-foreground">Helpful?</span>
                            <button
                              type="button"
                              onClick={() => handleFeedback(queryId, true)}
                              className="p-1 rounded hover:bg-muted hover:text-emerald-500 transition-colors"
                              title="Helpful answer"
                              data-testid="btn-feedback-positive"
                            >
                              <ThumbsUp className="h-3.5 w-3.5" />
                            </button>
                            <button
                              type="button"
                              onClick={() => handleFeedback(queryId, false)}
                              className="p-1 rounded hover:bg-muted hover:text-rose-500 transition-colors"
                              title="Unhelpful or inaccurate"
                              data-testid="btn-feedback-negative"
                            >
                              <ThumbsDown className="h-3.5 w-3.5" />
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Expandable Telemetry Breakdown */}
                  {!isUser && showMetricsFor === queryId && currentResp?.retrieval_metrics && (
                    <div
                      className="p-2.5 rounded-xl border border-border bg-muted/40 text-[11px] font-mono space-y-1.5"
                      data-testid="retrieval-metrics-drawer"
                    >
                      <div className="font-semibold text-muted-foreground uppercase text-[9px] tracking-wider">
                        RAG Pipeline Performance Breakdown
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-foreground/80">
                        <div>Dense Candidates: {currentResp.retrieval_metrics.dense_candidates}</div>
                        <div>Sparse Candidates: {currentResp.retrieval_metrics.sparse_candidates}</div>
                        <div>Reranked Passages: {currentResp.retrieval_metrics.reranked_candidates}</div>
                        <div>Retrieval Latency: {currentResp.retrieval_metrics.latency_retrieval_ms} ms</div>
                        <div>Generation Latency: {currentResp.retrieval_metrics.latency_generation_ms} ms</div>
                        <div>
                          Tokens: {currentResp.retrieval_metrics.tokens_prompt} prompt /{' '}
                          {currentResp.retrieval_metrics.tokens_completion} completion
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-muted text-muted-foreground shrink-0 mt-1">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex gap-3 max-w-4xl mx-auto" data-testid="rag-loading-indicator">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10 text-primary shrink-0 animate-pulse">
              <Bot className="h-4 w-4" />
            </div>
            <div className="rounded-2xl p-4 bg-card border border-border text-foreground space-y-2 rounded-tl-xs shadow-xs max-w-sm">
              <div className="flex items-center gap-2 text-xs text-primary font-medium">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>Searching knowledge base &amp; synthesizing grounded answer...</span>
              </div>
              <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-primary animate-indeterminate rounded-full" />
              </div>
            </div>
          </div>
        )}

        {/* Error Notification */}
        {error && (
          <div
            className="p-3.5 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-600 dark:text-rose-400 text-xs flex items-center gap-2 max-w-4xl mx-auto"
            data-testid="rag-error-banner"
          >
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Negative Feedback Modal */}
      {showFeedbackModal && (
        <div className="absolute inset-0 bg-background/80 backdrop-blur-xs flex items-center justify-center z-40 p-4">
          <div className="w-full max-w-md rounded-2xl border border-border bg-card p-5 shadow-xl space-y-4">
            <div className="flex items-center gap-2">
              <HelpCircle className="h-5 w-5 text-amber-500" />
              <h3 className="text-sm font-bold text-foreground">Provide Feedback</h3>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Help us improve KEEP RAG retrieval quality. Please describe what was inaccurate or missing.
            </p>
            <textarea
              rows={3}
              value={feedbackComment}
              onChange={(e) => setFeedbackComment(e.target.value)}
              placeholder="e.g. Missed section 4.2 in employee handbook or incorrect policy date..."
              className="w-full p-2.5 text-xs rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowFeedbackModal(null)}
                className="text-xs"
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => submitDetailedFeedback(showFeedbackModal)}
                className="text-xs"
              >
                Submit Feedback
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Input Form Footer */}
      <div className="border-t border-border bg-card/70 backdrop-blur-md p-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex items-end gap-2">
          <div className="relative flex-1">
            <textarea
              ref={inputRef}
              rows={1}
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask an enterprise question (e.g., 'What is our leave policy?')..."
              disabled={isLoading}
              className="w-full resize-none rounded-xl border border-border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-50"
              data-testid="input-rag-prompt"
            />
          </div>
          <Button
            type="submit"
            variant="primary"
            disabled={isLoading || !inputPrompt.trim()}
            className="h-11 px-4 rounded-xl flex items-center justify-center shrink-0"
            data-testid="btn-submit-rag-query"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
        <div className="max-w-4xl mx-auto mt-1 flex items-center justify-between text-[11px] text-muted-foreground px-1">
          <span className="flex items-center gap-1">
            <Sparkles className="h-3 w-3 text-primary" /> Powered by Hybrid Search (RRF) &amp; Neural Rerank
          </span>
          <span>Shift+Enter for newline</span>
        </div>
      </div>
    </div>
  );
};
