/**
 * Chat & RAG Assistant Feature Module
 * Citation-grounded conversational AI and real-time streaming inference.
 */

export * from '@/types/chat';
export { chatService } from '@/services/chatService';
export { useChatStream } from '@/hooks/useChatStream';

export const CHAT_FEATURE = {
  name: 'chat',
  version: '1.2.0',
  description: 'Enterprise generative AI assistant with streaming and citation grounding',
};
