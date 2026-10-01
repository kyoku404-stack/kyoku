/**
 * KEEP Enterprise Platform — Chat & RAG Service Client.
 * Connects to /api/v1/chat endpoints with synchronous query & SSE streaming.
 */

import { apiClient } from './api';
import { CONFIG } from '@/constants/config';
import type { ApiResponse } from '@/types/api';
import type {
  ChatCitation,
  ChatQueryRequest,
  ChatQueryResponse,
  ChatStreamCallbacks,
  ChatStreamRequest,
} from '@/types/chat';

export const chatService = {
  /**
   * Synchronous RAG question answering query with source citations.
   * POST /api/v1/chat/query
   */
  async queryChat(request: ChatQueryRequest): Promise<ApiResponse<ChatQueryResponse>> {
    const response = await apiClient.post<ApiResponse<ChatQueryResponse>>(
      '/chat/query',
      request
    );
    return response.data;
  },

  /**
   * Real-time Server-Sent Events (SSE) streaming for RAG query tokens and citations.
   * POST /api/v1/chat/stream
   * Returns an abort function to cancel the active stream.
   */
  streamChat(request: ChatStreamRequest, callbacks: ChatStreamCallbacks): () => void {
    const controller = new AbortController();
    const token = localStorage.getItem('keep_auth_token');
    const baseUrl = CONFIG.API_BASE_URL.replace(/\/$/, '');
    const streamUrl = `${baseUrl}/chat/stream`;

    (async () => {
      try {
        const response = await fetch(streamUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'text/event-stream',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify(request),
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`SSE streaming failed with status ${response.status}: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('Response body stream is not readable.');
        }

        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        let streamFinished = false;
        while (!streamFinished) {
          const { done, value } = await reader.read();
          if (done) {
            streamFinished = true;
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const messages = buffer.split('\n\n');
          // Retain incomplete trailing fragment in buffer
          buffer = messages.pop() ?? '';

          for (const message of messages) {
            if (!message.trim()) continue;

            const lines = message.split('\n');
            let eventType = 'message';
            let dataStr = '';

            for (const line of lines) {
              if (line.startsWith('event:')) {
                eventType = line.replace('event:', '').trim();
              } else if (line.startsWith('data:')) {
                dataStr = line.replace('data:', '').trim();
              }
            }

            if (!dataStr) continue;

            try {
              const parsedData = JSON.parse(dataStr);

              switch (eventType) {
                case 'token':
                  callbacks.onToken(parsedData.token || parsedData.content || '');
                  break;
                case 'citation': {
                  const citations: ChatCitation[] = Array.isArray(parsedData)
                    ? parsedData
                    : [parsedData];
                  callbacks.onCitation?.(citations);
                  break;
                }
                case 'done':
                  callbacks.onDone?.({
                    conversation_id: parsedData.conversation_id || request.conversation_id || '',
                    total_tokens: parsedData.total_tokens || 0,
                  });
                  break;
                case 'error':
                  callbacks.onError?.(new Error(parsedData.error || 'SSE streaming error'));
                  break;
                default:
                  if (parsedData.token) {
                    callbacks.onToken(parsedData.token);
                  }
                  break;
              }
            } catch {
              // Plaintext fallback token
              if (eventType === 'token') {
                callbacks.onToken(dataStr);
              }
            }
          }
        }
      } catch (err: unknown) {
        if ((err as Error)?.name !== 'AbortError') {
          callbacks.onError?.(
            err instanceof Error ? err : new Error('Unknown SSE stream error')
          );
        }
      }
    })();

    // Return cancellation function
    return () => {
      controller.abort();
    };
  },
};

export default chatService;
