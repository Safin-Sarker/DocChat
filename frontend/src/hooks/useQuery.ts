import { useMutation } from '@tanstack/react-query';
import { useCallback, useRef } from 'react';
import { api } from '../api/client';
import { useChatStore } from '../stores/chatStore';
import type { QueryRequest, QueryResponse } from '../types/api';

export const useRAGQuery = () => {
  return useMutation<QueryResponse, Error, QueryRequest>({
    mutationFn: (queryRequest: QueryRequest) => api.queryRAG(queryRequest),
  });
};

export const useRAGQueryStream = () => {
  const abortRef = useRef<AbortController | null>(null);

  const streamQuery = useCallback(async (queryRequest: QueryRequest) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await api.queryRAGStream(
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
