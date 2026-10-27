/**
 * KEEP Enterprise Platform — Knowledge Graph & Enterprise Intelligence Master Page (Phase 2.4).
 *
 * Integrated enterprise intelligence center providing topological network exploration,
 * multi-hop graph queries, downstream blast radius impact analysis, and subject-matter
 * expertise discovery.
 *
 * Specification: docs/API/api-contract.md Section 11 & devdocs/p2/p2.4.txt
 * Author: Member 3 (Frontend Lead)
 */

import React, { useState } from 'react';
import { useKnowledgeGraph } from '@/hooks/useKnowledgeGraph';
import {
  GraphMetricsBanner,
  GraphFilterBar,
  KnowledgeExplorer,
  EntityDetailPanel,
  ImpactAnalysisWidget,
  ExpertiseDirectory,
} from '@/features/graph';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Network,
  Share2,
  AlertTriangle,
  Award,
  Sparkles,
  Info,
} from 'lucide-react';

export const KnowledgeGraphPage: React.FC = () => {
  const {
    explorerData,
    selectedEntityId,
    entityDetails,
    entityRelationships,
    impactResult,
    expertiseResult,
    lastBuildReport,
    filters,
    isLoading,
    isBuilding,
    isDetailLoading,
    isImpactLoading,
    isExpertiseLoading,
    error,
    loadExplorerData,
    selectEntity,
    analyzeImpact,
    discoverExpertise,
    triggerBuild,
    triggerUpdate,
    setFilters,
  } = useKnowledgeGraph({ autoLoadExplorer: true });

  const [activeTab, setActiveTab] = useState<'EXPLORER' | 'IMPACT' | 'EXPERTISE'>('EXPLORER');

  const handleImpactFromDetail = (entityId: string) => {
    setActiveTab('IMPACT');
    analyzeImpact(entityId);
  };

  return (
    <div className="flex flex-col gap-5 p-6 max-w-7xl mx-auto w-full min-h-[calc(100vh-4rem)]" data-testid="knowledge-graph-page">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400">
              <Network className="h-5 w-5" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Knowledge Graph & Enterprise Intelligence
            </h1>
            <Badge variant="secondary" className="text-xs font-semibold px-2 py-0.5 bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20">
              Phase 2.4
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Constructed semantic relational network mapping organizational hierarchies, operational initiatives, document triples, and subject-matter expertise.
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-1 shadow-xs">
          <Button
            variant={activeTab === 'EXPLORER' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setActiveTab('EXPLORER')}
            className="h-8 gap-1.5 text-xs font-semibold"
            data-testid="tab-explorer"
          >
            <Share2 className="h-3.5 w-3.5" />
            Topology Explorer
          </Button>

          <Button
            variant={activeTab === 'IMPACT' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => {
              setActiveTab('IMPACT');
              if (selectedEntityId && !impactResult) {
                analyzeImpact(selectedEntityId);
              }
            }}
            className="h-8 gap-1.5 text-xs font-semibold"
            data-testid="tab-impact"
          >
            <AlertTriangle className="h-3.5 w-3.5" />
            Impact Analysis
          </Button>

          <Button
            variant={activeTab === 'EXPERTISE' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => {
              setActiveTab('EXPERTISE');
              if (!expertiseResult) {
                discoverExpertise('Intelligence');
              }
            }}
            className="h-8 gap-1.5 text-xs font-semibold"
            data-testid="tab-expertise"
          >
            <Award className="h-3.5 w-3.5" />
            Expertise Discovery
          </Button>
        </div>
      </div>

      {/* Error Alert Banner */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg border border-rose-500/30 bg-rose-500/10 text-rose-600 dark:text-rose-400 text-xs font-medium">
          <Info className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Build Feedback Toast/Banner */}
      {lastBuildReport && (
        <div className="flex items-center justify-between p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 text-xs">
          <span className="flex items-center gap-1.5">
            <Sparkles className="h-4 w-4 text-emerald-500" />
            Knowledge Graph rebuild complete: <strong>{lastBuildReport.entities_created}</strong> entities created,{' '}
            <strong>{lastBuildReport.relationships_created}</strong> relationships indexed in{' '}
            <strong>{lastBuildReport.duration_seconds}s</strong>.
          </span>
          <span className="font-semibold text-[11px]">Total: {lastBuildReport.total_entities} Nodes</span>
        </div>
      )}

      {/* Executive Topology Metrics */}
      <GraphMetricsBanner metrics={explorerData?.metrics || null} loading={isLoading} />

      {/* Filter and Ingestion Bar */}
      <GraphFilterBar
        filters={filters}
        onFilterChange={setFilters}
        onRefresh={() => loadExplorerData(filters.selectedEntityType)}
        onTriggerBuild={triggerBuild}
        onTriggerUpdate={triggerUpdate}
        isBuilding={isBuilding}
      />

      {/* Tab 1: Topology Explorer View */}
      {activeTab === 'EXPLORER' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          <div className={selectedEntityId ? 'lg:col-span-8' : 'lg:col-span-12'}>
            <KnowledgeExplorer
              nodes={explorerData?.nodes || []}
              links={explorerData?.links || []}
              selectedEntityId={selectedEntityId}
              onSelectEntity={selectEntity}
              searchQuery={filters.searchQuery}
              selectedEntityType={filters.selectedEntityType}
              loading={isLoading}
            />
          </div>

          {/* Side Drawer when an entity is selected */}
          {selectedEntityId && (
            <div className="lg:col-span-4 h-[560px]">
              <EntityDetailPanel
                entity={entityDetails}
                relationships={entityRelationships}
                onClose={() => selectEntity(null)}
                onAnalyzeImpact={handleImpactFromDetail}
                onSelectConnectedEntity={selectEntity}
                loading={isDetailLoading}
              />
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Impact Analysis View */}
      {activeTab === 'IMPACT' && (
        <div className="space-y-4">
          <ImpactAnalysisWidget
            impact={impactResult}
            onClose={() => setActiveTab('EXPLORER')}
            loading={isImpactLoading}
          />

          {!impactResult && (
            <div className="p-8 text-center rounded-xl border border-border bg-card text-xs text-muted-foreground">
              Select an entity from the Topology Explorer tab to compute its downstream blast radius, or click &ldquo;Analyze Impact&rdquo; inside the Entity Inspector.
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Expertise Discovery View */}
      {activeTab === 'EXPERTISE' && (
        <div>
          <ExpertiseDirectory
            expertise={expertiseResult}
            onSearchTopic={discoverExpertise}
            loading={isExpertiseLoading}
          />
        </div>
      )}
    </div>
  );
};
export default KnowledgeGraphPage;
