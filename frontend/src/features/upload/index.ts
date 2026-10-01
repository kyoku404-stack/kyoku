/**
 * Document Ingestion & Upload Feature Module
 * Multimodal document processing, OCR, chunking, and metadata management.
 */

export * from '@/types/document';
export { documentService } from '@/services/documentService';

export const UPLOAD_FEATURE = {
  name: 'upload',
  version: '1.2.0',
  description: 'Enterprise document ingestion, multipart upload, and OCR status',
};
