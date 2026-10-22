import React, { useState } from 'react';
import type { SystemAlert, AlertSeverity } from '@/types/observability';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Bell,
  AlertTriangle,
  AlertCircle,
  ShieldAlert,
  Info,
  CheckCircle2,
  Filter,
} from 'lucide-react';
import { formatDate } from '@/utils/formatters';

interface AlertPanelProps {
  alerts: SystemAlert[];
  onAcknowledge?: (alertId: string) => void;
  loading?: boolean;
}

export const getAlertSeverityBadge = (severity: AlertSeverity) => {
  switch (severity) {
    case 'CRITICAL':
      return (
        <Badge variant="destructive" className="gap-1 font-mono text-[10px]">
          <AlertCircle className="h-3 w-3" />
          CRITICAL
        </Badge>
      );
    case 'WARNING':
      return (
        <Badge variant="warning" className="gap-1 font-mono text-[10px]">
          <AlertTriangle className="h-3 w-3" />
          WARNING
        </Badge>
      );
    case 'SECURITY':
      return (
        <Badge variant="secondary" className="gap-1 font-mono text-[10px] bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
          <ShieldAlert className="h-3 w-3" />
          SECURITY
        </Badge>
      );
    case 'INFO':
    default:
      return (
        <Badge variant="secondary" className="gap-1 font-mono text-[10px] bg-sky-500/10 text-sky-600 dark:text-sky-400">
          <Info className="h-3 w-3" />
          INFO
        </Badge>
      );
  }
};

export const AlertPanel: React.FC<AlertPanelProps> = ({
  alerts = [],
  onAcknowledge,
  loading = false,
}) => {
  const [filterSeverity, setFilterSeverity] = useState<AlertSeverity | 'ALL'>('ALL');
  const [showAcknowledged, setShowAcknowledged] = useState<boolean>(false);

  // Default alerts matching devdocs Chapter 10 if none passed
  const sampleAlerts: SystemAlert[] = alerts.length > 0 ? alerts : [
    {
      id: 'alt-001',
      severity: 'INFO',
      title: 'Scheduled Storage Snapshot',
      message: 'Automated disk snapshot completed with SHA-256 integrity verification.',
      timestamp: new Date(Date.now() - 25 * 60 * 1000).toISOString(),
      component: 'Storage',
      acknowledged: false,
    },
    {
      id: 'alt-002',
      severity: 'WARNING',
      title: 'Memory Utilization Threshold',
      message: 'Container memory RSS reached 78% of allocated container reservation.',
      timestamp: new Date(Date.now() - 48 * 60 * 1000).toISOString(),
      component: 'API Gateway',
      threshold: 'Memory > 75%',
      acknowledged: false,
    },
    {
      id: 'alt-003',
      severity: 'SECURITY',
      title: 'Multiple Failed Authentication Attempts',
      message: 'Detected 3 invalid login attempts from external IP address 198.51.100.22.',
      timestamp: new Date(Date.now() - 95 * 60 * 1000).toISOString(),
      component: 'Auth Service',
      threshold: 'Failed Logins >= 3',
      acknowledged: true,
    },
  ];

  const filteredAlerts = sampleAlerts.filter((item) => {
    if (filterSeverity !== 'ALL' && item.severity !== filterSeverity) return false;
    if (!showAcknowledged && item.acknowledged) return false;
    return true;
  });

  const unacknowledgedCount = sampleAlerts.filter((a) => !a.acknowledged).length;

  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Bell className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-base font-semibold">
                  System Alerts & Diagnostic Triggers
                </CardTitle>
                {unacknowledgedCount > 0 && (
                  <Badge variant="destructive" className="text-[10px] px-1.5 py-0">
                    {unacknowledgedCount} Active
                  </Badge>
                )}
              </div>
              <CardDescription className="text-xs">
                Real-time notifications for threshold breaches, security alerts, and infrastructure warnings.
              </CardDescription>
            </div>
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs text-muted-foreground mr-1 flex items-center gap-1">
              <Filter className="h-3 w-3" /> Filter:
            </span>
            {(['ALL', 'CRITICAL', 'WARNING', 'SECURITY', 'INFO'] as const).map((sev) => (
              <button
                key={sev}
                onClick={() => setFilterSeverity(sev)}
                className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                  filterSeverity === sev
                    ? 'bg-primary text-primary-foreground font-semibold'
                    : 'bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
              >
                {sev}
              </button>
            ))}

            <button
              onClick={() => setShowAcknowledged(!showAcknowledged)}
              className={`ml-2 px-2 py-0.5 rounded text-[11px] border border-border transition-colors ${
                showAcknowledged
                  ? 'bg-muted text-foreground font-semibold'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {showAcknowledged ? 'Hide Dismissed' : 'Show Dismissed'}
            </button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {loading ? (
          <div className="space-y-2 py-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse h-16 bg-muted/40 rounded-lg" />
            ))}
          </div>
        ) : filteredAlerts.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground border border-dashed rounded-lg">
            <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-emerald-500 opacity-80" />
            <p className="text-sm font-medium text-foreground">Zero Active Threshold Alerts</p>
            <p className="text-xs mt-1 text-muted-foreground">
              All infrastructure subsystems, CPU, memory, and database connections are operating within normal parameters.
            </p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {filteredAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-3.5 rounded-lg border transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                  alert.acknowledged
                    ? 'bg-muted/20 border-border/40 opacity-70'
                    : alert.severity === 'CRITICAL'
                      ? 'bg-rose-500/5 border-rose-500/30'
                      : alert.severity === 'WARNING'
                        ? 'bg-amber-500/5 border-amber-500/30'
                        : alert.severity === 'SECURITY'
                          ? 'bg-indigo-500/5 border-indigo-500/30'
                          : 'bg-card border-border'
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {getAlertSeverityBadge(alert.severity)}
                    {alert.component && (
                      <span className="text-[11px] font-mono text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                        {alert.component}
                      </span>
                    )}
                    <span className="text-sm font-semibold text-foreground">
                      {alert.title}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">{alert.message}</p>
                  <div className="flex items-center gap-3 text-[11px] text-muted-foreground pt-0.5">
                    <span>{formatDate(alert.timestamp)}</span>
                    {alert.threshold && (
                      <span className="font-mono text-[10px] text-amber-600 dark:text-amber-400">
                        Trigger: {alert.threshold}
                      </span>
                    )}
                  </div>
                </div>

                {!alert.acknowledged && onAcknowledge && (
                  <Button
                    onClick={() => onAcknowledge(alert.id)}
                    variant="outline"
                    size="sm"
                    className="shrink-0 self-end sm:self-center text-xs h-7 gap-1"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5 text-muted-foreground" />
                    Acknowledge
                  </Button>
                )}
                {alert.acknowledged && (
                  <span className="text-[11px] text-muted-foreground italic self-end sm:self-center">
                    Acknowledged
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AlertPanel;
