import { useCallback, useRef } from 'react';
import { queryRAGStream } from '@/infrastructure/api/query.api';
import { useChatStore } from '@/infrastructure/stores/chatStore';
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
          const {
            appendToLastMessage,
            replaceLastMessageContent,
            setStreamingStage,
            updateLastMessageMeta,
            setEntities,
          } = useChatStore.getState();

          switch (eventType) {
            case 'status':
              setStreamingStage(data.stage);
              break;
            case 'token':
              if (data.replace) {
                replaceLastMessageContent('');
              } else {
                appendToLastMessage(data.content);
              }
              break;
            case 'sources':
              updateLastMessageMeta(data.sources, data.contexts);
              break;
            case 'reflection':
              updateLastMessageMeta(undefined, undefined, data);
              break;
            case 'cache':
              updateLastMessageMeta(undefined, undefined, undefined, data);
              break;
            case 'entities':
              setEntities(data.entities);
              break;
            case 'error':
              replaceLastMessageContent(
                'Sorry, I encountered an error processing your query. Please try again.'
              );
              break;
            case 'done':
              setStreamingStage(null);
              break;
          }
        },
        controller.signal
      );
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        useChatStore.getState().replaceLastMessageContent(
          'Sorry, I encountered an error processing your query. Please try again.'
        );
      }
    } finally {
      useChatStore.getState().setLoading(false);
      useChatStore.getState().setStreamingStage(null);
    }
  }, []);

  const abort = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { streamQuery, abort };
};
