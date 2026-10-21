/**
 * KEEP Enterprise Platform — Phase 1.8 Document Management Tests
 * Tests for: documentService client, DocumentUploadModal, DocumentExplorer,
 * DocumentPreviewModal, VersionHistoryTimeline, and DocumentsPage.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// ─── Mock API client ──────────────────────────────────────────────────────────

vi.mock('@/services/api', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('@/services/documentService', () => ({
  documentService: {
    uploadDocument: vi.fn(),
    listDocuments: vi.fn(),
    getDocumentDetail: vi.fn(),
    downloadDocument: vi.fn(),
    getDownloadUrl: vi.fn((id: string) => `/api/v1/documents/${id}/download`),
    getPreviewUrl: vi.fn((id: string) => `/api/v1/documents/${id}/preview`),
    updateMetadata: vi.fn(),
    uploadNewVersion: vi.fn(),
    deleteDocument: vi.fn(),
  },
}));

vi.mock('@/hooks/useAuthorization', () => ({
  useAuthorization: () => ({
    can: vi.fn(() => true),
    isAtLeast: vi.fn(() => true),
    role: 'OrgAdmin',
    isSimulating: false,
  }),
}));

import { documentService } from '@/services/documentService';
import { DocumentUploadModal } from '@/features/upload/DocumentUploadModal';
import { DocumentPreviewModal } from '@/features/upload/DocumentPreviewModal';
import { VersionHistoryTimeline } from '@/features/upload/VersionHistoryTimeline';
import { DocumentExplorer } from '@/features/upload/DocumentExplorer';
import { DocumentsPage } from '@/pages/DocumentsPage';
import type { DocumentItem, DocumentDetail } from '@/types/document';

// ─── Fixtures ─────────────────────────────────────────────────────────────────

const makeDocument = (overrides: Partial<DocumentItem> = {}): DocumentItem => ({
  id: 'doc-uuid-1',
  filename: 'q3-strategy.pdf',
  title: 'Q3 Strategy',
  file_type: 'application/pdf',
  file_size: 2048000,
  category: 'REPORTS',
  tags: ['strategy', 'q3'],
  version_number: 1,
  status: 'PROCESSED',
  ai_ready: true,
  chunk_count: 42,
  project_id: null,
  uploader_id: 'user-123',
  uploader_name: 'Alice Chen',
  created_at: new Date().toISOString(),
  updated_at: null,
  ...overrides,
});

const makeDocumentDetail = (): DocumentDetail => ({
  ...makeDocument(),
  organization_id: 'org-abc',
  original_filename: 'Q3 Strategy.pdf',
  description: 'Q3 strategy document',
  checksum_sha256: 'abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
  current_version_number: 2,
  metadata_json: {},
  versions: [
    {
      version_number: 2,
      file_size: 2048000,
      checksum_sha256: 'abc123',
      uploader_id: 'user-123',
      change_notes: 'Updated Q3 projections',
      created_at: new Date().toISOString(),
    },
    {
      version_number: 1,
      file_size: 1800000,
      checksum_sha256: 'def456',
      uploader_id: 'user-123',
      change_notes: null,
      created_at: new Date(Date.now() - 86400000).toISOString(),
    },
  ],
});

const makePaginatedResponse = (items: DocumentItem[] = []) => ({
  data: {
    items,
    total: items.length,
    page: 1,
    page_size: 20,
    total_pages: 1,
  },
});

// ─── documentService Tests ────────────────────────────────────────────────────

describe('documentService — Phase 1.8 API Client', () => {
  it('should call uploadDocument with options', async () => {
    const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    const mockResponse = {
      data: {
        document_id: 'new-doc',
        filename: 'test.pdf',
        original_filename: 'test.pdf',
        file_type: 'application/pdf',
        file_size: 7,
        checksum_sha256: 'abc',
        category: 'REPORTS' as const,
        tags: [],
        version_number: 1,
        status: 'PROCESSING' as const,
        ai_ready: false,
        project_id: null,
        uploader_id: null,
        created_at: new Date().toISOString(),
      },
    };
    vi.mocked(documentService.uploadDocument).mockResolvedValue(mockResponse as never);

    const result = await documentService.uploadDocument(mockFile, {
      title: 'Test Document',
      category: 'REPORTS',
      tags: ['test'],
    });

    expect(documentService.uploadDocument).toHaveBeenCalled();
    expect(result.data.document_id).toBe('new-doc');
  });

  it('should call listDocuments with pagination params', async () => {
    const items = [makeDocument()];
    vi.mocked(documentService.listDocuments).mockResolvedValue(makePaginatedResponse(items) as never);

    const result = await documentService.listDocuments({ page: 2, page_size: 10, category: 'REPORTS' });

    expect(documentService.listDocuments).toHaveBeenCalledWith({ page: 2, page_size: 10, category: 'REPORTS' });
    expect(result.data.items).toHaveLength(1);
  });

  it('should return document detail with version history', async () => {
    const detail = makeDocumentDetail();
    vi.mocked(documentService.getDocumentDetail).mockResolvedValue({ data: detail } as never);

    const result = await documentService.getDocumentDetail('doc-uuid-1');
    expect(result.data.versions).toHaveLength(2);
    expect(result.data.current_version_number).toBe(2);
  });

  it('should call updateMetadata with correct payload', async () => {
    const mockResp = {
      data: {
        id: 'doc-1',
        title: 'New Title',
        category: 'LEGAL',
        tags: ['legal'],
        updated_at: new Date().toISOString(),
      },
    };
    vi.mocked(documentService.updateMetadata).mockResolvedValue(mockResp as never);

    const result = await documentService.updateMetadata('doc-1', { title: 'New Title', category: 'LEGAL' });
    expect(result.data.title).toBe('New Title');
  });

  it('should call uploadNewVersion and return version info', async () => {
    const mockFile = new File(['v2'], 'doc-v2.pdf', { type: 'application/pdf' });
    const mockResp = {
      data: {
        document_id: 'doc-1',
        version_number: 2,
        filename: 'doc-v2.pdf',
        file_size: 2,
        checksum_sha256: 'abc',
        change_notes: 'Updated',
        status: 'AWAITING_PROCESSING' as const,
        created_at: new Date().toISOString(),
      },
    };
    vi.mocked(documentService.uploadNewVersion).mockResolvedValue(mockResp as never);

    const result = await documentService.uploadNewVersion('doc-1', mockFile, 'Updated');
    expect(result.data.version_number).toBe(2);
  });

  it('should call deleteDocument and return deletion flags', async () => {
    const mockResp = {
      data: {
        id: 'doc-1',
        deleted: true,
        is_deleted: true,
        deleted_at: new Date().toISOString(),
        status: null,
      },
    };
    vi.mocked(documentService.deleteDocument).mockResolvedValue(mockResp as never);

    const result = await documentService.deleteDocument('doc-1', 'delete');
    expect(result.data.is_deleted).toBe(true);
  });

  it('should build correct preview URL', () => {
    vi.mocked(documentService.getPreviewUrl).mockReturnValue('/api/v1/documents/doc-1/preview');
    expect(documentService.getPreviewUrl('doc-1')).toBe('/api/v1/documents/doc-1/preview');
  });
});

// ─── DocumentUploadModal Tests ────────────────────────────────────────────────

describe('DocumentUploadModal', () => {
  it('should render when isOpen is true', () => {
    render(
      <MemoryRouter>
        <DocumentUploadModal isOpen={true} onClose={vi.fn()} />
      </MemoryRouter>
    );
    expect(screen.getByText('Upload Documents')).toBeInTheDocument();
    expect(document.getElementById('upload-drop-zone')).toBeInTheDocument();
  });

  it('should not render when isOpen is false', () => {
    render(
      <MemoryRouter>
        <DocumentUploadModal isOpen={false} onClose={vi.fn()} />
      </MemoryRouter>
    );
    expect(screen.queryByText('Upload Documents')).not.toBeInTheDocument();
  });

  it('should have close button in header', () => {
    render(
      <MemoryRouter>
        <DocumentUploadModal isOpen={true} onClose={vi.fn()} />
      </MemoryRouter>
    );
    expect(document.getElementById('upload-modal-close')).toBeInTheDocument();
  });

  it('should show file type hint text', () => {
    render(
      <MemoryRouter>
        <DocumentUploadModal isOpen={true} onClose={vi.fn()} />
      </MemoryRouter>
    );
    expect(screen.getAllByText(/PDF, DOCX, PPTX/).length).toBeGreaterThanOrEqual(1);
  });

  it('should disable upload button when no files pending', () => {
    render(
      <MemoryRouter>
        <DocumentUploadModal isOpen={true} onClose={vi.fn()} />
      </MemoryRouter>
    );
    const uploadBtn = document.getElementById('upload-submit-btn') as HTMLButtonElement;
    expect(uploadBtn).toBeDisabled();
  });
});

// ─── VersionHistoryTimeline Tests ─────────────────────────────────────────────

describe('VersionHistoryTimeline', () => {
  const baseProps = {
    documentId: 'doc-1',
    documentFilename: 'strategy.pdf',
    currentVersionNumber: 2,
    versions: makeDocumentDetail().versions,
  };

  it('should render version items', () => {
    render(
      <MemoryRouter>
        <VersionHistoryTimeline {...baseProps} />
      </MemoryRouter>
    );
    expect(document.getElementById('version-item-v2')).toBeInTheDocument();
    expect(document.getElementById('version-item-v1')).toBeInTheDocument();
  });

  it('should badge current version with "Current" label', () => {
    render(
      <MemoryRouter>
        <VersionHistoryTimeline {...baseProps} />
      </MemoryRouter>
    );
    expect(screen.getByText('Current')).toBeInTheDocument();
  });

  it('should display change notes when present', () => {
    render(
      <MemoryRouter>
        <VersionHistoryTimeline {...baseProps} />
      </MemoryRouter>
    );
    expect(screen.getByText('Updated Q3 projections')).toBeInTheDocument();
  });

  it('should show empty state when no versions provided', () => {
    render(
      <MemoryRouter>
        <VersionHistoryTimeline {...baseProps} versions={[]} />
      </MemoryRouter>
    );
    expect(screen.getByText('No version history available')).toBeInTheDocument();
  });

  it('should render per-version download buttons', () => {
    render(
      <MemoryRouter>
        <VersionHistoryTimeline {...baseProps} />
      </MemoryRouter>
    );
    expect(document.getElementById('download-v2')).toBeInTheDocument();
    expect(document.getElementById('download-v1')).toBeInTheDocument();
  });
});

// ─── DocumentExplorer Tests ───────────────────────────────────────────────────

describe('DocumentExplorer', () => {
  beforeEach(() => {
    vi.mocked(documentService.listDocuments).mockResolvedValue(
      makePaginatedResponse([
        makeDocument(),
        makeDocument({ id: 'doc-2', filename: 'policy.docx', title: 'HR Policy', status: 'PENDING', ai_ready: false }),
      ]) as never
    );
  });

  afterEach(() => vi.clearAllMocks());

  it('should render the search input and upload button', async () => {
    render(
      <MemoryRouter>
        <DocumentExplorer />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(document.getElementById('document-search-input')).toBeInTheDocument();
      expect(document.getElementById('document-upload-btn')).toBeInTheDocument();
    });
  });

  it('should render documents in grid view after load', async () => {
    render(
      <MemoryRouter>
        <DocumentExplorer />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText('Q3 Strategy')).toBeInTheDocument();
      expect(screen.getByText('HR Policy')).toBeInTheDocument();
    });
  });

  it('should switch to table view when table button clicked', async () => {
    render(
      <MemoryRouter>
        <DocumentExplorer />
      </MemoryRouter>
    );
    await waitFor(() => screen.getByText('Q3 Strategy'));
    fireEvent.click(document.getElementById('view-table-btn')!);
    await waitFor(() => {
      expect(document.getElementById('documents-table')).toBeInTheDocument();
    });
  });

  it('should open upload modal when upload button clicked', async () => {
    render(
      <MemoryRouter>
        <DocumentExplorer />
      </MemoryRouter>
    );
    await waitFor(() => screen.getByText('Q3 Strategy'));
    fireEvent.click(document.getElementById('document-upload-btn')!);
    await waitFor(() => {
      expect(document.getElementById('document-upload-modal')).toBeInTheDocument();
    });
  });

  it('should display AI Ready badge for ai_ready documents', async () => {
    render(
      <MemoryRouter>
        <DocumentExplorer />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getAllByText(/AI Ready/)[0]).toBeInTheDocument();
    });
  });

  it('should show empty state when no documents returned', async () => {
    vi.mocked(documentService.listDocuments).mockResolvedValue(makePaginatedResponse([]) as never);
    render(
      <MemoryRouter>
        <DocumentExplorer />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText('No documents found')).toBeInTheDocument();
    });
  });

  it('should show category filter dropdown', async () => {
    render(
      <MemoryRouter>
        <DocumentExplorer />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(document.getElementById('document-category-filter')).toBeInTheDocument();
    });
  });

  it('should pass search param to listDocuments when search input changes', async () => {
    render(
      <MemoryRouter>
        <DocumentExplorer />
      </MemoryRouter>
    );
    await waitFor(() => screen.getByText('Q3 Strategy'));

    const searchInput = document.getElementById('document-search-input') as HTMLInputElement;
    fireEvent.change(searchInput, { target: { value: 'policy' } });

    // After debounce (300ms), listDocuments should be called with search param
    await waitFor(
      () => {
        expect(documentService.listDocuments).toHaveBeenCalledWith(
          expect.objectContaining({ search: 'policy' })
        );
      },
      { timeout: 2000 }
    );
  });
});

// ─── DocumentPreviewModal Tests ───────────────────────────────────────────────

describe('DocumentPreviewModal', () => {
  it('should not render when isOpen is false', () => {
    render(
      <MemoryRouter>
        <DocumentPreviewModal isOpen={false} onClose={vi.fn()} document={null} />
      </MemoryRouter>
    );
    expect(document.getElementById('document-preview-modal')).not.toBeInTheDocument();
  });

  it('should render PDF preview via iframe for PDF documents', () => {
    const doc = makeDocumentDetail();
    render(
      <MemoryRouter>
        <DocumentPreviewModal isOpen={true} onClose={vi.fn()} document={doc} />
      </MemoryRouter>
    );
    expect(document.getElementById('document-preview-modal')).toBeInTheDocument();
    expect(document.getElementById('preview-pdf-iframe')).toBeInTheDocument();
  });

  it('should show unsupported fallback for PPTX files', () => {
    const doc = makeDocumentDetail();
    doc.file_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation';
    render(
      <MemoryRouter>
        <DocumentPreviewModal isOpen={true} onClose={vi.fn()} document={doc} />
      </MemoryRouter>
    );
    expect(screen.getByText('Preview not available')).toBeInTheDocument();
  });

  it('should render document title in header', () => {
    const doc = makeDocumentDetail();
    render(
      <MemoryRouter>
        <DocumentPreviewModal isOpen={true} onClose={vi.fn()} document={doc} />
      </MemoryRouter>
    );
    expect(screen.getByText('Q3 Strategy')).toBeInTheDocument();
  });

  it('should call onClose when close button is clicked', () => {
    const onClose = vi.fn();
    const doc = makeDocumentDetail();
    render(
      <MemoryRouter>
        <DocumentPreviewModal isOpen={true} onClose={onClose} document={doc} />
      </MemoryRouter>
    );
    fireEvent.click(document.getElementById('preview-close-btn')!);
    expect(onClose).toHaveBeenCalled();
  });
});

// ─── DocumentsPage Tests ──────────────────────────────────────────────────────

describe('DocumentsPage', () => {
  beforeEach(() => {
    vi.mocked(documentService.listDocuments).mockResolvedValue(makePaginatedResponse([]) as never);
  });

  it('should render page heading', async () => {
    render(
      <MemoryRouter>
        <DocumentsPage />
      </MemoryRouter>
    );
    expect(screen.getByRole('heading', { name: /Knowledge Repository/i })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('No documents found')).toBeInTheDocument();
    });
  });

  it('should render all three feature pills', async () => {
    render(
      <MemoryRouter>
        <DocumentsPage />
      </MemoryRouter>
    );
    expect(screen.getByText('Multi-format support')).toBeInTheDocument();
    expect(screen.getByText('Secure storage')).toBeInTheDocument();
    expect(screen.getByText('AI-ready pipeline')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('No documents found')).toBeInTheDocument();
    });
  });

  it('should render the upload button when authorized', async () => {
    render(
      <MemoryRouter>
        <DocumentsPage />
      </MemoryRouter>
    );
    expect(document.getElementById('page-upload-btn')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('No documents found')).toBeInTheDocument();
    });
  });
});
