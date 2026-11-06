/**
 * KEEP Enterprise Platform — Phase 3.7 Sponsor Demonstration Showcase Launcher.
 *
 * Interactive demo showcase guiding project sponsors, stakeholders, and evaluators
 * through the 6 signature enterprise pillars of the KEEP platform.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  Bot,
  Layers,
  Network,
  Puzzle,
  Share2,
  Sparkles,
} from 'lucide-react';
import { PATHS } from '@/routes/paths';

interface DemoPillar {
  title: string;
  category: string;
  description: string;
  route: string;
  icon: React.ReactNode;
  badge: string;
}

export const SponsorDemoLauncher: React.FC = () => {
  const navigate = useNavigate();

  const demoPillars: DemoPillar[] = [
    {
      title: 'Multi-Tenant RAG & Semantic Search',
      category: 'Phase 2.2 / Phase 3.1',
      description: 'Hybrid BM25 + dense embedding vector search with organization-level security boundaries and pgvector indexing.',
      route: PATHS.DOCUMENTS,
      icon: <Layers className="w-5 h-5 text-indigo-500" />,
      badge: 'RAG Core',
    },
    {
      title: 'Enterprise AI Assistant & Citations',
      category: 'Phase 2.3 / Phase 2.4',
      description: 'Multi-turn context-aware assistant with streaming tokens, citation attribution cards, and conversation branching.',
      route: PATHS.ASSISTANT,
      icon: <Bot className="w-5 h-5 text-purple-500" />,
      badge: 'Streaming AI',
    },
    {
      title: 'Interactive Knowledge Graph Explorer',
      category: 'Phase 2.5',
      description: 'Force-directed graph visualization revealing enterprise entity relationships, document co-occurrences, and graph RAG paths.',
      route: PATHS.KNOWLEDGE_GRAPH,
      icon: <Network className="w-5 h-5 text-teal-500" />,
      badge: 'Graph AI',
    },
    {
      title: 'Real-Time Multi-User Collaboration',
      category: 'Phase 3.2',
      description: 'Live presence tracking, multi-user document comments, threaded discussions, and collaborative versioning.',
      route: PATHS.COLLABORATION,
      icon: <Share2 className="w-5 h-5 text-amber-500" />,
      badge: 'WebSockets',
    },
    {
      title: 'Sandboxed Plugin & Tool Marketplace',
      category: 'Phase 3.5',
      description: 'Extensible plugin architecture with capability grants, AST safety isolation, and community catalog management.',
      route: PATHS.PLUGINS,
      icon: <Puzzle className="w-5 h-5 text-rose-500" />,
      badge: 'Plugin SDK',
    },
    {
      title: 'Observability & High-Availability Operations',
      category: 'Phase 3.6',
      description: 'Real-time Prometheus telemetry, live log stream, multi-tier cache administration, and automated disaster recovery.',
      route: PATHS.SYSTEM,
      icon: <Activity className="w-5 h-5 text-emerald-500" />,
      badge: 'Infrastructure',
    },
  ];

  return (
    <div className="bg-gradient-to-br from-indigo-900 via-indigo-950 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden border border-indigo-700/50 space-y-6">
      {/* Background Decorative Glow */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl -z-10 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl -z-10 pointer-events-none" />

      {/* Hero Header */}
      <div className="max-w-3xl space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-indigo-500/20 text-indigo-300 border border-indigo-400/30">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          Sponsor Demonstration Showcase (v1.0.0 Production Release)
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
          KEEP Enterprise Platform Architectural Showcase
        </h2>
        <p className="text-sm text-indigo-200/80 leading-relaxed">
          Welcome to the comprehensive sponsor demonstration suite. Explore the end-to-end capabilities spanning our 4-tier architecture, production-grade AI stack, and high-availability operations.
        </p>
      </div>

      {/* Grid of 6 Demonstration Tracks */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
        {demoPillars.map((pillar) => (
          <div
            key={pillar.title}
            onClick={() => navigate(pillar.route)}
            className="group cursor-pointer bg-white/5 hover:bg-white/10 border border-white/10 hover:border-indigo-400/50 rounded-xl p-5 transition-all duration-200 flex flex-col justify-between space-y-4 hover:shadow-lg"
          >
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <div className="p-2.5 bg-white/10 rounded-lg group-hover:scale-105 transition-transform">
                  {pillar.icon}
                </div>
                <span className="text-2xs font-semibold px-2 py-0.5 rounded-full bg-white/10 text-indigo-200 border border-white/10">
                  {pillar.badge}
                </span>
              </div>

              <div>
                <span className="text-3xs font-mono text-indigo-300 uppercase tracking-widest block">
                  {pillar.category}
                </span>
                <h3 className="text-base font-bold text-white group-hover:text-indigo-300 transition-colors mt-0.5">
                  {pillar.title}
                </h3>
              </div>

              <p className="text-xs text-gray-300 leading-normal line-clamp-3">
                {pillar.description}
              </p>
            </div>

            <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-300 group-hover:text-indigo-200 pt-2 border-t border-white/5">
              <span>Launch Track Demo</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
