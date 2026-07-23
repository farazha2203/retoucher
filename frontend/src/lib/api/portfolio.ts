import { apiClient } from '@/lib/api/client';
import type {
  PortfolioComment,
  PortfolioSocialItem,
} from '@/lib/types/portfolio';

export const portfolioAPI = {
  async get(id: number | string): Promise<PortfolioSocialItem> {
    const response = await apiClient.get<PortfolioSocialItem>(
      `/accounts/portfolio/${id}/`,
    );
    return response.data;
  },

  async toggleLike(
    id: number | string,
  ): Promise<{ liked: boolean; likes_count: number }> {
    const response = await apiClient.post(
      `/accounts/portfolio/${id}/toggle_like/`,
    );
    return response.data;
  },

  async comment(
    id: number | string,
    body: string,
    parent?: number,
  ): Promise<PortfolioComment> {
    const response = await apiClient.post<PortfolioComment>(
      `/accounts/portfolio/${id}/comment/`,
      { body, parent },
    );
    return response.data;
  },

  async reportComment(
    id: number | string,
    comment: number,
    reason: string,
  ): Promise<{ created: boolean; report_id: number }> {
    const response = await apiClient.post(
      `/accounts/portfolio/${id}/report-comment/`,
      { comment, reason },
    );
    return response.data;
  },
};
