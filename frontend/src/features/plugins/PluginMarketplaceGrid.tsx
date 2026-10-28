/**
 * KEEP Enterprise Platform — Extension Marketplace Grid.
 *
 * Phase: 3.5
 * Role: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  Download,
  Star,
  Check,
  ShieldCheck,
  Award,
  Users,
  Search,
  Sparkles,
  Link,
  GitBranch,
  Layers,
  BarChart2,
  Plus,
} from 'lucide-react';
import type { PluginMarketplaceItem, PluginCategory, PluginVerificationTier } from '@/types/plugin';

interface PluginMarketplaceGridProps {
  items: PluginMarketplaceItem[];
  loading: boolean;
  onInstallClick: (item: PluginMarketplaceItem) => void;
  onOpenPublish: () => void;
}

export const PluginMarketplaceGrid: React.FC<PluginMarketplaceGridProps> = ({
  items,
  loading,
  onInstallClick,
  onOpenPublish,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');

  const filteredItems = items.filter((item) => {
    const matchesSearch =
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.developer.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCat = selectedCategory === 'ALL' || item.category === selectedCategory;
    return matchesSearch && matchesCat;
  });

  const getTierBadge = (tier: PluginVerificationTier) => {
    switch (tier) {
      case 'CERTIFIED':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Award className="w-3 h-3" /> Certified Enterprise
          </span>
        );
      case 'VERIFIED':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <ShieldCheck className="w-3 h-3" /> Verified Partner
          </span>
        );
      case 'COMMUNITY':
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
            <Users className="w-3 h-3" /> Community
          </span>
        );
    }
  };

  const getCategoryIcon = (category: PluginCategory) => {
    switch (category) {
      case 'AI':
        return <Sparkles className="w-4 h-4 text-purple-400" />;
      case 'INTEGRATION':
        return <Link className="w-4 h-4 text-cyan-400" />;
      case 'WORKFLOW':
        return <GitBranch className="w-4 h-4 text-amber-400" />;
      case 'UI':
        return <Layers className="w-4 h-4 text-emerald-400" />;
      case 'ANALYTICS':
        return <BarChart2 className="w-4 h-4 text-blue-400" />;
    }
  };

  return (
    <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 backdrop-blur-md">
      {/* Header Controls */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-lg font-semibold text-white tracking-tight">Marketplace Catalog</h2>
          <p className="text-sm text-slate-400">
            Discover vetted LLM connectors, ERP adapters, and bidirectional workflow extensions.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Search */}
          <div className="relative flex-1 md:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search marketplace..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-950/70 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/50"
            />
          </div>

          {/* Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-slate-950/70 border border-slate-800 rounded-xl px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:border-indigo-500/50"
          >
            <option value="ALL">All Categories</option>
            <option value="AI">AI Engines</option>
            <option value="INTEGRATION">Integrations</option>
            <option value="WORKFLOW">Workflows</option>
            <option value="UI">UI Extensions</option>
            <option value="ANALYTICS">Analytics</option>
          </select>

          {/* Publish Extension CTA */}
          <button
            onClick={onOpenPublish}
            className="inline-flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-sm font-medium shadow-lg shadow-indigo-500/20 transition-all shrink-0"
          >
            <Plus className="w-4 h-4" /> Publish Extension
          </button>
        </div>
      </div>

      {/* Grid */}
      {loading && items.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 animate-pulse">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-64 bg-slate-800/30 rounded-xl border border-slate-800" />
          ))}
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="text-center py-12 border border-dashed border-slate-800 rounded-xl">
          <Layers className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-medium text-slate-300 mb-1">No matching extensions found</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Try adjusting your search criteria or register a new plugin package into the registry.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredItems.map((item) => (
            <div
              key={item.id}
              className="bg-slate-900/60 border border-slate-800 hover:border-slate-700 rounded-xl p-5 flex flex-col justify-between transition-all group hover:shadow-xl hover:shadow-indigo-500/5"
            >
              <div>
                {/* Header tier and category */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-1.5">
                    {getCategoryIcon(item.category)}
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      {item.category}
                    </span>
                  </div>
                  {getTierBadge(item.verification_tier)}
                </div>

                {/* Title & Author */}
                <div className="flex items-start gap-3 mb-2">
                  <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 font-bold shrink-0">
                    {item.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-white tracking-tight group-hover:text-indigo-400 transition-colors">
                      {item.name}
                    </h3>
                    <p className="text-xs text-slate-400">by {item.developer}</p>
                  </div>
                </div>

                {/* Description */}
                <p className="text-sm text-slate-400 line-clamp-3 mb-4 leading-relaxed">
                  {item.description}
                </p>

                {/* Metadata & Capabilities */}
                <div className="flex items-center gap-3 text-xs text-slate-400 mb-4 pb-4 border-b border-slate-800/80">
                  <span className="inline-flex items-center gap-1">
                    <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                    <span className="font-semibold text-slate-200">{item.rating.toFixed(1)}</span>
                  </span>
                  <span>•</span>
                  <span>{item.installs_count.toLocaleString()} installs</span>
                  <span>•</span>
                  <span className="font-mono">v{item.version}</span>
                </div>
              </div>

              {/* Install or Installed CTA */}
              <div className="pt-2">
                {item.is_installed ? (
                  <button
                    disabled
                    className="w-full py-2 px-3 bg-slate-800/60 border border-slate-700/60 rounded-xl text-slate-300 text-sm font-medium inline-flex items-center justify-center gap-2 cursor-default"
                  >
                    <Check className="w-4 h-4 text-emerald-400" /> Installed
                  </button>
                ) : (
                  <button
                    onClick={() => onInstallClick(item)}
                    className="w-full py-2 px-3 bg-indigo-600/90 hover:bg-indigo-600 border border-indigo-500/30 rounded-xl text-white text-sm font-medium inline-flex items-center justify-center gap-2 transition-colors shadow-md shadow-indigo-600/20"
                  >
                    <Download className="w-4 h-4" /> Install Extension
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
