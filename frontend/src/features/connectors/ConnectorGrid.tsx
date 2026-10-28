/**
 * Phase 3.1 ConnectorGrid Component.
 * Displays connector cards with live status badges, telemetry summaries, and action triggers.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import {
  RefreshCw,
  KeyRound,
  Trash2,
  ExternalLink,
  Search,
  HardDrive,
  FileText,
  MessageSquare,
  Code2,
  Kanban,
  Users2,
  Activity,
  CheckCircle,
  AlertTriangle,
  Clock,
  Radio,
} from 'lucide-react';
import type { ConnectorListItem } from '@/types/connector';

interface ConnectorGridProps {
  connectors: ConnectorListItem[];
  isLoading: boolean;
  categoryFilter: string;
  statusFilter: string;
  searchQuery: string;
  onCategoryChange: (category: string) => void;
  onStatusChange: (status: string) => void;
  onSearchChange: (query: string) => void;
  onSync: (id: string) => void;
  onInspectStatus: (id: string) => void;
  onAuthenticate: (connector: ConnectorListItem) => void;
  onRemove: (id: string) => void;
  onRegisterClick: () => void;
}

export const ConnectorGrid: React.FC<ConnectorGridProps> = ({
  connectors,
  isLoading,
  categoryFilter,
  statusFilter,
  searchQuery,
  onCategoryChange,
  onStatusChange,
  onSearchChange,
  onSync,
  onInspectStatus,
  onAuthenticate,
  onRemove,
  onRegisterClick,
}) => {
  const categories = [
    { id: 'ALL', label: 'All Categories' },
    { id: 'CLOUD_STORAGE', label: 'Cloud Storage' },
    { id: 'DOCUMENTATION', label: 'Documentation' },
    { id: 'COMMUNICATION', label: 'Communication' },
    { id: 'DEVELOPMENT', label: 'Development' },
    { id: 'PROJECT_MANAGEMENT', label: 'Project Mgmt' },
    { id: 'CRM', label: 'CRM' },
  ];

  const statuses = [
    { id: 'ALL', label: 'All Statuses' },
    { id: 'HEALTHY', label: 'Healthy' },
    { id: 'CONNECTED', label: 'Connected' },
    { id: 'SYNCING', label: 'Syncing' },
    { id: 'CONFIGURED', label: 'Configured' },
    { id: 'ERROR', label: 'Error' },
  ];

  const getPlatformIcon = (platform: string) => {
    switch (platform.toUpperCase()) {
      case 'GOOGLE_DRIVE':
      case 'ONEDRIVE':
      case 'SHAREPOINT':
      case 'DROPBOX':
      case 'S3':
        return <HardDrive className="w-5 h-5 text-sky-500" />;
      case 'CONFLUENCE':
      case 'NOTION':
        return <FileText className="w-5 h-5 text-indigo-500" />;
      case 'SLACK':
      case 'TEAMS':
        return <MessageSquare className="w-5 h-5 text-emerald-500" />;
      case 'GITHUB':
      case 'GITLAB':
        return <Code2 className="w-5 h-5 text-purple-500" />;
      case 'JIRA':
        return <Kanban className="w-5 h-5 text-blue-500" />;
      case 'SALESFORCE':
      case 'HUBSPOT':
        return <Users2 className="w-5 h-5 text-amber-500" />;
      default:
        return <Activity className="w-5 h-5 text-slate-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'HEALTHY':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
            <CheckCircle className="w-3 h-3" /> Healthy
          </span>
        );
      case 'CONNECTED':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 dark:bg-blue-950/60 px-2 py-0.5 text-xs font-semibold text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
            <CheckCircle className="w-3 h-3" /> Connected
          </span>
        );
      case 'SYNCING':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 dark:bg-amber-950/60 px-2 py-0.5 text-xs font-semibold text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800 animate-pulse">
            <Radio className="w-3 h-3 animate-spin" /> Syncing
          </span>
        );
      case 'CONFIGURED':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-xs font-semibold text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
            <Clock className="w-3 h-3" /> Configured
          </span>
        );
      case 'ERROR':
      case 'DEGRADED':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 dark:bg-rose-950/60 px-2 py-0.5 text-xs font-semibold text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800">
            <AlertTriangle className="w-3 h-3" /> Attention
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center rounded-full bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-xs font-medium text-slate-600 dark:text-slate-400">
            {status}
          </span>
        );
    }
  };

  const formatLastSync = (timestamp: string | null) => {
    if (!timestamp) return 'Never synchronized';
    const date = new Date(timestamp);
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="flex flex-col gap-5">
      {/* Search and Filters Bar */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 shadow-sm">
        {/* Search input */}
        <div className="relative flex-1 min-w-[240px]">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search connectors by name or platform..."
            className="w-full pl-9 pr-4 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800/80 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Filter dropdowns */}
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={categoryFilter}
            onChange={(e) => onCategoryChange(e.target.value)}
            className="px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm"
          >
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>

          <select
            value={statusFilter}
            onChange={(e) => onStatusChange(e.target.value)}
            className="px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm"
          >
            {statuses.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Grid view */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-500" />
          <span className="text-sm font-medium text-slate-500 dark:text-slate-400">
            Loading enterprise connectors...
          </span>
        </div>
      ) : connectors.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 px-4 text-center rounded-xl border border-dashed border-slate-300 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
          <div className="w-12 h-12 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 flex items-center justify-center text-indigo-600 dark:text-indigo-400 mb-3">
            <ExternalLink className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-white">
            No connectors configured
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 max-w-sm mt-1">
            Connect your first cloud storage, communication, or code repository platform to begin syncing knowledge.
          </p>
          <button
            type="button"
            onClick={onRegisterClick}
            className="mt-4 px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-colors"
          >
            Add First Connector
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {connectors.map((c) => (
            <div
              key={c.id}
              className="flex flex-col justify-between rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm hover:shadow-md transition-shadow"
            >
              <div>
                {/* Card Header */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                      {getPlatformIcon(c.platform_type)}
                    </div>
                    <div>
                      <h3 className="text-base font-semibold text-slate-900 dark:text-white line-clamp-1" title={c.name}>
                        {c.name}
                      </h3>
                      <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                        {c.platform_type.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                  <div>{getStatusBadge(c.status)}</div>
                </div>

                {/* Body metadata */}
                <div className="mt-4 space-y-2 border-t border-slate-100 dark:border-slate-800/80 pt-3 text-xs text-slate-600 dark:text-slate-400">
                  <div className="flex items-center justify-between">
                    <span>Documents Synced</span>
                    <span className="font-semibold text-slate-900 dark:text-white">
                      {c.total_documents_synced.toLocaleString()} docs
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Auth Scheme</span>
                    <span className="font-medium text-slate-700 dark:text-slate-300">
                      {c.auth_type.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Last Synchronized</span>
                    <span className="text-slate-500 dark:text-slate-400">
                      {formatLastSync(c.last_sync_at)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action buttons */}
              <div className="mt-5 flex items-center justify-between gap-2 border-t border-slate-100 dark:border-slate-800/80 pt-3">
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => onSync(c.id)}
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-md bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/60 dark:hover:bg-indigo-900/60 text-indigo-700 dark:text-indigo-400 transition-colors"
                    title="Run manual sync"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    Sync
                  </button>

                  <button
                    type="button"
                    onClick={() => onInspectStatus(c.id)}
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-md border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors"
                    title="View health telemetry"
                  >
                    <Activity className="w-3.5 h-3.5" />
                    Status
                  </button>

                  <button
                    type="button"
                    onClick={() => onAuthenticate(c)}
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-md border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors"
                    title="Update credentials"
                  >
                    <KeyRound className="w-3.5 h-3.5" />
                    Auth
                  </button>
                </div>

                <button
                  type="button"
                  onClick={() => onRemove(c.id)}
                  className="p-1.5 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 rounded-md transition-colors"
                  title="Remove connector"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
