import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { DashboardSummary } from '@/types/dashboard';
import { useDashboardContext } from '@/context/DashboardContext';
import {
  Sun,
  Sunrise,
  Sunset,
  Building2,
  FolderKanban,
  FileText,
  Calendar,
  Sparkles,
} from 'lucide-react';

interface WelcomeSectionProps {
  summary?: DashboardSummary | null;
  isLoading?: boolean;
}

export const WelcomeSection: React.FC<WelcomeSectionProps> = ({
  summary: propSummary,
  isLoading: propIsLoading,
}) => {
  const context = useDashboardContext();
  const summary = propSummary !== undefined ? propSummary : context?.summary ?? null;
  const isLoading = propIsLoading !== undefined ? propIsLoading : context?.isLoading ?? false;
  if (isLoading || !summary) {
    return (
      <Card className="p-6 border border-border bg-card/60 backdrop-blur-xs animate-pulse">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-3">
            <div className="h-4 w-28 bg-muted rounded" />
            <div className="h-8 w-64 bg-muted rounded" />
            <div className="h-4 w-48 bg-muted rounded" />
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 w-24 bg-muted rounded-lg" />
            ))}
          </div>
        </div>
      </Card>
    );
  }

  const { user, organization, kpi, greeting_time_of_day } = summary;

  const greetingMap: Record<
    string,
    { text: string; icon: React.ComponentType<{ className?: string }>; color: string }
  > = {
    morning: { text: 'Good morning', icon: Sunrise, color: 'text-amber-500' },
    afternoon: { text: 'Good afternoon', icon: Sun, color: 'text-orange-500' },
    evening: { text: 'Good evening', icon: Sunset, color: 'text-indigo-400' },
  };

  const activeGreeting = greetingMap[greeting_time_of_day] ?? {
    text: 'Welcome',
    icon: Sun,
    color: 'text-amber-500',
  };

  const GreetingIcon = activeGreeting.icon;

  return (
    <Card className="relative overflow-hidden border border-border bg-linear-to-br from-card via-card/90 to-primary/5 p-6 shadow-xs">
      <div className="absolute top-0 right-0 -mt-10 -mr-10 h-40 w-40 rounded-full bg-primary/5 blur-2xl pointer-events-none" />

      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
        {/* Left greeting & identity */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <GreetingIcon className={`h-4 w-4 ${activeGreeting.color}`} />
              {activeGreeting.text}
            </span>
            <Badge variant="outline" className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 border-primary/20 text-primary bg-primary/5">
              {organization.plan || 'Enterprise'}
            </Badge>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
            {user.full_name || 'Team Member'}
          </h1>

          <div className="flex items-center gap-2 text-xs sm:text-sm text-muted-foreground">
            <Building2 className="h-3.5 w-3.5 text-muted-foreground/70" />
            <span className="font-medium text-foreground">{organization.name}</span>
            <span>•</span>
            <span className="capitalize">{user.role} workspace</span>
          </div>
        </div>

        {/* Right metrics quick-bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3 shrink-0">
          <div className="rounded-xl border border-border/60 bg-background/50 backdrop-blur-xs p-3 text-center transition-colors hover:border-primary/40">
            <div className="flex items-center justify-center text-primary mb-1">
              <FolderKanban className="h-4 w-4" />
            </div>
            <div className="text-lg font-bold text-foreground">{kpi.total_projects}</div>
            <div className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
              Projects
            </div>
          </div>

          <div className="rounded-xl border border-border/60 bg-background/50 backdrop-blur-xs p-3 text-center transition-colors hover:border-primary/40">
            <div className="flex items-center justify-center text-emerald-500 mb-1">
              <FileText className="h-4 w-4" />
            </div>
            <div className="text-lg font-bold text-foreground">{kpi.total_documents}</div>
            <div className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
              Documents
            </div>
          </div>

          <div className="rounded-xl border border-border/60 bg-background/50 backdrop-blur-xs p-3 text-center transition-colors hover:border-primary/40">
            <div className="flex items-center justify-center text-blue-500 mb-1">
              <Calendar className="h-4 w-4" />
            </div>
            <div className="text-lg font-bold text-foreground">{kpi.upcoming_meetings}</div>
            <div className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
              Meetings
            </div>
          </div>

          <div className="rounded-xl border border-border/60 bg-background/50 backdrop-blur-xs p-3 text-center transition-colors hover:border-primary/40">
            <div className="flex items-center justify-center text-amber-500 mb-1">
              <Sparkles className="h-4 w-4" />
            </div>
            <div className="text-lg font-bold text-foreground">
              {kpi.ai_queries_today > 0 ? kpi.ai_queries_today : kpi.total_members}
            </div>
            <div className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
              {kpi.ai_queries_today > 0 ? 'AI Today' : 'Members'}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};
