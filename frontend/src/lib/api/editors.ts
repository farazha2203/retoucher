import { apiClient } from '@/lib/api/client';
import type { EditorProfile } from '@/lib/types/editors';
export type { EditorProfile, EditorSkill } from '@/lib/types/editors';

export const editorsAPI = {
  async list(): Promise<EditorProfile[]> {
    const response = await apiClient.get<
      EditorProfile[] | { results: EditorProfile[] }
    >('/accounts/editors/');

    return Array.isArray(response.data)
      ? response.data
      : response.data.results;
  },

  async get(id: number | string): Promise<EditorProfile> {
    const response = await apiClient.get<EditorProfile>(
      `/accounts/editors/${id}/`,
    );
    return response.data;
  },
};
