/**
 * KEEP Enterprise Platform — Search Service Client.
 * Connects to /api/v1/search endpoints.
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type { HybridSearchRequest, SearchResponse } from '@/types/search';

export const searchService = {
  /**
   * Executes hybrid vector + BM25 keyword search.
   * POST /api/v1/search/hybrid
   */
  async hybridSearch(request: HybridSearchRequest): Promise<ApiResponse<SearchResponse>> {
    const response = await apiClient.post<ApiResponse<SearchResponse>>(
      '/search/hybrid',
      request
    );
    return response.data;
  },
};

export default searchService;
