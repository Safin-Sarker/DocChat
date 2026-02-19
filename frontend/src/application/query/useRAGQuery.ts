import { useMutation } from '@tanstack/react-query';
import { queryRAG } from '@/infrastructure/api/query.api';
import type { QueryRequest, QueryResponse } from '@/domain/query/types';

export const useRAGQuery = () => {
  return useMutation<QueryResponse, Error, QueryRequest>({
    mutationFn: (queryRequest: QueryRequest) => queryRAG(queryRequest),
  });
};
