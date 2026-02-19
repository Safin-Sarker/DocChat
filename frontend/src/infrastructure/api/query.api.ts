import apiClient, { API_URL } from './apiClient';
import { useAuthStore } from '@/infrastructure/stores/authStore';
import type { QueryRequest, QueryResponse } from '@/domain/query/types';

export const queryRAG = async (queryRequest: QueryRequest): Promise<QueryResponse> => {
  const response = await apiClient.post<QueryResponse>(
    '/api/v1/query/',
    queryRequest
  );
  return response.data;
};

export const queryRAGStream = async (
  queryRequest: QueryRequest,
  onEvent: (eventType: string, data: any) => void,
  signal?: AbortSignal
): Promise<void> => {
  const token = useAuthStore.getState().token;
  const response = await fetch(`${API_URL}/api/v1/query/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(queryRequest),
    signal,
  });

  if (!response.ok) {
    if (response.status === 401) {
      useAuthStore.getState().logout();
    }
    const errorData = await response.json().catch(() => ({ detail: 'Stream request failed' }));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE events from buffer
    const parts = buffer.split('\n\n');
    buffer = parts.pop() || '';

    for (const part of parts) {
      if (!part.trim()) continue;
      const lines = part.split('\n');
      let eventType = '';
      let eventData = '';

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          eventData = line.slice(6);
        }
      }

      if (eventType && eventData) {
        try {
          const parsed = JSON.parse(eventData);
          onEvent(eventType, parsed);
        } catch (e) {
          console.error('Failed to parse SSE data:', eventData, e);
        }
      }
    }
  }
};
