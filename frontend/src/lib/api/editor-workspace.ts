import { apiClient } from '@/lib/api/client';
import type { EditorWorkspacePortfolioItem, EditorWorkspaceProfile } from '@/lib/types/editor-workspace';

export const editorWorkspaceAPI = {
  async getMe(): Promise<EditorWorkspaceProfile> {
    const response = await apiClient.get<EditorWorkspaceProfile>('/accounts/editors/me/');
    return response.data;
  },
  async updateProfile(payload: Partial<EditorWorkspaceProfile>): Promise<EditorWorkspaceProfile> {
    const response = await apiClient.patch<EditorWorkspaceProfile>('/accounts/editors/me/', payload);
    return response.data;
  },
  async createPortfolio(formData: FormData): Promise<EditorWorkspacePortfolioItem> {
    const response = await apiClient.post<EditorWorkspacePortfolioItem>('/accounts/editors/me/portfolio/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    return response.data;
  },
  async updatePortfolio(id: number, formData: FormData): Promise<EditorWorkspacePortfolioItem> {
    const response = await apiClient.patch<EditorWorkspacePortfolioItem>(`/accounts/editors/me/portfolio/${id}/`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    return response.data;
  },
  async deletePortfolio(id: number): Promise<void> {
    await apiClient.delete(`/accounts/editors/me/portfolio/${id}/`);
  },
  async submitPortfolio(id: number): Promise<EditorWorkspacePortfolioItem> {
    const response = await apiClient.post<EditorWorkspacePortfolioItem>(`/accounts/editors/me/portfolio/${id}/submit/`);
    return response.data;
  },
};
