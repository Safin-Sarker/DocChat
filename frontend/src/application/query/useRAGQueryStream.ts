import { useCallback, useRef } from 'react';
import { queryRAGStream } from '@/infrastructure/api/query.api';
import { store } from '@/infrastructure/store';
import {
  appendToLastMessage,
  replaceLastMessageContent,
  setStreamingStage,
  updateLastMessageMeta,
  setEntities,
  setLoading,
} from '@/infrastructure/store/slices/chatSlice';
import type { QueryRequest } from '@/domain/query/types';

export const useRAGQueryStream = () => {
  const abortRef = useRef<AbortController | null>(null);

  const streamQuery = useCallback(async (queryRequest: QueryRequest) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await queryRAGStream(
        queryRequest,
        (eventType, data) => {
          switch (eventType) {
            case 'status':
              store.dispatch(setStreamingStage(data.stage));
              break;
            case 'token':
              if (data.replace) {
                store.dispatch(replaceLastMessageContent(''));
              } else {
                store.dispatch(appendToLastMessage(data.content));
              }
              break;
            case 'sources':
              store.dispatch(updateLastMessageMeta({ sources: data.sources, contexts: data.contexts, source_map: data.source_map }));
              break;
            case 'reflection':
              store.dispatch(updateLastMessageMeta({ reflection: data }));
              break;
            case 'cache':
              store.dispatch(updateLastMessageMeta({ cache: data }));
              break;
            case 'entities':
              store.dispatch(setEntities(data.entities));
              break;
            case 'error':
              store.dispatch(replaceLastMessageContent(
                'Sorry, I encountered an error processing your query. Please try again.'
              ));
              break;
            case 'done':
              store.dispatch(setStreamingStage(null));
              break;
          }
        },
        controller.signal
      );
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== 'AbortError') {
        store.dispatch(replaceLastMessageContent(
          'Sorry, I encountered an error processing your query. Please try again.'
        ));
      }
    } finally {
      store.dispatch(setLoading(false));
      store.dispatch(setStreamingStage(null));
    }
  }, []);

  const abort = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { streamQuery, abort };
};
