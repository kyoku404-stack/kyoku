/**
 * KEEP Enterprise Platform — AI Knowledge Q&A Engine (RAG) Page (Phase 2.2).
 *
 * Integrated enterprise question answering center combining hybrid semantic/sparse
 * retrieval, neural reranking, source citation grounding, conversational memory,
 * and satisfaction feedback.
 *
 * Specification: devdocs/p2/p2.2.txt Chapter 15 & docs/api/api-contract.md Section 9
 * Author: Member 3 (Frontend Lead)
 */

import React, { useState } from 'react';
import { useRAG } from '@/hooks/useRAG';
import {
  RAGMetricsBanner,
  SearchFilterBar,
  CitationDrawer,
  SessionHistorySidebar,
  ChatThread,
} from '@/features/rag';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Sparkles,
  Bot,
  RefreshCw,
  PanelLeftClose,
  PanelLeftOpen,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

export const RAGChatPage: React.FC = () => {
  const {
    sessionId,
    messages,
    sessions,
    lastResponse,
    selectedCitation,
    statistics,
    isLoading,
    isCitationLoading,
    isStatsLoading,
    error,
    hybridDenseWeight,
    setHybridDenseWeight,
    hybridSparseWeight,
    setHybridSparseWeight,
    topK,
    setTopK,
    submitQuery,
    inspectCitation,
    closeCitation,
    submitFeedback,
    startNewSession,
    selectSession,
    loadStatistics,
  } = useRAG({ autoLoadHistory: true });

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [metricsOpen, setMetricsOpen] = useState(false);

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] w-full overflow-hidden bg-background" data-testid="rag-chat-page">
      {/* 1. Page Header & Action Controls */}
      <div className="border-b border-border bg-card/60 backdrop-blur-md px-6 py-3 shrink-0 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen((prev) => !prev)}
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            title={sidebarOpen ? 'Collapse session history' : 'Expand session history'}
            data-testid="btn-toggle-sidebar"
          >
            {sidebarOpen ? (
              <PanelLeftClose className="h-4 w-4" />
            ) : (
              <PanelLeftOpen className="h-4 w-4" />
            )}
          </Button>

          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Bot className="h-5 w-5" />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-foreground">
                AI Knowledge Search &amp; Q&amp;A
              </h1>
              <Badge variant="outline" className="text-[10px] text-primary border-primary/30">
                Phase 2.2 Active
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              Hybrid Dense/Sparse Search (RRF) • Neural Rerank • Source Provenance
            </p>
          </div>
        </div>

        {/* Header Right Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setMetricsOpen((prev) => !prev)}
            className="h-8 text-xs flex items-center gap-1.5"
            data-testid="btn-toggle-metrics"
          >
            <Sparkles className="h-3.5 w-3.5 text-purple-400" />
            <span>Executive Telemetry</span>
            {metricsOpen ? (
              <ChevronUp className="h-3 w-3" />
            ) : (
              <ChevronDown className="h-3 w-3" />
            )}
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={loadStatistics}
            disabled={isStatsLoading}
            className="h-8 text-xs text-muted-foreground hover:text-foreground"
            title="Refresh statistics"
            data-testid="btn-refresh-stats"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isStatsLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* 2. Collapsible Executive KPI Metrics Banner */}
      {metricsOpen && (
        <div className="border-b border-border bg-card/40 p-4 transition-all animate-fadeIn shrink-0">
          <RAGMetricsBanner statistics={statistics} loading={isStatsLoading} />
        </div>
      )}

      {/* 3. Hybrid Search Tuning Bar */}
      <div className="border-b border-border bg-card/20 px-6 py-2 shrink-0">
        <SearchFilterBar
          hybridDenseWeight={hybridDenseWeight}
          setHybridDenseWeight={setHybridDenseWeight}
          hybridSparseWeight={hybridSparseWeight}
          setHybridSparseWeight={setHybridSparseWeight}
          topK={topK}
          setTopK={setTopK}
        />
      </div>

      {/* 4. Main Workspace: Session Sidebar + Chat Thread + Citation Drawer */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left: Conversational Session History */}
        <SessionHistorySidebar
          sessions={sessions}
          activeSessionId={sessionId}
          onSelectSession={selectSession}
          onNewSession={startNewSession}
          isOpen={sidebarOpen}
        />

        {/* Center: Interactive Conversational Exchange */}
        <ChatThread
          messages={messages}
          lastResponse={lastResponse}
          isLoading={isLoading}
          error={error}
          onSubmitQuery={submitQuery}
          onSelectCitation={inspectCitation}
          onSubmitFeedback={submitFeedback}
        />

        {/* Right Slide-over: Deep Provenance Citation Drawer */}
        <CitationDrawer
          citation={selectedCitation}
          isOpen={Boolean(selectedCitation)}
          onClose={closeCitation}
          isLoading={isCitationLoading}
        />
      </div>
    </div>
  );
};
