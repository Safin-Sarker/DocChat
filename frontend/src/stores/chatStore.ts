import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Message, UploadedDocument } from '../types/api';

interface ChatStore {
  messages: Message[];
  currentDocId: string | null;
  isLoading: boolean;
  entities: string[];
  serverSessionId: string | null;
  uploadedDocuments: UploadedDocument[];
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateLastMessage: (content: string, sources?: Array<Record<string, any>>, contexts?: string[]) => void;
  clearMessages: () => void;
  setCurrentDoc: (docId: string | null) => void;
  setLoading: (loading: boolean) => void;
  setEntities: (entities: string[]) => void;
  setServerSessionId: (id: string | null) => void;
  addUploadedDocument: (doc: UploadedDocument) => void;
  removeUploadedDocument: (docId: string) => void;
  setUploadedDocuments: (docs: UploadedDocument[]) => void;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set) => ({
      messages: [],
      currentDocId: null,
      isLoading: false,
      entities: [],
      serverSessionId: null,
      uploadedDocuments: [],

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

      updateLastMessage: (content, sources, contexts) =>
        set((state) => {
          const newMessages = [...state.messages];
          if (newMessages.length > 0) {
            const lastMessage = newMessages[newMessages.length - 1];
            newMessages[newMessages.length - 1] = {
              ...lastMessage,
              content,
              sources,
              contexts,
            };
          }
          return { messages: newMessages };
        }),

      clearMessages: () => set({ messages: [], entities: [], uploadedDocuments: [] }),

      setCurrentDoc: (docId) => set({ currentDocId: docId }),

      setLoading: (loading) => set({ isLoading: loading }),

      setEntities: (entities) => set({ entities }),

      setServerSessionId: (id) => set({ serverSessionId: id }),

      addUploadedDocument: (doc) =>
        set((state) => ({
          uploadedDocuments: [...state.uploadedDocuments, doc],
        })),

      removeUploadedDocument: (docId) =>
        set((state) => ({
          uploadedDocuments: state.uploadedDocuments.filter((d) => d.doc_id !== docId),
          currentDocId: state.currentDocId === docId ? null : state.currentDocId,
        })),

      setUploadedDocuments: (docs) => set({ uploadedDocuments: docs }),
    }),
    {
      name: 'docchat-storage',
      partialize: (state) => ({
        currentDocId: state.currentDocId,
        entities: state.entities,
        messages: state.messages,
        serverSessionId: state.serverSessionId,
        uploadedDocuments: state.uploadedDocuments,
      }),
    }
  )
);
