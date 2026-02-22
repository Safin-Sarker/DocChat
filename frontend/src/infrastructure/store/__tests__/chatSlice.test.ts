import { describe, it, expect, vi } from 'vitest'
import chatReducer, {
  addMessage,
  toggleDocSelection,
  setSelectAllDocs,
  removeUploadedDocument,
} from '../slices/chatSlice'

// Mock crypto.randomUUID for deterministic IDs in tests
vi.stubGlobal('crypto', { randomUUID: () => 'test-uuid' })

const initialState = {
  messages: [],
  currentDocId: null,
  selectedDocIds: [],
  selectAllDocs: false,
  isLoading: false,
  entities: [],
  serverSessionId: null,
  uploadedDocuments: [],
  streamingStage: null,
}

describe('chatSlice', () => {
  it('addMessage appends a message to the array', () => {
    const state = chatReducer(initialState, addMessage({ role: 'user', content: 'hello' }))
    expect(state.messages).toHaveLength(1)
    expect(state.messages[0].role).toBe('user')
    expect(state.messages[0].content).toBe('hello')
    expect(state.messages[0].id).toBe('test-uuid')
  })

  it('toggleDocSelection toggles doc_id in/out of selectedDocIds', () => {
    let state = chatReducer(initialState, toggleDocSelection('doc-1'))
    expect(state.selectedDocIds).toContain('doc-1')

    state = chatReducer(state, toggleDocSelection('doc-1'))
    expect(state.selectedDocIds).not.toContain('doc-1')
  })

  it('setSelectAllDocs toggles selectAllDocs flag', () => {
    const stateWithDocs = {
      ...initialState,
      uploadedDocuments: [
        { doc_id: 'd1', filename: 'a.pdf', pages: 1, uploadedAt: '' },
        { doc_id: 'd2', filename: 'b.pdf', pages: 2, uploadedAt: '' },
      ],
    }
    const state = chatReducer(stateWithDocs, setSelectAllDocs(true))
    expect(state.selectAllDocs).toBe(true)
    expect(state.selectedDocIds).toEqual(['d1', 'd2'])

    const state2 = chatReducer(state, setSelectAllDocs(false))
    expect(state2.selectAllDocs).toBe(false)
    expect(state2.selectedDocIds).toEqual([])
  })

  it('removeUploadedDocument removes doc from uploadedDocuments', () => {
    const stateWithDocs = {
      ...initialState,
      uploadedDocuments: [
        { doc_id: 'd1', filename: 'a.pdf', pages: 1, uploadedAt: '' },
        { doc_id: 'd2', filename: 'b.pdf', pages: 2, uploadedAt: '' },
      ],
      selectedDocIds: ['d1', 'd2'],
      currentDocId: 'd1',
    }
    const state = chatReducer(stateWithDocs, removeUploadedDocument('d1'))
    expect(state.uploadedDocuments).toHaveLength(1)
    expect(state.uploadedDocuments[0].doc_id).toBe('d2')
    expect(state.selectedDocIds).not.toContain('d1')
    expect(state.currentDocId).toBeNull()
  })
})
