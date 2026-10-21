/**
 * Document Management Feature Module — Phase 1.8
 * Upload, explore, preview, and manage enterprise documents.
 */

export { DocumentUploadModal } from './DocumentUploadModal';
export { DocumentPreviewModal } from './DocumentPreviewModal';
export { VersionHistoryTimeline } from './VersionHistoryTimeline';
export { DocumentExplorer } from './DocumentExplorer';

export * from '@/types/document';
export { documentService } from '@/services/documentService';

export const UPLOAD_FEATURE = {
  name: 'upload',
  version: '1.8.0',
  description: 'Enterprise document management: upload, organize, preview, version, and AI-ready ingestion',
};
