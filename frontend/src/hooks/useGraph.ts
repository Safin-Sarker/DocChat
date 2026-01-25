import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import type { GraphQueryResponse } from '../types/api';

export const useGraphQuery = (entities: string[] = []) => {
  const safeEntities = entities || [];

  return useQuery<GraphQueryResponse, Error>({
    queryKey: ['graph', safeEntities],
    queryFn: () => api.getRelatedEntities({ entities: safeEntities, max_depth: 2, limit: 50 }),
    enabled: safeEntities.length > 0,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    refetchOnWindowFocus: false,
  });
};
