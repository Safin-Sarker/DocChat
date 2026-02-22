import apiClient from './apiClient';
import type { AuditLogEntry } from '@/domain/activity/types';

export async function getMyActivityLogs(limit = 50, offset = 0): Promise<AuditLogEntry[]> {
  const response = await apiClient.get<AuditLogEntry[]>('/api/v1/audit/me', {
    params: { limit, offset },
  });
  return response.data;
}
