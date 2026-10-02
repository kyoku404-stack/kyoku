import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { chatService } from '@/services/chatService';
import { useChatStream } from '@/hooks/useChatStream';
import type { ChatCitation } from '@/types/chat';

describe('Chat SSE Streaming & useChatStream Hook', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('parses SSE token, citation, and done events properly in streamChat', async () => {
    const ssePayload =
      'event: citation\n' +
      'data: [{"document_id":"d1","filename":"policy.pdf","page_number":1,"chunk_index":0,"snippet":"Snippet text","relevance_score":0.95}]\n\n' +
      'event: token\n' +
      'data: {"token":"Hello "}\n\n' +
      'event: token\n' +
      'data: {"token":"world!"}\n\n' +
      'event: done\n' +
      'data: {"finish_reason":"stop","total_tokens":4}\n\n';

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(ssePayload));
        controller.close();
      },
    });

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      body: stream,
    } as unknown as Response);

    const tokens: string[] = [];
    let receivedCitations: ChatCitation[] = [];
    const receivedDone = { current: null as { conversation_id?: string; total_tokens?: number } | null };

    await new Promise<void>((resolve) => {
      chatService.streamChat(
        { query: 'test query' },
        {
          onToken: (t) => tokens.push(t),
          onCitation: (c) => {
            receivedCitations = c;
          },
          onDone: (d) => {
            receivedDone.current = d;
            resolve();
          },
        }
      );
    });

    expect(tokens.join('')).toBe('Hello world!');
    expect(receivedCitations).toHaveLength(1);
    expect(receivedCitations[0].filename).toBe('policy.pdf');
    expect(receivedDone.current?.total_tokens).toBe(4);
  });

  it('accumulates tokens and citations in useChatStream hook', async () => {
    const ssePayload =
      'event: citation\n' +
      'data: [{"document_id":"d2","filename":"report.pdf","snippet":"Annual revenue","relevance_score":0.99}]\n\n' +
      'event: token\n' +
      'data: {"token":"Revenue "}\n\n' +
      'event: token\n' +
      'data: {"token":"grew 20%."}\n\n' +
      'event: done\n' +
      'data: {"total_tokens":6}\n\n';

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(ssePayload));
        controller.close();
      },
    });

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      body: stream,
    } as unknown as Response);

    const { result } = renderHook(() => useChatStream());

    expect(result.current.answer).toBe('');
    expect(result.current.isStreaming).toBe(false);

    act(() => {
      result.current.sendStreamQuery('What is the revenue growth?');
    });

    expect(result.current.isStreaming).toBe(true);

    // Allow async stream reading to complete
    await act(async () => {
      await new Promise((r) => setTimeout(r, 50));
    });

    expect(result.current.answer).toBe('Revenue grew 20%.');
    expect(result.current.citations).toHaveLength(1);
    expect(result.current.citations[0].filename).toBe('report.pdf');
    expect(result.current.totalTokens).toBe(6);
    expect(result.current.isStreaming).toBe(false);
  });

  it('handles stream error gracefully', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Network error during stream'));

    const { result } = renderHook(() => useChatStream());

    act(() => {
      result.current.sendStreamQuery('Failing query');
    });

    await act(async () => {
      await new Promise((r) => setTimeout(r, 20));
    });

    expect(result.current.error).toBe('Network error during stream');
    expect(result.current.isStreaming).toBe(false);
  });
});
