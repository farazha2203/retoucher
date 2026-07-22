import { apiClient } from './client';
import type { EditCategory, EditStyle } from '@/types';

export const catalogAPI = {
  categories: async (): Promise<EditCategory[]> => {
    const { data } = await apiClient.get('/api/catalog/categories/');
    return data;
  },

  styles: async (categoryId?: number): Promise<EditStyle[]> => {
    const params = categoryId ? { category: String(categoryId) } : {};
    const { data } = await apiClient.get('/api/catalog/styles/', { params });
    return data;
  },
};