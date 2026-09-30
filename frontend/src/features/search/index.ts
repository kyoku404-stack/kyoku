/**
 * Search Feature Module
 * Hybrid dense vector & sparse keyword semantic search engine.
 */

export * from '@/types/search';
export { searchService } from '@/services/searchService';

export const SEARCH_FEATURE = {
  name: 'search',
  version: '1.2.0',
  description: 'Enterprise hybrid semantic vector and keyword search interface',
};
