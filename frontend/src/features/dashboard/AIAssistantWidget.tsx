import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAIAssistant } from '@/hooks/useDashboard';
import { useAuthorization } from '@/hooks/useAuthorization';
import {
  Sparkles,
  Send,
  RotateCcw,
  FileText,
  Bot,
  User as UserIcon,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';

export const AIAssistantWidget: React.FC = () => {
  const { role } = useAuthorization();
  const {
    query,
    setQuery,
    status,
    streamingResponse,
    sources,
    error,
    submitQuery,
    resetAssistant,
  } = useAIAssistant();

  // Role-tailored suggested prompts per Section 5.3
  const getSuggestedPrompts = () => {
    switch (role) {
      case 'SuperAdmin':
      case 'OrgAdmin':
        return [
          "Summarize this week's activity across projects",
          'Which projects are behind schedule?',
          'What organizational knowledge is most accessed?',
        ];
      case 'Manager':
        return [
          'Summarize open tasks for my projects',
          'Which documents were uploaded this week?',
          'What are the upcoming team milestones?',
        ];
      case 'Member':
        return [
          'Summarize the latest project architecture notes',
          'Find recent policy documents and standards',
          'What meetings are scheduled for today?',
        ];
      default:
        return [
          'What projects and documentation can I access?',
          'Find documents in active workspaces',
        ];
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitQuery();
    }
  };

  const isGenerating = status === 'LOADING' || status === 'STREAMING';

  return (
    <Card className="border border-border bg-card flex flex-col h-full shadow-xs">
      <CardHeader className="pb-3 border-b border-border/60">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-base font-bold text-foreground">
                  AI Knowledge Assistant
                </CardTitle>
                <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-primary/30 text-primary bg-primary/5">
                  Phase 1.7 Shell
                </Badge>
              </div>
              <CardDescription className="text-xs text-muted-foreground">
                Ask questions across organizational documents and workspaces
              </CardDescription>
            </div>
          </div>

          {(status !== 'IDLE' || streamingResponse) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={resetAssistant}
              className="h-7 text-xs gap-1 text-muted-foreground hover:text-foreground"
            >
              <RotateCcw className="h-3 w-3" />
              <span>Reset</span>
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-4 space-y-4 flex flex-col justify-between">
        {/* Output & Conversation display */}
        <div className="flex-1 overflow-y-auto space-y-3 min-h-[160px] max-h-[320px] rounded-lg border border-border/60 bg-muted/20 p-3.5 text-xs">
          {status === 'IDLE' && !streamingResponse ? (
            <div className="h-full flex flex-col justify-center items-center text-center space-y-3 py-4">
              <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                <Bot className="h-5 w-5" />
              </div>
              <div className="space-y-1 max-w-sm">
                <p className="font-semibold text-foreground">
                  Hello! How can I assist you with KEEP knowledge today?
                </p>
                <p className="text-[11px] text-muted-foreground">
                  Choose a role-suggested prompt below or type your inquiry.
                </p>
              </div>

              {/* Suggested prompts chips */}
              <div className="flex flex-wrap gap-1.5 justify-center pt-2">
                {getSuggestedPrompts().map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setQuery(prompt);
                      submitQuery(prompt);
                    }}
                    className="rounded-full border border-border bg-background px-3 py-1 text-[11px] text-foreground hover:border-primary/50 hover:bg-primary/5 transition-all text-left"
                  >
                    "{prompt}"
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {/* User question */}
              <div className="flex items-start gap-2.5">
                <div className="h-6 w-6 rounded-full bg-muted flex items-center justify-center text-muted-foreground shrink-0 mt-0.5">
                  <UserIcon className="h-3.5 w-3.5" />
                </div>
                <div className="bg-background border border-border rounded-lg p-2.5 max-w-[85%] text-xs font-medium text-foreground">
                  {query || 'Inquiry'}
                </div>
              </div>

              {/* Assistant answer */}
              <div className="flex items-start gap-2.5">
                <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center text-primary shrink-0 mt-0.5">
                  <Sparkles className="h-3.5 w-3.5" />
                </div>
                <div className="space-y-2 flex-1">
                  <div className="bg-card border border-border/80 rounded-lg p-3 text-xs leading-relaxed text-foreground shadow-2xs">
                    {streamingResponse ? (
                      <div className="space-y-1.5 whitespace-pre-wrap">
                        {streamingResponse}
                        {isGenerating && (
                          <span className="inline-block w-1.5 h-3.5 ml-1 bg-primary animate-pulse align-middle" />
                        )}
                      </div>
                    ) : status === 'LOADING' ? (
                      <div className="flex items-center gap-2 text-muted-foreground text-[11px]">
                        <span className="inline-block h-2 w-2 rounded-full bg-primary animate-ping" />
                        <span>Consulting KEEP knowledge engine...</span>
                      </div>
                    ) : null}
                  </div>

                  {/* Sources citation list (Phase 1.7 / 2.2) */}
                  {sources && sources.length > 0 && (
                    <div className="space-y-1 pt-1">
                      <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                        <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                        <span>Grounding Citations ({sources.length})</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {sources.map((src, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center gap-1 rounded bg-background border border-border px-2 py-0.5 text-[10px] text-muted-foreground"
                          >
                            <FileText className="h-3 w-3 text-emerald-500" />
                            <span className="font-medium text-foreground">{src.title}</span>
                            <span>({Math.round(src.relevance_score * 100)}%)</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Error state */}
                  {error && (
                    <div className="rounded-md border border-destructive/30 bg-destructive/5 p-2.5 text-xs text-destructive flex items-center gap-2">
                      <AlertCircle className="h-4 w-4 shrink-0" />
                      <span>{error}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Query Input Box */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask AI Assistant about organizational knowledge..."
            disabled={isGenerating}
            className="flex-1 h-9 rounded-lg border border-border bg-background px-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-1 focus:ring-primary disabled:opacity-50"
            aria-label="Ask AI Assistant query"
          />

          <Button
            size="sm"
            onClick={() => submitQuery()}
            disabled={!query.trim() || isGenerating}
            className="h-9 px-3 gap-1.5 shrink-0"
          >
            <Send className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Ask</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
