import { useMutation } from '@tanstack/react-query';
import { api } from '../api/client';
import type { QueryRequest, QueryResponse } from '../types/api';

export const useRAGQuery = () => {
  return useMutation<QueryResponse, Error, QueryRequest>({
    mutationFn: (queryRequest: QueryRequest) => api.queryRAG(queryRequest),
  });
};
