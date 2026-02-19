import apiClient from './apiClient';
import type { GraphQueryRequest, GraphQueryResponse } from '@/domain/graph/types';

export const getRelatedEntities = async (graphRequest: GraphQueryRequest): Promise<GraphQueryResponse> => {
  const response = await apiClient.post<GraphQueryResponse>(
    '/api/v1/graph/related',
    graphRequest
  );
  return response.data;
};
