import { useState, useRef, useCallback } from 'react';
import { chatService } from '@/services/chatService';
import type { ChatCitation } from '@/types/chat';

interface UseChatStreamReturn {
  answer: string;
  citations: ChatCitation[];
  isStreaming: boolean;
  error: string | null;
  totalTokens: number;
  sendStreamQuery: (query: string, conversationId?: string) => void;
  abortStream: () => void;
  resetStream: () => void;
}

export function useChatStream(): UseChatStreamReturn {
  const [answer, setAnswer] = useState<string>('');
  const [citations, setCitations] = useState<ChatCitation[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [totalTokens, setTotalTokens] = useState<number>(0);

  const abortRef = useRef<(() => void) | null>(null);

  const abortStream = useCallback(() => {
    if (abortRef.current) {
      abortRef.current();
      abortRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const resetStream = useCallback(() => {
    abortStream();
    setAnswer('');
    setCitations([]);
    setError(null);
    setTotalTokens(0);
  }, [abortStream]);

  const sendStreamQuery = useCallback(
    (query: string, conversationId?: string) => {
      // Abort any ongoing stream
      abortStream();

      setAnswer('');
      setCitations([]);
      setError(null);
      setIsStreaming(true);

      const cancel = chatService.streamChat(
        { query, conversation_id: conversationId },
        {
          onToken: (token) => {
            setAnswer((prev) => prev + token);
          },
          onCitation: (incomingCitations) => {
            setCitations((prev) => [...prev, ...incomingCitations]);
          },
          onDone: (data) => {
            setTotalTokens(data.total_tokens);
            setIsStreaming(false);
            abortRef.current = null;
          },
          onError: (err) => {
            setError(err.message || 'Stream processing failed.');
            setIsStreaming(false);
            abortRef.current = null;
          },
        }
      );

      abortRef.current = cancel;
    },
    [abortStream]
  );

  return {
    answer,
    citations,
    isStreaming,
    error,
    totalTokens,
    sendStreamQuery,
    abortStream,
    resetStream,
  };
}

export default useChatStream;
