import { apiClient } from './client';
import type { ProjectRequest, CreateProjectPayload, PaginatedResponse } from '@/types';

export const projectsAPI = {
  list: async (params?: Record<string, string>): Promise<PaginatedResponse<ProjectRequest>> => {
    const { data } = await apiClient.get('/api/projects/requests/', { params });
    return data;
  },

  get: async (id: number): Promise<ProjectRequest> => {
    const { data } = await apiClient.get(`/api/projects/requests/${id}/`);
    return data;
  },

  create: async (payload: CreateProjectPayload): Promise<ProjectRequest> => {
    const { data } = await apiClient.post('/api/projects/requests/', payload);
    return data;
  },

  submit: async (id: number): Promise<ProjectRequest> => {
    const { data } = await apiClient.post(`/api/projects/requests/${id}/submit/`);
    return data;
  },

  uploadImage: async (projectId: number, file: File, caption?: string): Promise<void> => {
    const form = new FormData();
    form.append('image', file);
    if (caption) form.append('caption', caption);
    await apiClient.post(`/api/projects/requests/${projectId}/upload-image/`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/projects/requests/${id}/`);
  },
};