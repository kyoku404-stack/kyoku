import React from 'react';
import { Card } from '@/components/ui/card';
import { PermissionGate } from '@/components/authorization/PermissionGate';
import { Permission } from '@/types/permission';
import type { DashboardKPI } from '@/types/dashboard';
import { useDashboardContext } from '@/context/DashboardContext';
import {
  FolderKanban,
  FileText,
  Users,
  Video,
  HardDrive,
  Sparkles,
  ArrowUpRight,
} from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  accentColor: string;
  progressPercent?: number;
  badge?: string;
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  accentColor,
  progressPercent,
  badge,
}) => {
  return (
    <Card className="p-4 border border-border bg-card hover:border-primary/40 transition-all duration-200 group relative overflow-hidden">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {title}
          </span>
          <div className="text-2xl font-black text-foreground tracking-tight">
            {value}
          </div>
          {subtitle && (
            <p className="text-[11px] text-muted-foreground">{subtitle}</p>
          )}
        </div>

        <div
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${accentColor} shadow-xs transition-transform group-hover:scale-105`}
        >
          <Icon className="h-5 w-5" />
        </div>
      </div>

      {progressPercent !== undefined && (
        <div className="mt-3 space-y-1">
          <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, Math.max(0, progressPercent))}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-muted-foreground">
            <span>{progressPercent}% consumed</span>
            {badge && <span className="font-medium text-foreground">{badge}</span>}
          </div>
        </div>
      )}
    </Card>
  );
};

interface KPICardGridProps {
  kpi?: DashboardKPI;
  isLoading?: boolean;
}

export const KPICardGrid: React.FC<KPICardGridProps> = ({
  kpi: propKpi,
  isLoading: propIsLoading,
}) => {
  const context = useDashboardContext();
  const kpi = propKpi !== undefined ? propKpi : context?.summary?.kpi;
  const isLoading = propIsLoading !== undefined ? propIsLoading : context?.isLoading ?? false;
  if (isLoading || !kpi) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3.5">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i} className="p-4 h-24 border border-border bg-card/60 animate-pulse">
            <div className="h-3 w-20 bg-muted rounded mb-2" />
            <div className="h-7 w-12 bg-muted rounded" />
          </Card>
        ))}
      </div>
    );
  }

  // Format bytes helper
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 GB';
    const gb = bytes / (1024 * 1024 * 1024);
    if (gb < 1) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${gb.toFixed(1)} GB`;
  };

  const storageUsed = formatBytes(kpi.storage_used_bytes);
  const storageTotal = formatBytes(kpi.storage_quota_bytes);
  const storagePercent = Math.round(
    kpi.storage_quota_bytes > 0
      ? (kpi.storage_used_bytes / kpi.storage_quota_bytes) * 100
      : 0
  );

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3.5">
      <KPICard
        title="Total Projects"
        value={kpi.total_projects}
        subtitle="Active initiatives"
        icon={FolderKanban}
        accentColor="bg-indigo-500/10 text-indigo-500"
      />

      <KPICard
        title="Documents"
        value={kpi.total_documents}
        subtitle="Indexed assets"
        icon={FileText}
        accentColor="bg-emerald-500/10 text-emerald-500"
      />

      <KPICard
        title="Team Members"
        value={kpi.total_members}
        subtitle="Active users"
        icon={Users}
        accentColor="bg-blue-500/10 text-blue-500"
      />

      <KPICard
        title="Meetings"
        value={kpi.upcoming_meetings}
        subtitle="Upcoming syncs"
        icon={Video}
        accentColor="bg-amber-500/10 text-amber-500"
      />

      <KPICard
        title="Storage Usage"
        value={storageUsed}
        subtitle={`of ${storageTotal} limit`}
        icon={HardDrive}
        accentColor="bg-purple-500/10 text-purple-500"
        progressPercent={storagePercent}
        badge={`${storagePercent}%`}
      />

      {/* AI Queries KPI — Visible to OrgAdmin / SuperAdmin per Section 2.2 */}
      <PermissionGate
        permission={Permission.ANALYTICS_VIEW}
        fallback={
          <KPICard
            title="System Status"
            value="Optimal"
            subtitle="Zero errors reported"
            icon={ArrowUpRight}
            accentColor="bg-teal-500/10 text-teal-500"
          />
        }
      >
        <KPICard
          title="AI Queries"
          value={kpi.ai_queries_today}
          subtitle="Processed today"
          icon={Sparkles}
          accentColor="bg-pink-500/10 text-pink-500"
        />
      </PermissionGate>
    </div>
  );
};
