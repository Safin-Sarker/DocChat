import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Message, UploadedDocument, ReflectionScore, SSEStage } from '../types/api';

interface ChatStore {
  messages: Message[];
  currentDocId: string | null;
  selectedDocIds: string[];
  selectAllDocs: boolean;
  isLoading: boolean;
  entities: string[];
  serverSessionId: string | null;
  uploadedDocuments: UploadedDocument[];
  streamingStage: SSEStage | null;

  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateLastMessage: (content: string, sources?: Array<Record<string, any>>, contexts?: string[], reflection?: ReflectionScore | null) => void;
  appendToLastMessage: (token: string) => void;
  replaceLastMessageContent: (content: string) => void;
  updateLastMessageMeta: (sources?: Array<Record<string, any>>, contexts?: string[], reflection?: ReflectionScore | null) => void;
  clearMessages: () => void;
  setCurrentDoc: (docId: string | null) => void;
  toggleDocSelection: (docId: string) => void;
  setSelectAllDocs: (selectAll: boolean) => void;
  clearDocSelection: () => void;
  setLoading: (loading: boolean) => void;
  setEntities: (entities: string[]) => void;
  setServerSessionId: (id: string | null) => void;
  setStreamingStage: (stage: SSEStage | null) => void;
  addUploadedDocument: (doc: UploadedDocument) => void;
  removeUploadedDocument: (docId: string) => void;
  setUploadedDocuments: (docs: UploadedDocument[]) => void;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set) => ({
      messages: [],
      currentDocId: null,
      selectedDocIds: [],
      selectAllDocs: false,
      isLoading: false,
      entities: [],
      serverSessionId: null,
      uploadedDocuments: [],
      streamingStage: null,

      addMessage: (message) =>
        set((state) => ({
          messages: [
            ...state.messages,
            {
              ...message,
              id: crypto.randomUUID(),
              timestamp: new Date(),
            },
          ],
        })),

      updateLastMessage: (content, sources, contexts, reflection) =>
        set((state) => {
          const newMessages = [...state.messages];
          if (newMessages.length > 0) {
            const lastMessage = newMessages[newMessages.length - 1];
            newMessages[newMessages.length - 1] = {
              ...lastMessage,
              content,
              sources,
              contexts,
              reflection,
            };
          }
          return { messages: newMessages };
        }),

      appendToLastMessage: (token) =>
        set((state) => {
          const newMessages = [...state.messages];
          if (newMessages.length > 0) {
            const last = newMessages[newMessages.length - 1];
            newMessages[newMessages.length - 1] = {
              ...last,
              content: last.content + token,
            };
          }
          return { messages: newMessages };
        }),

      replaceLastMessageContent: (content) =>
        set((state) => {
          const newMessages = [...state.messages];
          if (newMessages.length > 0) {
            newMessages[newMessages.length - 1] = {
              ...newMessages[newMessages.length - 1],
              content,
            };
          }
          return { messages: newMessages };
        }),

      updateLastMessageMeta: (sources, contexts, reflection) =>
        set((state) => {
          const newMessages = [...state.messages];
          if (newMessages.length > 0) {
            const last = newMessages[newMessages.length - 1];
            newMessages[newMessages.length - 1] = {
              ...last,
              ...(sources !== undefined && { sources }),
              ...(contexts !== undefined && { contexts }),
              ...(reflection !== undefined && { reflection }),
            };
          }
          return { messages: newMessages };
        }),

      clearMessages: () => set({ messages: [], entities: [] }),

      setCurrentDoc: (docId) => set({ currentDocId: docId }),

      toggleDocSelection: (docId) =>
        set((state) => {
          const isSelected = state.selectedDocIds.includes(docId);
          const newSelectedIds = isSelected
            ? state.selectedDocIds.filter((id) => id !== docId)
            : [...state.selectedDocIds, docId];
          return {
            selectedDocIds: newSelectedIds,
            selectAllDocs: false,
            currentDocId: newSelectedIds.length === 1 ? newSelectedIds[0] : state.currentDocId,
          };
        }),

      setSelectAllDocs: (selectAll) =>
        set((state) => ({
          selectAllDocs: selectAll,
          selectedDocIds: selectAll
            ? state.uploadedDocuments.map((d) => d.doc_id)
            : [],
          currentDocId: null,
        })),

      clearDocSelection: () =>
        set({ selectedDocIds: [], selectAllDocs: false, currentDocId: null }),

      setLoading: (loading) => set({ isLoading: loading }),

      setEntities: (entities) => set({ entities }),

      setServerSessionId: (id) => set({ serverSessionId: id }),

      setStreamingStage: (stage) => set({ streamingStage: stage }),

      addUploadedDocument: (doc) =>
        set((state) => ({
          uploadedDocuments: [...state.uploadedDocuments, doc],
          selectedDocIds: [...state.selectedDocIds, doc.doc_id],
        })),

      removeUploadedDocument: (docId) =>
        set((state) => ({
          uploadedDocuments: state.uploadedDocuments.filter((d) => d.doc_id !== docId),
          selectedDocIds: state.selectedDocIds.filter((id) => id !== docId),
          currentDocId: state.currentDocId === docId ? null : state.currentDocId,
        })),

      setUploadedDocuments: (docs) =>
        set((state) => ({
          uploadedDocuments: docs,
          selectedDocIds: state.selectAllDocs
            ? docs.map((d) => d.doc_id)
            : state.selectedDocIds.filter((id) => docs.some((d) => d.doc_id === id)),
        })),
    }),
    {
      name: 'docchat-storage',
      partialize: (state) => ({
        currentDocId: state.currentDocId,
        selectedDocIds: state.selectedDocIds,
        selectAllDocs: state.selectAllDocs,
        entities: state.entities,
        messages: state.messages,
        serverSessionId: state.serverSessionId,
        uploadedDocuments: state.uploadedDocuments,
      }),
    }
  )
);
