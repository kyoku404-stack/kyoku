import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Server,
  Globe,
  ShieldCheck,
  Layers,
  Cpu,
  CheckCircle2,
  Activity,
  HardDrive,
  Workflow,
} from 'lucide-react';
import { CONFIG } from '@/constants/config';

interface DeploymentReadinessCardProps {
  className?: string;
}

export const DeploymentReadinessCard: React.FC<DeploymentReadinessCardProps> = ({
  className,
}) => {
  const isProd = CONFIG.IS_PRODUCTION;
  const isStaging = CONFIG.IS_STAGING;

  return (
    <Card className={className}>
      <CardHeader className="pb-4 border-b border-border">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
              <Server className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-base sm:text-lg font-bold">
                  Frontend Production Deployment & Ingress Topology
                </CardTitle>
                <Badge
                  variant={isProd ? 'success' : isStaging ? 'warning' : 'outline'}
                  className="font-mono text-[10px]"
                >
                  {CONFIG.ENVIRONMENT.toUpperCase()}
                </Badge>
              </div>
              <CardDescription className="text-xs text-muted-foreground mt-0.5">
                Nginx gateway routing, optimized vendor bundle code-splitting, and zero-trust security hardening.
              </CardDescription>
            </div>
          </div>

          <Badge variant="success" className="gap-1 font-mono text-[11px] self-start sm:self-auto">
            <CheckCircle2 className="h-3.5 w-3.5" />
            PHASE 1.10 READY
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-5 space-y-5">
        {/* Architecture & Ingress Matrix */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Card 1: Ingress Routing */}
          <div className="rounded-lg border border-border bg-card/60 p-4 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <Globe className="h-4 w-4 text-primary" />
              Reverse Proxy Ingress
            </div>
            <div className="text-sm font-semibold text-foreground flex items-center gap-1.5">
              <span>{CONFIG.DEPLOYMENT.REVERSE_PROXY}</span>
              <span className="text-xs text-muted-foreground font-mono">({CONFIG.DEPLOYMENT.GATEWAY_PROTOCOL})</span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Path <code className="text-primary font-mono bg-muted px-1 py-0.5 rounded text-[11px]">{CONFIG.API_BASE_URL}</code> routing
              terminating TLS 1.3 and preserving ingress correlation headers.
            </p>
          </div>

          {/* Card 2: Bundle Splitting & Optimization */}
          <div className="rounded-lg border border-border bg-card/60 p-4 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <Layers className="h-4 w-4 text-emerald-500" />
              Bundle Splitting & Caching
            </div>
            <div className="text-sm font-semibold text-foreground flex items-center gap-1.5">
              <span>Rollup Code Splitting</span>
              <span className="text-xs text-emerald-600 dark:text-emerald-400 font-mono">4 Chunks</span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Targeted vendor bundles (<code className="font-mono text-[11px]">react</code>, <code className="font-mono text-[11px]">ui</code>, <code className="font-mono text-[11px]">core</code>) with immutable content-hash cache busting.
            </p>
          </div>

          {/* Card 3: Enterprise Security Hardening */}
          <div className="rounded-lg border border-border bg-card/60 p-4 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <ShieldCheck className="h-4 w-4 text-primary" />
              Defense-in-Depth Headers
            </div>
            <div className="text-sm font-semibold text-foreground flex items-center gap-1.5">
              <span>Enterprise Hardened</span>
              <span className="text-xs text-primary font-mono">ADR-029</span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Strict HSTS, Frame-Options DENY, Content-Type nosniff, and granular CSP policies enforced on all egress routes.
            </p>
          </div>
        </div>

        {/* Detailed Spec Badges & Viewport Adaptations */}
        <div className="rounded-xl bg-muted/40 p-4 border border-border/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3 text-xs">
            <div className="flex items-center gap-1.5 font-medium text-foreground">
              <Activity className="h-3.5 w-3.5 text-primary" />
              <span>Target SLOs:</span>
            </div>
            <span className="text-muted-foreground">
              RPO <strong className="text-foreground">&lt; {CONFIG.DEPLOYMENT.STORAGE_SLO_RPO_HOURS}h</strong>
            </span>
            <span className="text-border">|</span>
            <span className="text-muted-foreground">
              RTO <strong className="text-foreground">&lt; {CONFIG.DEPLOYMENT.STORAGE_SLO_RTO_MINUTES}m</strong>
            </span>
            <span className="text-border">|</span>
            <span className="text-muted-foreground">
              Page Load <strong className="text-foreground">&lt; 2.0s</strong>
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="text-[10px] font-mono gap-1">
              <Cpu className="h-3 w-3" />
              Mobile: &lt; 640px
            </Badge>
            <Badge variant="outline" className="text-[10px] font-mono gap-1">
              <Workflow className="h-3 w-3" />
              Tablet: 768px - 1024px
            </Badge>
            <Badge variant="outline" className="text-[10px] font-mono gap-1">
              <HardDrive className="h-3 w-3" />
              Desktop: 1440px+
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
