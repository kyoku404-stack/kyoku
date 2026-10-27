import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, ShieldAlert, Cpu } from 'lucide-react';
import type { AssistantMessage } from '@/types/assistant';

interface AssistantChatBoxProps {
  messages: AssistantMessage[];
  isLoading: boolean;
  onSendMessage: (text: string) => Promise<void>;
  onOpenApprovalModal?: () => void;
  onNewSession?: () => void;
}

export const AssistantChatBox: React.FC<AssistantChatBoxProps> = ({
  messages,
  isLoading,
  onSendMessage,
  onOpenApprovalModal,
  onNewSession,
}) => {
  const [inputText, setInputText] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;
    const text = inputText;
    setInputText('');
    await onSendMessage(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-[580px] bg-slate-900/80 border border-slate-800 rounded-2xl backdrop-blur-md overflow-hidden">
      {/* Chat Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800 bg-slate-950/40">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Conversational AI Assistant
            </h3>
            <p className="text-[11px] text-slate-400">Agentic multi-step task execution engine</p>
          </div>
        </div>

        {onNewSession && (
          <button
            type="button"
            onClick={onNewSession}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium px-2.5 py-1 rounded-md hover:bg-slate-800/60 transition-colors"
          >
            New Session
          </button>
        )}
      </div>

      {/* Messages Thread */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 text-xs font-bold ${
                  isUser
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-800 border border-slate-700 text-indigo-400'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div
                className={`max-w-[80%] rounded-2xl p-3.5 text-xs leading-relaxed ${
                  isUser
                    ? 'bg-indigo-600 text-white rounded-tr-none'
                    : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none'
                }`}
              >
                {!isUser && msg.intent && (
                  <div className="flex items-center gap-1.5 mb-2">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                      {msg.intent}
                    </span>
                  </div>
                )}

                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Tool calls execution pills */}
                {!isUser && msg.tools_executed && msg.tools_executed.length > 0 && (
                  <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-1.5">
                    <span className="text-[10px] text-slate-500 font-medium">Tools used:</span>
                    {msg.tools_executed.map((tool, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] font-mono text-emerald-400"
                      >
                        <Cpu className="w-3 h-3" /> {tool}
                      </span>
                    ))}
                  </div>
                )}

                {/* HITL Action banner */}
                {!isUser && msg.requires_approval && (
                  <div className="mt-3 p-2 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-center justify-between">
                    <div className="flex items-center space-x-1.5 text-amber-300 text-[11px] font-medium">
                      <ShieldAlert className="w-3.5 h-3.5" />
                      <span>Approval required</span>
                    </div>
                    {onOpenApprovalModal && (
                      <button
                        type="button"
                        onClick={onOpenApprovalModal}
                        className="px-2 py-0.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-[10px] rounded transition-colors"
                      >
                        Review
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex items-start space-x-3">
            <div className="w-7 h-7 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-indigo-400">
              <Sparkles className="w-4 h-4 animate-spin" />
            </div>
            <div className="bg-slate-950 border border-slate-800 rounded-2xl rounded-tl-none p-3.5 text-xs text-slate-400 flex items-center space-x-2">
              <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
              <span>Analyzing intent & orchestrating tools...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-slate-800 bg-slate-950/60">
        <div className="relative flex items-center">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question, request a report, or instruct a task (e.g. 'Generate weekly summary')..."
            rows={2}
            className="w-full pl-3 pr-12 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 resize-none focus:outline-none focus:border-indigo-500 transition-colors"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isLoading}
            className="absolute right-2.5 p-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-lg transition-colors"
            title="Send Message"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
