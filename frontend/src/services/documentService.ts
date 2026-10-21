/**
 * KEEP Enterprise Platform — Document Management Service Client.
 * Phase 1.8: Document Upload, File Management & Storage System.
 * Connects to all 8 /api/v1/documents/* endpoints.
 */

import { apiClient } from './api';
import type { ApiResponse, PaginatedData } from '@/types/api';
import type {
  DocumentListParams,
  DocumentItem,
  DocumentDetail,
  DocumentUploadResponse,
  DocumentUpdatePayload,
  DocumentUpdateResponse,
  DocumentVersionUploadResponse,
  DocumentDeleteResponse,
  DocumentCategory,
} from '@/types/document';

export const documentService = {
  /**
   * Upload a document (PDF, DOCX, PPTX, XLSX, TXT, MD, CSV, PNG, JPG, WEBP).
   * POST /api/v1/documents/upload → 202 Accepted (async processing).
   */
  async uploadDocument(
    file: File,
    options?: {
      title?: string;
      description?: string;
      category?: DocumentCategory;
      tags?: string[];
      project_id?: string;
    }
  ): Promise<ApiResponse<DocumentUploadResponse>> {
    const formData = new FormData();
    formData.append('file', file);
    if (options?.title) formData.append('title', options.title);
    if (options?.description) formData.append('description', options.description);
    if (options?.category) formData.append('category', options.category);
    if (options?.tags?.length) formData.append('tags', options.tags.join(','));
    if (options?.project_id) formData.append('project_id', options.project_id);

    const response = await apiClient.post<ApiResponse<DocumentUploadResponse>>(
      '/documents/upload',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        // Progress tracking available via onUploadProgress
      }
    );
    return response.data;
  },

  /**
   * List documents with filters and pagination.
   * GET /api/v1/documents → 200 OK (PaginatedData<DocumentItem>).
   */
  async listDocuments(
    params?: DocumentListParams
  ): Promise<ApiResponse<PaginatedData<DocumentItem>>> {
    const response = await apiClient.get<ApiResponse<PaginatedData<DocumentItem>>>(
      '/documents',
      { params }
    );
    return response.data;
  },

  /**
   * Retrieve full document metadata including version history.
   * GET /api/v1/documents/{id} → 200 OK (DocumentDetail).
   */
  async getDocumentDetail(id: string): Promise<ApiResponse<DocumentDetail>> {
    const response = await apiClient.get<ApiResponse<DocumentDetail>>(
      `/documents/${id}`
    );
    return response.data;
  },

  /**
   * Get the download URL for a document (triggers browser download).
   * GET /api/v1/documents/{id}/download
   * Returns the full URL for streaming download.
   */
  getDownloadUrl(id: string): string {
    const base = (import.meta.env.VITE_API_BASE_URL as string) || '/api/v1';
    return `${base}/documents/${id}/download`;
  },

  /**
   * Trigger a file download programmatically.
   */
  async downloadDocument(id: string, filename: string): Promise<void> {
    const response = await apiClient.get(`/documents/${id}/download`, {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data as BlobPart]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  /**
   * Get preview URL for inline rendering (PDF viewer, image, text).
   * GET /api/v1/documents/{id}/preview
   */
  getPreviewUrl(id: string): string {
    const base = (import.meta.env.VITE_API_BASE_URL as string) || '/api/v1';
    return `${base}/documents/${id}/preview`;
  },

  /**
   * Update document metadata (title, description, category, tags, project_id).
   * PATCH /api/v1/documents/{id} → 200 OK.
   */
  async updateMetadata(
    id: string,
    payload: DocumentUpdatePayload
  ): Promise<ApiResponse<DocumentUpdateResponse>> {
    const response = await apiClient.patch<ApiResponse<DocumentUpdateResponse>>(
      `/documents/${id}`,
      payload
    );
    return response.data;
  },

  /**
   * Upload a new version of an existing document.
   * POST /api/v1/documents/{id}/version → 201 Created.
   */
  async uploadNewVersion(
    id: string,
    file: File,
    changeNotes?: string
  ): Promise<ApiResponse<DocumentVersionUploadResponse>> {
    const formData = new FormData();
    formData.append('file', file);
    if (changeNotes) formData.append('change_notes', changeNotes);

    const response = await apiClient.post<ApiResponse<DocumentVersionUploadResponse>>(
      `/documents/${id}/version`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return response.data;
  },

  /**
   * Soft-delete or archive a document.
   * DELETE /api/v1/documents/{id}?action=delete|archive → 200 OK.
   */
  async deleteDocument(
    id: string,
    action: 'delete' | 'archive' = 'delete'
  ): Promise<ApiResponse<DocumentDeleteResponse>> {
    const response = await apiClient.delete<ApiResponse<DocumentDeleteResponse>>(
      `/documents/${id}`,
      { params: { action } }
    );
    return response.data;
  },
};

export default documentService;
