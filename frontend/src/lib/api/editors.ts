import { apiClient } from './client';

export interface EditorSkill {
  id: number;
  category: number;
  category_title: string;
  title: string;
  slug: string;
  description: string;
  min_price: number;
  max_price: number;
  suggested_price: number;
  estimated_delivery_hours: number;
  packages: unknown[];
}

export interface EditorPortfolioItem {
  id: number;
  title: string;
  description: string;
  style: number | null;
  style_title: string;
  before_image: string | null;
  after_image: string | null;
  is_featured: boolean;
}

export interface EditorProfile {
  id: number;
  user: number;
  username: string;
  display_name: string;
  bio: string;
  level: 'junior' | 'mid' | 'senior' | 'pro';
  skills: EditorSkill[];
  base_price: number;
  average_delivery_hours: number;
  rating_average: string | number;
  completed_orders_count: number;
  is_available: boolean;
  accepts_direct_requests: boolean;
  accepts_public_requests: boolean;
  accepts_sample_challenges: boolean;
  portfolio_items?: EditorPortfolioItem[];
}

export const editorsAPI = {
  list: async (params?: Record<string, string | number | boolean>) => {
    const { data } = await apiClient.get('/api/accounts/editors/', { params });
    return Array.isArray(data) ? data : data.results ?? [];
  },

  get: async (id: number | string) => {
    const { data } = await apiClient.get(`/api/accounts/editors/${id}/`);
    return data as EditorProfile;
  },
};