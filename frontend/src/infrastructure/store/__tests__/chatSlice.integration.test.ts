import { describe, it, expect, vi } from 'vitest'
import chatReducer, {
  addMessage,
  updateLastMessage,
  appendToLastMessage,
} from '../slices/chatSlice'

// Mock crypto.randomUUID for deterministic IDs
vi.stubGlobal('crypto', { randomUUID: () => 'test-uuid-integration' })

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

describe('chatSlice integration – updateLastMessage & appendToLastMessage', () => {
  it('updateLastMessage updates content, sources, contexts, and reflection', () => {
    // Add a message first
    let state = chatReducer(initialState, addMessage({ role: 'assistant', content: 'initial' }))
    expect(state.messages).toHaveLength(1)

    // Update with full payload
    state = chatReducer(
      state,
      updateLastMessage({
        content: 'updated content',
        sources: [{ doc_id: 'd1', page: 1 }],
        contexts: ['context 1', 'context 2'],
        reflection: {
          faithfulness: 0.95,
          relevance: 0.9,
          completeness: 0.85,
          coherence: 0.9,
          conciseness: 0.88,
          overall: 0.9,
          verdict: 'pass',
          feedback: '',
          was_regenerated: false,
        },
      })
    )

    const last = state.messages[state.messages.length - 1]
    expect(last.content).toBe('updated content')
    expect(last.sources).toHaveLength(1)
    expect(last.contexts).toEqual(['context 1', 'context 2'])
    expect(last.reflection?.verdict).toBe('pass')
    expect(last.reflection?.overall).toBe(0.9)
  })

  it('appendToLastMessage appends text to last message content', () => {
    let state = chatReducer(initialState, addMessage({ role: 'assistant', content: 'Hello' }))
    state = chatReducer(state, appendToLastMessage(' world'))
    state = chatReducer(state, appendToLastMessage('!'))

    const last = state.messages[state.messages.length - 1]
    expect(last.content).toBe('Hello world!')
  })
})
