import React from 'react';
import { useHealth } from '@/hooks/useHealth';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Activity, RefreshCw, CheckCircle, AlertCircle, Server, Clock, Database, Globe } from 'lucide-react';
import { formatDate } from '@/utils/formatters';

export const HealthPage: React.FC = () => {
  const { health, loading, error, latencyMs, refresh } = useHealth(10000);

  return (
    <div className="space-y-6 max-w-4xl mx-auto py-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-2.5">
            <Activity className="h-7 w-7 text-primary" />
            Backend Engine Health & Diagnostics
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Real-time status of the FastAPI backend service and API gateway.
          </p>
        </div>
        <Button
          onClick={() => refresh()}
          variant="outline"
          size="sm"
          disabled={loading}
          className="self-start sm:self-auto"
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Now
        </Button>
      </div>

      {/* Main Status Indicator */}
      <Card className="border-l-4 border-l-primary">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {health?.status === 'healthy' ? (
                <CheckCircle className="h-6 w-6 text-emerald-500" />
              ) : (
                <AlertCircle className="h-6 w-6 text-amber-500" />
              )}
              <div>
                <CardTitle className="text-xl">FastAPI Gateway Status</CardTitle>
                <CardDescription>Endpoint: /api/v1/health</CardDescription>
              </div>
            </div>
            {health?.status === 'healthy' ? (
              <Badge variant="processed">ONLINE & HEALTHY</Badge>
            ) : error ? (
              <Badge variant="failed">OFFLINE / ERROR</Badge>
            ) : (
              <Badge variant="processing">CONNECTING...</Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="rounded-lg bg-destructive/10 p-4 text-sm text-destructive border border-destructive/20">
              <div className="font-semibold">Connection Error:</div>
              <p className="mt-1">{error}</p>
              <p className="mt-2 text-xs text-muted-foreground">
                Ensure backend FastAPI server is running at <code className="bg-muted px-1.5 py-0.5 rounded">http://localhost:8000</code>.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="rounded-lg border border-border bg-muted/20 p-4">
                <div className="flex items-center text-xs text-muted-foreground mb-1">
                  <Server className="h-4 w-4 mr-1 text-primary" />
                  Service Version
                </div>
                <div className="text-lg font-semibold text-foreground">
                  v{health?.version || '0.1.0'}
                </div>
              </div>

              <div className="rounded-lg border border-border bg-muted/20 p-4">
                <div className="flex items-center text-xs text-muted-foreground mb-1">
                  <Globe className="h-4 w-4 mr-1 text-sky-500" />
                  Environment
                </div>
                <div className="text-lg font-semibold text-foreground uppercase text-xs tracking-wider">
                  {health?.environment || 'development'}
                </div>
              </div>

              <div className="rounded-lg border border-border bg-muted/20 p-4">
                <div className="flex items-center text-xs text-muted-foreground mb-1">
                  <Clock className="h-4 w-4 mr-1 text-amber-500" />
                  Response Latency
                </div>
                <div className="text-lg font-semibold text-foreground">
                  {latencyMs !== null ? `${latencyMs} ms` : '--'}
                </div>
              </div>

              <div className="rounded-lg border border-border bg-muted/20 p-4">
                <div className="flex items-center text-xs text-muted-foreground mb-1">
                  <Database className="h-4 w-4 mr-1 text-emerald-500" />
                  Database Engine
                </div>
                <div className="text-lg font-semibold text-foreground text-sm">
                  PostgreSQL 16
                </div>
              </div>
            </div>
          )}
        </CardContent>
        {health?.timestamp && (
          <CardFooter className="text-xs text-muted-foreground border-t border-border pt-4">
            Last Ping Received: {formatDate(health.timestamp)}
          </CardFooter>
        )}
      </Card>

      {/* Architecture Verification Matrix */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Subsystem Health Verification</CardTitle>
          <CardDescription>Four-agent system readiness matrix</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-lg border border-border bg-card">
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-4 w-4 text-emerald-500" />
                <span className="text-sm font-medium">Member 1: Architecture & AI Service Contracts</span>
              </div>
              <Badge variant="processed">Verified</Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg border border-border bg-card">
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-4 w-4 text-emerald-500" />
                <span className="text-sm font-medium">Member 2: FastAPI Core & SQLAlchemy Database Session</span>
              </div>
              <Badge variant="processed">Verified</Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg border border-border bg-card">
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-4 w-4 text-emerald-500" />
                <span className="text-sm font-medium">Member 3: React / Vite Frontend Scaffolding & Theme Engine</span>
              </div>
              <Badge variant="processed">Active (This Branch)</Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg border border-border bg-card">
              <div className="flex items-center space-x-3">
                <Clock className="h-4 w-4 text-amber-500" />
                <span className="text-sm font-medium">Member 4: Docker Compose & CI/CD Pipeline</span>
              </div>
              <Badge variant="pending">In Progress</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
