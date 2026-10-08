/**
 * KEEP Enterprise Platform — Knowledge Graph API Client Service.
 * Connects frontend graph visualizers to backend `kg_entities` and `kg_relationships` endpoints.
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  KgQueryRequest,
  KgQueryResponse,
  KgEntity,
  KgRelationship,
} from '@/types/knowledge';

export const knowledgeService = {
  /**
   * Execute semantic Knowledge Graph traversal query.
   */
  async queryGraph(request: KgQueryRequest): Promise<ApiResponse<KgQueryResponse>> {
    const response = await apiClient.post<ApiResponse<KgQueryResponse>>(
      '/graph/query',
      request
    );
    return response.data;
  },

  /**
   * List extracted knowledge entities.
   */
  async listEntities(): Promise<ApiResponse<KgEntity[]>> {
    const response = await apiClient.get<ApiResponse<KgEntity[]>>('/graph/entities');
    return response.data;
  },

  /**
   * List relationship edges.
   */
  async listRelationships(): Promise<ApiResponse<KgRelationship[]>> {
    const response = await apiClient.get<ApiResponse<KgRelationship[]>>(
      '/graph/relationships'
    );
    return response.data;
  },
};
