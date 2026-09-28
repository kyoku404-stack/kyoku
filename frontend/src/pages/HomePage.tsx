import React from 'react';
import { Link } from 'react-router-dom';
import { ROUTES } from '@/routes/paths';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Search,
  Sparkles,
  Network,
  Shield,
  ArrowRight,
  Activity,
  CheckCircle2,
} from 'lucide-react';

export const HomePage: React.FC = () => {
  return (
    <div className="space-y-12 max-w-6xl mx-auto py-6">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-2xl border border-border bg-gradient-to-b from-card/80 to-muted/20 p-8 sm:p-12 shadow-sm">
        <div className="relative z-10 max-w-3xl space-y-6">
          <Badge variant="processing" className="px-3 py-1">
            Phase 1.1 Development Baseline
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-foreground">
            Knowledge Extraction & Enterprise Platform
          </h1>
          <p className="text-lg text-muted-foreground leading-relaxed">
            KEEP unifies fragmented corporate knowledge—documents, communications, meetings, and relational data—into an interconnected semantic network powered by Hybrid RAG and Knowledge Graphs.
          </p>
          <div className="flex flex-wrap items-center gap-4 pt-2">
            <Link to={ROUTES.HEALTH}>
              <Button size="lg" className="shadow-md">
                <Activity className="mr-2 h-5 w-5" />
                Inspect Engine Health
              </Button>
            </Link>
            <Link to={ROUTES.LOGIN}>
              <Button variant="outline" size="lg">
                Enter Platform
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>

        {/* Ambient subtle glow */}
        <div className="absolute -right-20 -top-20 h-72 w-72 rounded-full bg-primary/10 blur-3xl pointer-events-none" />
      </section>

      {/* Feature Pillar Cards */}
      <section className="space-y-6">
        <div className="space-y-1 text-center sm:text-left">
          <h2 className="text-2xl font-bold tracking-tight text-foreground">
            Enterprise Intelligence Architecture
          </h2>
          <p className="text-sm text-muted-foreground">
            Four foundational capabilities engineered for zero hallucination and complete auditability.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="hover:shadow-md transition-shadow">
            <CardHeader className="space-y-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-500/10 text-sky-600 dark:text-sky-400">
                <Search className="h-5 w-5" />
              </div>
              <CardTitle className="text-base">Hybrid Search</CardTitle>
              <CardDescription>
                Dense cosine vector search combined with sparse BM25 ranking and Reciprocal Rank Fusion.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="hover:shadow-md transition-shadow">
            <CardHeader className="space-y-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-500/10 text-violet-600 dark:text-violet-400">
                <Sparkles className="h-5 w-5" />
              </div>
              <CardTitle className="text-base">Citation RAG</CardTitle>
              <CardDescription>
                Accurate, citation-backed answers with strict source provenance tags [Doc X, Page Y].
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="hover:shadow-md transition-shadow">
            <CardHeader className="space-y-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                <Network className="h-5 w-5" />
              </div>
              <CardTitle className="text-base">Knowledge Graph</CardTitle>
              <CardDescription>
                Discovers hidden cross-departmental relationships between projects, teams, and documents.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="hover:shadow-md transition-shadow">
            <CardHeader className="space-y-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-rose-500/10 text-rose-600 dark:text-rose-400">
                <Shield className="h-5 w-5" />
              </div>
              <CardTitle className="text-base">Zero-Trust Isolation</CardTitle>
              <CardDescription>
                Multi-tenant organization boundary isolation and fine-grained RBAC authorization.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>

      {/* System Status Banner */}
      <section className="rounded-xl border border-border bg-card p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Phase 1.1 Initialization Complete</h3>
              <p className="text-sm text-muted-foreground">
                FastAPI Backend (Port 8000) &bull; React Vite Frontend (Port 3000) &bull; PostgreSQL 16
              </p>
            </div>
          </div>
          <Link to={ROUTES.HEALTH}>
            <Button variant="outline" size="sm">
              Live Health Telemetry
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
};
