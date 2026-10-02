/**
 * KEEP Enterprise Platform — Document Ingestion Service Client.
 * Connects to /api/v1/documents endpoints.
 */

import { apiClient } from './api';
import type { ApiResponse, PaginatedData } from '@/types/api';
import type {
  DocumentListParams,
  DocumentResponse,
  DocumentUploadResponse,
} from '@/types/document';

export const documentService = {
  /**
   * Upload a corporate document (PDF, DOCX, TXT, PNG, JPG) to trigger asynchronous ingestion.
   * POST /api/v1/documents/upload
   */
  async uploadDocument(
    file: File,
    title?: string,
    tags?: string
  ): Promise<ApiResponse<DocumentUploadResponse>> {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    if (tags) formData.append('tags', tags);

    const response = await apiClient.post<ApiResponse<DocumentUploadResponse>>(
      '/documents/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * Retrieves paginated documents from the repository.
   * GET /api/v1/documents
   */
  async listDocuments(
    params?: DocumentListParams
  ): Promise<ApiResponse<PaginatedData<DocumentResponse>>> {
    const response = await apiClient.get<ApiResponse<PaginatedData<DocumentResponse>>>(
      '/documents',
      { params }
    );
    return response.data;
  },
};

export default documentService;
