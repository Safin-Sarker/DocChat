import { useGetRelatedEntitiesQuery } from '@/infrastructure/store/api/apiSlice';
import type { GraphQueryResponse } from '@/domain/graph/types';

export const useGraphQuery = (entities: string[] = []) => {
  const safeEntities = entities || [];

  const result = useGetRelatedEntitiesQuery(
    { entities: safeEntities, max_depth: 2, limit: 50 },
    { skip: safeEntities.length === 0 }
  );

  return {
    data: result.data as GraphQueryResponse | undefined,
    isLoading: result.isLoading,
    isFetching: result.isFetching,
    isError: result.isError,
    error: result.error ? new Error((result.error as { detail?: string })?.detail || 'Query failed') : null,
    refetch: result.refetch,
  };
};
