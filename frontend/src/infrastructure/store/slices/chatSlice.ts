import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { Message } from '@/domain/chat/types';
import type { UploadedDocument } from '@/domain/document/types';
import type { ReflectionScore, SSEStage, SSECacheEvent } from '@/domain/query/types';

interface ChatState {
  messages: Message[];
  currentDocId: string | null;
  selectedDocIds: string[];
  selectAllDocs: boolean;
  isLoading: boolean;
  entities: string[];
  serverSessionId: string | null;
  uploadedDocuments: UploadedDocument[];
  streamingStage: SSEStage | null;
}

const initialState: ChatState = {
  messages: [],
  currentDocId: null,
  selectedDocIds: [],
  selectAllDocs: false,
  isLoading: false,
  entities: [],
  serverSessionId: null,
  uploadedDocuments: [],
  streamingStage: null,
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addMessage(state, action: PayloadAction<Omit<Message, 'id' | 'timestamp'>>) {
      state.messages.push({
        ...action.payload,
        id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
      });
    },

    updateLastMessage(
      state,
      action: PayloadAction<{
        content: string;
        sources?: Array<Record<string, any>>;
        contexts?: string[];
        reflection?: ReflectionScore | null;
      }>
    ) {
      const last = state.messages[state.messages.length - 1];
      if (last) {
        last.content = action.payload.content;
        last.sources = action.payload.sources;
        last.contexts = action.payload.contexts;
        last.reflection = action.payload.reflection;
      }
    },

    appendToLastMessage(state, action: PayloadAction<string>) {
      const last = state.messages[state.messages.length - 1];
      if (last) {
        last.content += action.payload;
      }
    },

    replaceLastMessageContent(state, action: PayloadAction<string>) {
      const last = state.messages[state.messages.length - 1];
      if (last) {
        last.content = action.payload;
      }
    },

    updateLastMessageMeta(
      state,
      action: PayloadAction<{
        sources?: Array<Record<string, any>>;
        contexts?: string[];
        reflection?: ReflectionScore | null;
        cache?: SSECacheEvent;
      }>
    ) {
      const last = state.messages[state.messages.length - 1];
      if (last) {
        if (action.payload.sources !== undefined) last.sources = action.payload.sources;
        if (action.payload.contexts !== undefined) last.contexts = action.payload.contexts;
        if (action.payload.reflection !== undefined) last.reflection = action.payload.reflection;
        if (action.payload.cache !== undefined) last.cache = action.payload.cache;
      }
    },

    clearMessages(state) {
      state.messages = [];
      state.entities = [];
    },

    setCurrentDoc(state, action: PayloadAction<string | null>) {
      state.currentDocId = action.payload;
    },

    toggleDocSelection(state, action: PayloadAction<string>) {
      const docId = action.payload;
      const idx = state.selectedDocIds.indexOf(docId);
      if (idx >= 0) {
        state.selectedDocIds.splice(idx, 1);
      } else {
        state.selectedDocIds.push(docId);
      }
      state.selectAllDocs = false;
      state.currentDocId =
        state.selectedDocIds.length === 1 ? state.selectedDocIds[0] : state.currentDocId;
    },

    setSelectAllDocs(state, action: PayloadAction<boolean>) {
      state.selectAllDocs = action.payload;
      state.selectedDocIds = action.payload
        ? state.uploadedDocuments.map((d) => d.doc_id)
        : [];
      state.currentDocId = null;
    },

    clearDocSelection(state) {
      state.selectedDocIds = [];
      state.selectAllDocs = false;
      state.currentDocId = null;
    },

    setLoading(state, action: PayloadAction<boolean>) {
      state.isLoading = action.payload;
    },

    setEntities(state, action: PayloadAction<string[]>) {
      state.entities = action.payload;
    },

    setServerSessionId(state, action: PayloadAction<string | null>) {
      state.serverSessionId = action.payload;
    },

    setStreamingStage(state, action: PayloadAction<SSEStage | null>) {
      state.streamingStage = action.payload;
    },

    addUploadedDocument(state, action: PayloadAction<UploadedDocument>) {
      state.uploadedDocuments.push(action.payload);
      state.selectedDocIds.push(action.payload.doc_id);
    },

    removeUploadedDocument(state, action: PayloadAction<string>) {
      const docId = action.payload;
      state.uploadedDocuments = state.uploadedDocuments.filter((d) => d.doc_id !== docId);
      state.selectedDocIds = state.selectedDocIds.filter((id) => id !== docId);
      if (state.currentDocId === docId) state.currentDocId = null;
    },

    setUploadedDocuments(state, action: PayloadAction<UploadedDocument[]>) {
      const docs = action.payload;
      state.uploadedDocuments = docs;
      state.selectedDocIds = state.selectAllDocs
        ? docs.map((d) => d.doc_id)
        : state.selectedDocIds.filter((id) => docs.some((d) => d.doc_id === id));
    },

    truncateMessagesAt(state, action: PayloadAction<number>) {
      state.messages = state.messages.slice(0, action.payload);
    },
  },
});

export const {
  addMessage,
  updateLastMessage,
  appendToLastMessage,
  replaceLastMessageContent,
  updateLastMessageMeta,
  clearMessages,
  setCurrentDoc,
  toggleDocSelection,
  setSelectAllDocs,
  clearDocSelection,
  setLoading,
  setEntities,
  setServerSessionId,
  setStreamingStage,
  addUploadedDocument,
  removeUploadedDocument,
  setUploadedDocuments,
  truncateMessagesAt,
} = chatSlice.actions;

export default chatSlice.reducer;
