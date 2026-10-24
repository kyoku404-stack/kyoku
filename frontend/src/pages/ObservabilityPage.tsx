import React, { useState } from 'react';
import { useObservability } from '@/hooks/useObservability';
import {
  SubsystemStatusCard,
  TelemetryMetricsGrid,
  AlertPanel,
  LogViewer,
  DiagnosticsModal,
  DeploymentReadinessCard,
} from '@/features/observability';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Activity,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  Play,
  FileCode,
  Shield,
  Clock,
  Layers,
  Download,
} from 'lucide-react';
import { formatDate } from '@/utils/formatters';
import { observabilityService } from '@/services/observabilityService';


export const ObservabilityPage: React.FC = () => {
  const {
    compositeHealth,
    dbHealth,
    storageHealth,
    apiHealth,
    authHealth,
    telemetry,
    latencyHistory,
    activeAlerts,
    loading,
    error,
    lastUpdated,
    isPolling,
    togglePolling,
    refresh,
    acknowledgeAlert,
    runDiagnostics,
  } = useObservability({ pollingInterval: 10000 });

  const [activeTab, setActiveTab] = useState<'overview' | 'subsystems' | 'telemetry' | 'alerts' | 'logs'>('overview');
  const [diagModalOpen, setDiagModalOpen] = useState<boolean>(false);
  const [downloadingMetrics, setDownloadingMetrics] = useState<boolean>(false);

  const overallStatus = compositeHealth?.status || telemetry?.system_status || 'healthy';

  const handleDownloadPrometheus = async () => {
    try {
      setDownloadingMetrics(true);
      const metricsText = await observabilityService.getRawPrometheusMetrics();
      const blob = new Blob([metricsText], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `keep-prometheus-metrics-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      // Fallback: download telemetry summary JSON
      const json = JSON.stringify(telemetry || compositeHealth, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `keep-telemetry-summary-${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } finally {
      setDownloadingMetrics(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto py-6 px-4 sm:px-6">
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
              <Activity className="h-7 w-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
                  System Observability & Monitoring
                </h1>
                <Badge variant="success" className="font-mono text-[10px] py-0.5 px-2">
                  Phase 1.10 Ready
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground mt-0.5">
                Multi-tier health probes, real-time telemetry metrics, alerting, and structured request tracing.
              </p>
            </div>
          </div>
        </div>

        {/* Global Toolbar Controls */}
        <div className="flex flex-wrap items-center gap-2 self-start md:self-auto">
          {/* Polling Toggle */}
          <Button
            onClick={togglePolling}
            variant="outline"
            size="sm"
            className="text-xs h-9 gap-1.5"
            title="Toggle background live telemetry polling (every 10s)"
          >
            <span
              className={`h-2 w-2 rounded-full ${
                isPolling ? 'bg-emerald-500 animate-pulse' : 'bg-muted-foreground'
              }`}
            />
            {isPolling ? 'Live Polling (10s)' : 'Polling Paused'}
          </Button>

          {/* Diagnostic Test Runner */}
          <Button
            onClick={() => setDiagModalOpen(true)}
            variant="outline"
            size="sm"
            className="text-xs h-9 gap-1.5"
          >
            <Play className="h-3.5 w-3.5 text-primary" />
            Run Diagnostics
          </Button>

          {/* Download Prometheus Metrics */}
          <Button
            onClick={handleDownloadPrometheus}
            disabled={downloadingMetrics}
            variant="outline"
            size="sm"
            className="text-xs h-9 gap-1.5"
            title="Download raw Prometheus exposition /metrics text"
          >
            <Download className="h-3.5 w-3.5 text-muted-foreground" />
            Metrics Exposition
          </Button>

          {/* Refresh Action */}
          <Button
            onClick={() => refresh()}
            variant="primary"
            size="sm"
            disabled={loading}
            className="text-xs h-9 gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Optional Connection Alert Banner */}
      {error && (
        <div className="p-3.5 rounded-lg border border-destructive/30 bg-destructive/10 text-destructive text-xs flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>Observability warning: {error}</span>
        </div>
      )}

      {/* Primary Composite Platform Status Banner */}

      <Card
        className={`border-l-4 shadow-sm transition-all ${
          overallStatus === 'healthy'
            ? 'border-l-emerald-500 bg-emerald-500/[0.02]'
            : overallStatus === 'degraded'
              ? 'border-l-amber-500 bg-amber-500/[0.02]'
              : 'border-l-rose-500 bg-rose-500/[0.02]'
        }`}
      >
        <CardHeader className="py-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div
                className={`p-2.5 rounded-full ${
                  overallStatus === 'healthy'
                    ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                    : overallStatus === 'degraded'
                      ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400'
                      : 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                }`}
              >
                {overallStatus === 'healthy' ? (
                  <CheckCircle className="h-6 w-6" />
                ) : (
                  <AlertTriangle className="h-6 w-6" />
                )}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <CardTitle className="text-lg font-bold">
                    Platform Operational Status: {overallStatus.toUpperCase()}
                  </CardTitle>
                </div>
                <CardDescription className="text-xs text-muted-foreground">
                  Probed across PostgreSQL, Multi-Tenant Storage, FastAPI Engine, and JWT Auth Providers.
                </CardDescription>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="text-right hidden sm:block">
                <span className="text-[11px] text-muted-foreground block">
                  Last Telemetry Ping
                </span>
                <span className="text-xs font-mono text-foreground font-medium">
                  {lastUpdated ? formatDate(lastUpdated.toISOString()) : 'Syncing...'}
                </span>
              </div>
              <Badge
                variant={overallStatus === 'healthy' ? 'success' : 'warning'}
                className="font-mono text-xs px-2.5 py-1"
              >
                {overallStatus === 'healthy' ? 'ALL SYSTEMS OPERATIONAL' : 'SYSTEM DEGRADED'}
              </Badge>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Navigation Tab Selector */}
      <div className="flex items-center gap-1 border-b border-border pb-px overflow-x-auto">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'overview'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
          }`}
        >
          <Layers className="h-3.5 w-3.5" />
          Command Center Overview
        </button>

        <button
          onClick={() => setActiveTab('subsystems')}
          className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'subsystems'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
          }`}
        >
          <Shield className="h-3.5 w-3.5" />
          Subsystem Health Probes
        </button>

        <button
          onClick={() => setActiveTab('telemetry')}
          className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'telemetry'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
          }`}
        >
          <Activity className="h-3.5 w-3.5" />
          KPIs & Latency Trends
        </button>

        <button
          onClick={() => setActiveTab('alerts')}
          className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'alerts'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
          }`}
        >
          <Clock className="h-3.5 w-3.5" />
          Alerts & Triggers
          {activeAlerts.filter((a) => !a.acknowledged).length > 0 && (
            <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-rose-500/10 text-rose-600 dark:text-rose-400 font-bold">
              {activeAlerts.filter((a) => !a.acknowledged).length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('logs')}
          className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'logs'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
          }`}
        >
          <FileCode className="h-3.5 w-3.5" />
          Structured Log Viewer
        </button>
      </div>

      {/* Main Tab Content Display */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* 4 Core Subsystem Probes Grid */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                Subsystem Probes Status
              </h2>
              <span className="text-xs text-muted-foreground font-mono">
                5 Probes Operational
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <SubsystemStatusCard
                type="database"
                status={compositeHealth?.dependencies.database?.status || 'healthy'}
                dbData={dbHealth || compositeHealth?.dependencies.database}
                loading={loading}
              />
              <SubsystemStatusCard
                type="storage"
                status={compositeHealth?.dependencies.storage?.status || 'healthy'}
                storageData={storageHealth || compositeHealth?.dependencies.storage}
                loading={loading}
              />
              <SubsystemStatusCard
                type="api"
                status={compositeHealth?.dependencies.api?.status || 'healthy'}
                apiData={apiHealth || compositeHealth?.dependencies.api}
                loading={loading}
              />
              <SubsystemStatusCard
                type="auth"
                status={compositeHealth?.dependencies.auth?.status || 'healthy'}
                authData={authHealth || compositeHealth?.dependencies.auth}
                loading={loading}
              />
            </div>
          </div>

          {/* Telemetry Metrics Grid */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                Operational Telemetry KPIs (Prometheus Summary)
              </h2>
              <Badge variant="secondary" className="text-[10px] font-mono">
                /api/v1/metrics/summary
              </Badge>
            </div>
            <TelemetryMetricsGrid
              kpis={telemetry?.kpis}
              uptimeSeconds={compositeHealth?.uptime_seconds || telemetry?.uptime_seconds}
              latencyHistory={latencyHistory}
              loading={loading}
            />
          </div>

          {/* Production Deployment & Ingress Topology Card */}
          <DeploymentReadinessCard />

          {/* Active Alerts Section */}
          <AlertPanel
            alerts={activeAlerts}
            onAcknowledge={acknowledgeAlert}
            loading={loading}
          />

          {/* Quick Structured Log Stream Preview */}
          <LogViewer />
        </div>
      )}

      {activeTab === 'subsystems' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <SubsystemStatusCard
              type="database"
              status={compositeHealth?.dependencies.database?.status || 'healthy'}
              dbData={dbHealth || compositeHealth?.dependencies.database}
              loading={loading}
            />
            <SubsystemStatusCard
              type="storage"
              status={compositeHealth?.dependencies.storage?.status || 'healthy'}
              storageData={storageHealth || compositeHealth?.dependencies.storage}
              loading={loading}
            />
            <SubsystemStatusCard
              type="api"
              status={compositeHealth?.dependencies.api?.status || 'healthy'}
              apiData={apiHealth || compositeHealth?.dependencies.api}
              loading={loading}
            />
            <SubsystemStatusCard
              type="auth"
              status={compositeHealth?.dependencies.auth?.status || 'healthy'}
              authData={authHealth || compositeHealth?.dependencies.auth}
              loading={loading}
            />
          </div>
        </div>
      )}

      {activeTab === 'telemetry' && (
        <div className="space-y-4">
          <TelemetryMetricsGrid
            kpis={telemetry?.kpis}
            uptimeSeconds={compositeHealth?.uptime_seconds || telemetry?.uptime_seconds}
            latencyHistory={latencyHistory}
            loading={loading}
          />
        </div>
      )}

      {activeTab === 'alerts' && (
        <AlertPanel
          alerts={activeAlerts}
          onAcknowledge={acknowledgeAlert}
          loading={loading}
        />
      )}

      {activeTab === 'logs' && (
        <LogViewer />
      )}

      {/* Diagnostics Test Execution Modal */}
      <DiagnosticsModal
        isOpen={diagModalOpen}
        onClose={() => setDiagModalOpen(false)}
        onRunDiagnostics={runDiagnostics}
      />
    </div>
  );
};

export default ObservabilityPage;
