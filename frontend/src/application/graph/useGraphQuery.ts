import { useQuery } from '@tanstack/react-query';
import { getRelatedEntities } from '@/infrastructure/api/graph.api';
import type { GraphQueryResponse } from '@/domain/graph/types';

export const useGraphQuery = (entities: string[] = []) => {
  const safeEntities = entities || [];

  return useQuery<GraphQueryResponse, Error>({
    queryKey: ['graph', safeEntities],
    queryFn: () => getRelatedEntities({ entities: safeEntities, max_depth: 2, limit: 50 }),
    enabled: safeEntities.length > 0,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    refetchOnWindowFocus: false,
  });
};
