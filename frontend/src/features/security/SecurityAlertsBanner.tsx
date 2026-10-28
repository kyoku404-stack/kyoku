/**
 * Phase 3.3 SecurityAlertsBanner Component.
 * Real-time enterprise security threat monitor and incident remediation.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import {
  AlertOctagon,
  ShieldCheck,
  CheckCircle,
  Activity,
} from 'lucide-react';
import type { SecurityThreatAlertItem } from '@/types/security';

interface SecurityAlertsBannerProps {
  alerts: SecurityThreatAlertItem[];
  onResolveAlert: (alertId: string) => Promise<unknown>;
  isLoading: boolean;
}

export const SecurityAlertsBanner: React.FC<SecurityAlertsBannerProps> = ({
  alerts,
  onResolveAlert,
  isLoading,
}) => {
  const activeAlerts = alerts.filter((a) => !a.resolved);

  if (activeAlerts.length === 0) {
    return (
      <div className="p-4 rounded-xl border border-emerald-200/80 dark:border-emerald-950 bg-emerald-50/50 dark:bg-emerald-950/20 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-100 dark:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300 flex items-center justify-center">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-emerald-900 dark:text-emerald-200">
              Zero Active Security Anomalies
            </h4>
            <p className="text-xs text-emerald-700/80 dark:text-emerald-400">
              Zero-trust perimeter active. Continuous monitoring of logins, prompt injections, and exfiltrations.
            </p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200">
          All Systems Nominal
        </span>
      </div>
    );
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-rose-600 text-white';
      case 'HIGH':
        return 'bg-amber-600 text-white';
      case 'MEDIUM':
        return 'bg-yellow-500 text-slate-950';
      case 'LOW':
      default:
        return 'bg-blue-600 text-white';
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2 text-rose-600 dark:text-rose-400 text-xs font-bold tracking-wider uppercase">
        <Activity className="w-4 h-4 animate-pulse" />
        <span>Active Security Threat Incidents ({activeAlerts.length})</span>
      </div>

      <div className="flex flex-col gap-2.5">
        {activeAlerts.map((alert) => (
          <div
            key={alert.id}
            className="p-4 rounded-xl border border-rose-200 dark:border-rose-900/60 bg-rose-50/70 dark:bg-rose-950/30 flex flex-col md:flex-row md:items-center justify-between gap-3 transition"
          >
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-rose-100 dark:bg-rose-900/50 text-rose-600 dark:text-rose-400 shrink-0">
                <AlertOctagon className="w-5 h-5" />
              </div>
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-full ${getSeverityBadge(
                      alert.severity
                    )}`}
                  >
                    {alert.severity}
                  </span>
                  <span className="font-bold text-xs text-rose-950 dark:text-rose-100">
                    {alert.alert_type.replace(/_/g, ' ')}
                  </span>
                  <span className="text-[11px] font-mono text-rose-600/70 dark:text-rose-400">
                    Source: {alert.source_ip}
                  </span>
                </div>
                <p className="text-xs text-rose-900 dark:text-rose-200">
                  {alert.description}
                </p>
                <span className="text-[10px] text-rose-500/80 font-mono">
                  Triggered at {new Date(alert.triggered_at).toLocaleString()}
                </span>
              </div>
            </div>

            <button
              onClick={() => onResolveAlert(alert.id)}
              disabled={isLoading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-white dark:bg-slate-900 text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-800 hover:bg-rose-100 dark:hover:bg-rose-950 transition shadow-sm w-fit shrink-0"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              Resolve Incident
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SecurityAlertsBanner;
