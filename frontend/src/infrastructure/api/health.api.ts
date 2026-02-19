import apiClient from './apiClient';
import type { HealthCheckResponse } from '@/domain/health/types';

export const healthCheck = async (): Promise<HealthCheckResponse> => {
  const response = await apiClient.get<HealthCheckResponse>('/health');
  return response.data;
};
