import { describe, it, expect, vi } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/test/test-utils'
import { DocumentList } from '../DocumentList'
import type { UploadedDocument } from '@/domain/document/types'

// Mock the document API
vi.mock('@/infrastructure/api/document.api', () => ({
  deleteDocument: vi.fn(),
}))

const makeDocs = (count: number): UploadedDocument[] =>
  Array.from({ length: count }, (_, i) => ({
    doc_id: `doc-${i}`,
    filename: `document-${i}.pdf`,
    pages: i + 1,
    uploadedAt: new Date().toISOString(),
  }))

describe('DocumentList', () => {
  it('shows empty state when no documents', () => {
    renderWithProviders(<DocumentList isLoading={false} />, {
      preloadedState: { chat: { messages: [], currentDocId: null, selectedDocIds: [], selectAllDocs: false, isLoading: false, entities: [], serverSessionId: null, uploadedDocuments: [], streamingStage: null } },
    })
    expect(screen.getByText('No documents')).toBeInTheDocument()
    expect(screen.getByText('Upload a document to start chatting')).toBeInTheDocument()
  })

  it('shows loading skeletons when isLoading is true', () => {
    const { container } = renderWithProviders(<DocumentList isLoading={true} />)
    // Skeletons render as div elements with animate-pulse class
    const skeletons = container.querySelectorAll('[class*="animate-pulse"]')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('renders document items by filename', () => {
    const docs = makeDocs(2)
    renderWithProviders(<DocumentList isLoading={false} />, {
      preloadedState: { chat: { messages: [], currentDocId: null, selectedDocIds: [], selectAllDocs: false, isLoading: false, entities: [], serverSessionId: null, uploadedDocuments: docs, streamingStage: null } },
    })
    expect(screen.getByText('document-0.pdf')).toBeInTheDocument()
    expect(screen.getByText('document-1.pdf')).toBeInTheDocument()
  })

  it('filters documents when searching', async () => {
    const user = userEvent.setup()
    const docs = makeDocs(4) // Need 3+ docs for search to appear
    renderWithProviders(<DocumentList isLoading={false} />, {
      preloadedState: { chat: { messages: [], currentDocId: null, selectedDocIds: [], selectAllDocs: false, isLoading: false, entities: [], serverSessionId: null, uploadedDocuments: docs, streamingStage: null } },
    })

    const searchInput = screen.getByPlaceholderText('Search documents...')
    await user.type(searchInput, 'document-0')

    expect(screen.getByText('document-0.pdf')).toBeInTheDocument()
    expect(screen.queryByText('document-1.pdf')).not.toBeInTheDocument()
  })
})
