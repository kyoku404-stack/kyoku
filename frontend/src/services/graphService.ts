/**
 * KEEP Enterprise Platform — Knowledge Graph API Client Service (Phase 2.4).
 * Implements communication with all Phase 2.4 REST endpoints:
 * - POST /api/v1/graph/build
 * - POST /api/v1/graph/update
 * - GET  /api/v1/graph/entity/:id
 * - GET  /api/v1/graph/relationships/:id
 * - POST /api/v1/graph/query
 * - GET  /api/v1/graph/explorer
 * - GET  /api/v1/graph/expertise
 * - GET  /api/v1/graph/impact/:entity_id
 *
 * Specification: docs/API/api-contract.md Section 11 & devdocs/p2/p2.4.txt
 * Author: Member 3 (Frontend Lead)
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  EntityRelationshipsResponse,
  EntityResponse,
  ExpertiseResponse,
  GraphBuildRequest,
  GraphBuildResponse,
  GraphExplorerResponse,
  GraphQueryRequest,
  GraphQueryResponse,
  GraphUpdateRequest,
  GraphUpdateResponse,
  ImpactAnalysisResponse,
} from '@/types/graph';

export const graphService = {
  /**
   * Trigger asynchronous or synchronous full knowledge graph construction.
   * POST /api/v1/graph/build
   */
  async buildGraph(payload: GraphBuildRequest = {}): Promise<ApiResponse<GraphBuildResponse>> {
    const response = await apiClient.post<ApiResponse<GraphBuildResponse>>(
      '/graph/build',
      payload
    );
    return response.data;
  },

  /**
   * Incrementally extract entities and relationships from text or document.
   * POST /api/v1/graph/update
   */
  async updateGraph(payload: GraphUpdateRequest): Promise<ApiResponse<GraphUpdateResponse>> {
    const response = await apiClient.post<ApiResponse<GraphUpdateResponse>>(
      '/graph/update',
      payload
    );
    return response.data;
  },

  /**
   * Retrieve node details and properties for an entity.
   * GET /api/v1/graph/entity/:id
   */
  async getEntity(id: string): Promise<ApiResponse<EntityResponse>> {
    const response = await apiClient.get<ApiResponse<EntityResponse>>(
      `/graph/entity/${id}`
    );
    return response.data;
  },

  /**
   * Retrieve directed neighborhood relationships for an entity.
   * GET /api/v1/graph/relationships/:id
   */
  async getEntityRelationships(id: string): Promise<ApiResponse<EntityRelationshipsResponse>> {
    const response = await apiClient.get<ApiResponse<EntityRelationshipsResponse>>(
      `/graph/relationships/${id}`
    );
    return response.data;
  },

  /**
   * Execute multi-hop graph traversal with cycle prevention.
   * POST /api/v1/graph/query
   */
  async queryGraph(payload: GraphQueryRequest): Promise<ApiResponse<GraphQueryResponse>> {
    const response = await apiClient.post<ApiResponse<GraphQueryResponse>>(
      '/graph/query',
      payload
    );
    return response.data;
  },

  /**
   * Fetch nodes, links, and topological metrics for canvas visualization.
   * GET /api/v1/graph/explorer
   */
  async getExplorerData(
    entityType?: string,
    limit: number = 100
  ): Promise<ApiResponse<GraphExplorerResponse>> {
    const response = await apiClient.get<ApiResponse<GraphExplorerResponse>>(
      '/graph/explorer',
      {
        params: {
          entity_type: entityType || undefined,
          limit,
        },
      }
    );
    return response.data;
  },

  /**
   * Rank subject-matter experts for a given topic or competency.
   * GET /api/v1/graph/expertise
   */
  async getExpertise(topic: string, limit: number = 5): Promise<ApiResponse<ExpertiseResponse>> {
    const response = await apiClient.get<ApiResponse<ExpertiseResponse>>(
      '/graph/expertise',
      {
        params: {
          topic,
          limit,
        },
      }
    );
    return response.data;
  },

  /**
   * Calculate downstream blast radius and affected dependencies.
   * GET /api/v1/graph/impact/:entity_id
   */
  async getImpact(
    entityId: string,
    maxDepth: number = 3
  ): Promise<ApiResponse<ImpactAnalysisResponse>> {
    const response = await apiClient.get<ApiResponse<ImpactAnalysisResponse>>(
      `/graph/impact/${entityId}`,
      {
        params: {
          max_depth: maxDepth,
        },
      }
    );
    return response.data;
  },
};
