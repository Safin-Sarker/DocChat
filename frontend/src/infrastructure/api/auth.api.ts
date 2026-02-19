import apiClient from './apiClient';
import type { LoginRequest, RegisterRequest, AuthResponse } from '@/domain/auth/types';

export const login = async (credentials: LoginRequest): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>('/api/v1/auth/login', credentials);
  return response.data;
};

export const register = async (data: RegisterRequest): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>('/api/v1/auth/register', data);
  return response.data;
};
