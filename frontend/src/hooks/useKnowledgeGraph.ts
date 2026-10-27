/**
 * Phase 2.4 Knowledge Graph & Enterprise Intelligence Custom React Hook.
 * Manages topological graph state, node selection, impact analysis,
 * subject-matter expertise discovery, traversal queries, and background builds.
 *
 * Specification: docs/API/api-contract.md Section 11 & devdocs/p2/p2.4.txt
 * Author: Member 3 (Frontend Lead)
 */

import { useState, useCallback, useEffect } from 'react';
import { graphService } from '@/services/graphService';
import type {
  EntityRelationshipsResponse,
  EntityResponse,
  ExpertiseResponse,
  GraphBuildRequest,
  GraphBuildResponse,
  GraphExplorerResponse,
  GraphFilterState,
  GraphQueryResponse,
  GraphUpdateRequest,
  ImpactAnalysisResponse,
} from '@/types/graph';

export interface UseKnowledgeGraphOptions {
  autoLoadExplorer?: boolean;
  initialEntityType?: string;
  initialLimit?: number;
}

export function useKnowledgeGraph(options: UseKnowledgeGraphOptions = {}) {
  const { autoLoadExplorer = true, initialEntityType, initialLimit = 100 } = options;

  // Main canvas topology
  const [explorerData, setExplorerData] = useState<GraphExplorerResponse | null>(null);

  // Inspector & detail drawer
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);
  const [entityDetails, setEntityDetails] = useState<EntityResponse | null>(null);
  const [entityRelationships, setEntityRelationships] = useState<EntityRelationshipsResponse | null>(null);

  // Enterprise intelligence views
  const [impactResult, setImpactResult] = useState<ImpactAnalysisResponse | null>(null);
  const [expertiseResult, setExpertiseResult] = useState<ExpertiseResponse | null>(null);
  const [traversalResult, setTraversalResult] = useState<GraphQueryResponse | null>(null);
  const [lastBuildReport, setLastBuildReport] = useState<GraphBuildResponse | null>(null);

  // Filters & Controls
  const [filters, setFilters] = useState<GraphFilterState>({
    searchQuery: '',
    selectedEntityType: initialEntityType || 'ALL',
    maxDepth: 2,
    showOrphans: true,
  });

  // Loading & Error States
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isBuilding, setIsBuilding] = useState<boolean>(false);
  const [isDetailLoading, setIsDetailLoading] = useState<boolean>(false);
  const [isImpactLoading, setIsImpactLoading] = useState<boolean>(false);
  const [isExpertiseLoading, setIsExpertiseLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch Knowledge Explorer topology and metrics.
   */
  const loadExplorerData = useCallback(async (typeFilter?: string, limit: number = initialLimit) => {
    setIsLoading(true);
    setError(null);
    try {
      const filterType = typeFilter && typeFilter !== 'ALL' ? typeFilter : undefined;
      const resp = await graphService.getExplorerData(filterType, limit);
      if (resp.success && resp.data) {
        setExplorerData(resp.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load graph explorer topology';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [initialLimit]);

  /**
   * Select a node and fetch both entity details and its immediate directed relationships.
   */
  const selectEntity = useCallback(async (entityId: string | null) => {
    setSelectedEntityId(entityId);
    if (!entityId) {
      setEntityDetails(null);
      setEntityRelationships(null);
      return;
    }

    setIsDetailLoading(true);
    setError(null);
    try {
      const [detailResp, relsResp] = await Promise.all([
        graphService.getEntity(entityId),
        graphService.getEntityRelationships(entityId),
      ]);
      if (detailResp.success) {
        setEntityDetails(detailResp.data);
      }
      if (relsResp.success) {
        setEntityRelationships(relsResp.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve entity inspection details';
      setError(msg);
    } finally {
      setIsDetailLoading(false);
    }
  }, []);

  /**
   * Run recursive blast radius impact analysis on a target entity.
   */
  const analyzeImpact = useCallback(async (entityId: string, depth: number = 3) => {
    setIsImpactLoading(true);
    setError(null);
    try {
      const resp = await graphService.getImpact(entityId, depth);
      if (resp.success && resp.data) {
        setImpactResult(resp.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to run impact analysis';
      setError(msg);
    } finally {
      setIsImpactLoading(false);
    }
  }, []);

  /**
   * Discover subject-matter expertise for a topic.
   */
  const discoverExpertise = useCallback(async (topic: string, limit: number = 5) => {
    if (!topic.trim()) return;
    setIsExpertiseLoading(true);
    setError(null);
    try {
      const resp = await graphService.getExpertise(topic.trim(), limit);
      if (resp.success && resp.data) {
        setExpertiseResult(resp.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to discover expertise';
      setError(msg);
    } finally {
      setIsExpertiseLoading(false);
    }
  }, []);

  /**
   * Multi-hop breadth-first graph traversal from a start node.
   */
  const runTraversal = useCallback(async (startEntityId: string, maxDepth: number = 2) => {
    setIsLoading(true);
    setError(null);
    try {
      const resp = await graphService.queryGraph({
        start_entity_id: startEntityId,
        max_depth: maxDepth,
      });
      if (resp.success && resp.data) {
        setTraversalResult(resp.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Traversal query failed';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Trigger graph build or rebuild.
   */
  const triggerBuild = useCallback(async (rebuildAll: boolean = false) => {
    setIsBuilding(true);
    setError(null);
    try {
      const buildPayload: GraphBuildRequest = {
        rebuild_all: rebuildAll,
        confidence_threshold: 0.70,
        include_documents: true,
        include_organizational: true,
      };
      const resp = await graphService.buildGraph(buildPayload);
      if (resp.success && resp.data) {
        setLastBuildReport(resp.data);
        // Refresh explorer
        await loadExplorerData(filters.selectedEntityType);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Knowledge graph build failed';
      setError(msg);
    } finally {
      setIsBuilding(false);
    }
  }, [filters.selectedEntityType, loadExplorerData]);

  /**
   * Incrementally update graph with unstructured text or document chunk.
   */
  const triggerUpdate = useCallback(async (textContent: string, documentId?: string) => {
    setIsBuilding(true);
    setError(null);
    try {
      const updatePayload: GraphUpdateRequest = {
        text_content: textContent,
        document_id: documentId,
      };
      const resp = await graphService.updateGraph(updatePayload);
      if (resp.success) {
        await loadExplorerData(filters.selectedEntityType);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Incremental graph update failed';
      setError(msg);
    } finally {
      setIsBuilding(false);
    }
  }, [filters.selectedEntityType, loadExplorerData]);

  // Initial load
  useEffect(() => {
    if (autoLoadExplorer) {
      loadExplorerData();
    }
  }, [autoLoadExplorer, loadExplorerData]);

  return {
    // Data states
    explorerData,
    selectedEntityId,
    entityDetails,
    entityRelationships,
    impactResult,
    expertiseResult,
    traversalResult,
    lastBuildReport,
    filters,

    // Loading & Error states
    isLoading,
    isBuilding,
    isDetailLoading,
    isImpactLoading,
    isExpertiseLoading,
    error,

    // Actions
    loadExplorerData,
    selectEntity,
    analyzeImpact,
    discoverExpertise,
    runTraversal,
    triggerBuild,
    triggerUpdate,
    setFilters,
  };
}
