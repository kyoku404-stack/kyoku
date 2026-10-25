/**
 * Phase 2.2 RAG Engine & Semantic Search Custom React Hook.
 * Manages conversational state, grounded question answering, citations,
 * session history, feedback, and telemetry metrics.
 *
 * Specification: docs/api/api-contract.md Section 9 & devdocs/p2/p2.2.txt
 * Author: Member 3 (Frontend Lead)
 */

import { useState, useCallback, useEffect } from 'react';
import { ragService } from '@/services/ragService';
import type {
  RAGQueryRequest,
  RAGQueryResponse,
  RAGCitation,
  RAGCitationDetail,
  RAGChatSessionItem,
  RAGChatMessageItem,
  RAGStatistics,
} from '@/types/rag';

export interface UseRAGOptions {
  initialSessionId?: string | null;
  autoLoadHistory?: boolean;
}

export function useRAG(options: UseRAGOptions = {}) {
  const [sessionId, setSessionId] = useState<string | null>(options.initialSessionId || null);
  const [messages, setMessages] = useState<RAGChatMessageItem[]>([]);
  const [sessions, setSessions] = useState<RAGChatSessionItem[]>([]);
  const [lastResponse, setLastResponse] = useState<RAGQueryResponse | null>(null);
  const [selectedCitation, setSelectedCitation] = useState<RAGCitationDetail | null>(null);
  const [statistics, setStatistics] = useState<RAGStatistics | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isCitationLoading, setIsCitationLoading] = useState<boolean>(false);
  const [isStatsLoading, setIsStatsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Search parameters state
  const [hybridDenseWeight, setHybridDenseWeight] = useState<number>(0.65);
  const [hybridSparseWeight, setHybridSparseWeight] = useState<number>(0.35);
  const [topK, setTopK] = useState<number>(5);

  /**
   * Load conversational session history.
   */
  const loadHistory = useCallback(async (targetSessionId?: string) => {
    try {
      const response = await ragService.getHistory(targetSessionId);
      if (response.success && response.data) {
        setSessions(response.data.sessions || []);
        if (targetSessionId) {
          const activeSess = response.data.sessions.find((s) => s.session_id === targetSessionId);
          if (activeSess) {
            setMessages(activeSess.messages || []);
          }
        }
      }
    } catch (err: unknown) {
      console.error('Failed to load RAG conversation history:', err);
    }
  }, []);

  /**
   * Fetch aggregate RAG statistics.
   */
  const loadStatistics = useCallback(async () => {
    setIsStatsLoading(true);
    try {
      const response = await ragService.getStatistics();
      if (response.success && response.data) {
        setStatistics(response.data);
      }
    } catch (err: unknown) {
      console.error('Failed to load RAG statistics:', err);
    } finally {
      setIsStatsLoading(false);
    }
  }, []);

  /**
   * Submit natural language question for grounded RAG answer synthesis.
   */
  const submitQuery = useCallback(
    async (queryText: string) => {
      if (!queryText.trim() || isLoading) return;

      const trimmed = queryText.trim();
      const tempUserMsg: RAGChatMessageItem = {
        message_id: `temp-${Date.now()}`,
        role: 'user',
        content: trimmed,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, tempUserMsg]);
      setIsLoading(true);
      setError(null);

      try {
        const payload: RAGQueryRequest = {
          query: trimmed,
          session_id: sessionId,
          hybrid_dense_weight: hybridDenseWeight,
          hybrid_sparse_weight: hybridSparseWeight,
          top_k: topK,
          stream: false,
        };

        const res = await ragService.queryRAG(payload);
        if (res.success && res.data) {
          const respData = res.data;
          setLastResponse(respData);

          if (respData.session_id && respData.session_id !== sessionId) {
            setSessionId(respData.session_id);
          }

          const assistantMsg: RAGChatMessageItem = {
            message_id: `resp-${Date.now()}`,
            role: 'assistant',
            content: respData.answer,
            citations_json: JSON.stringify(respData.citations),
            created_at: new Date().toISOString(),
          };

          setMessages((prev) => [...prev, assistantMsg]);
        } else {
          setError(res.message || 'Failed to synthesize answer.');
        }
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'An error occurred during query processing.';
        setError(message);
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, hybridDenseWeight, hybridSparseWeight, topK, isLoading]
  );

  /**
   * Inspect detailed source citation chunk.
   */
  const inspectCitation = useCallback(async (citation: RAGCitation) => {
    setIsCitationLoading(true);
    try {
      const res = await ragService.getCitationDetail(citation.chunk_id);
      if (res.success && res.data) {
        setSelectedCitation(res.data);
      } else {
        // Fallback to citation summary if full detail cannot be fetched
        setSelectedCitation({
          citation_id: citation.citation_id,
          chunk_id: citation.chunk_id,
          document_id: citation.document_id,
          document_title: citation.document_title,
          document_version_id: citation.document_version_id,
          chunk_index: 0,
          page_number: citation.page_number,
          section: citation.section,
          full_content: citation.excerpt,
        });
      }
    } catch {
      setSelectedCitation({
        citation_id: citation.citation_id,
        chunk_id: citation.chunk_id,
        document_id: citation.document_id,
        document_title: citation.document_title,
        document_version_id: citation.document_version_id,
        chunk_index: 0,
        page_number: citation.page_number,
        section: citation.section,
        full_content: citation.excerpt,
      });
    } finally {
      setIsCitationLoading(false);
    }
  }, []);

  /**
   * Submit answer satisfaction feedback.
   */
  const submitFeedback = useCallback(
    async (queryId: string, isHelpful: boolean, rating?: number, comment?: string) => {
      try {
        const res = await ragService.submitFeedback({
          query_id: queryId,
          is_helpful: isHelpful,
          rating,
          comment,
        });
        return res.success;
      } catch (err) {
        console.error('Failed to submit feedback:', err);
        return false;
      }
    },
    []
  );

  /**
   * Start a new chat session.
   */
  const startNewSession = useCallback(() => {
    setSessionId(null);
    setMessages([]);
    setLastResponse(null);
    setSelectedCitation(null);
    setError(null);
  }, []);

  /**
   * Select an existing chat session.
   */
  const selectSession = useCallback((sess: RAGChatSessionItem) => {
    setSessionId(sess.session_id);
    setMessages(sess.messages || []);
    setLastResponse(null);
    setSelectedCitation(null);
    setError(null);
  }, []);

  useEffect(() => {
    if (options.autoLoadHistory !== false) {
      loadHistory(sessionId || undefined);
      loadStatistics();
    }
  }, [loadHistory, loadStatistics, sessionId, options.autoLoadHistory]);

  return {
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
    closeCitation: () => setSelectedCitation(null),
    submitFeedback,
    startNewSession,
    selectSession,
    loadHistory,
    loadStatistics,
  };
}
