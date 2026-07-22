import { apiClient } from './client';
import type {
  Order,
  OrderComment,
  OrderImage,
  PaginatedResponse,
  OrderActivityLog,
  OrderStatusHistory,
  OrderTimelineResponse,
} from '@/types';

type MaybePaginated<T> = PaginatedResponse<T> | T[];

function normalizeList<T>(data: MaybePaginated<T>): PaginatedResponse<T> {
  if (Array.isArray(data)) {
    return { count: data.length, next: null, previous: null, results: data };
  }
  return data;
}

export type CreateOrderPayload = {
  title: string;
  description?: string;
  deadline?: string | null;
};

export type UpdateOrderPayload = Partial<CreateOrderPayload>;

export type CreateCommentPayload = {
  target_type?: 'order' | 'image' | 'delivery' | 'revision';
  image?: number | null;
  delivery?: number | null;
  revision?: number | null;
  text?: string;
  x?: number | null;
  y?: number | null;
  parent?: number | null;
  annotation_type?: 'none' | 'point' | 'rectangle' | 'circle' | 'arrow' | 'freehand';
  annotation_label?: string;
  annotation_color?: string;
  annotation_data?: Record<string, unknown>;
};

export type UpdateCommentPayload = Partial<CreateCommentPayload>;

export const ordersAPI = {
  async list(params?: Record<string, string | number | boolean>): Promise<PaginatedResponse<Order>> {
    const { data } = await apiClient.get('/orders/', { params });
    return normalizeList<Order>(data);
  },

  async get(id: number | string): Promise<Order> {
    const { data } = await apiClient.get(`/orders/${id}/`);
    return data;
  },

  async timeline(id: number | string): Promise<OrderTimelineResponse> {
    const { data } = await apiClient.get(`/orders/${id}/timeline/`);
    return data;
  },

  async create(payload: CreateOrderPayload): Promise<Order> {
    const { data } = await apiClient.post('/orders/', payload);
    return data;
  },

  async update(id: number | string, payload: UpdateOrderPayload): Promise<Order> {
    const { data } = await apiClient.patch(`/orders/${id}/`, payload);
    return data;
  },

  async remove(id: number | string): Promise<void> {
    await apiClient.delete(`/orders/${id}/`);
  },

  async submit(id: number | string): Promise<Order> {
    const { data } = await apiClient.post(`/orders/${id}/submit/`);
    return data;
  },

  async approve(id: number | string): Promise<Order> {
    const { data } = await apiClient.post(`/orders/${id}/client-approve/`);
    return data;
  },

  async requestRevision(id: number | string, note: string): Promise<Order> {
    const { data } = await apiClient.post(`/orders/${id}/client-request-revision/`, { note });
    return data;
  },

  async rate(id: number | string, score: number, comment = ''): Promise<Order | void> {
    const { data } = await apiClient.post(`/orders/${id}/client-rate/`, { score, comment });
    return data;
  },

  async uploadImage(id: number | string, file: File, note = ''): Promise<OrderImage> {
    const formData = new FormData();
    formData.append('image', file);
    if (note) formData.append('note', note);

    const { data } = await apiClient.post(`/orders/${id}/upload-image/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  async getComments(id: number | string): Promise<OrderComment[]> {
    const { data } = await apiClient.get(`/orders/${id}/comments/`);
    return Array.isArray(data) ? data : data.results ?? [];
  },

  async getCommentThreads(id: number | string): Promise<OrderComment[]> {
    const { data } = await apiClient.get(`/orders/${id}/comment-threads/`);
    return Array.isArray(data) ? data : data.results ?? [];
  },

  async createComment(id: number | string, payload: CreateCommentPayload): Promise<OrderComment> {
    const { data } = await apiClient.post(`/orders/${id}/comments/`, payload);
    return data;
  },

  async updateComment(id: number | string, commentId: number | string, payload: UpdateCommentPayload): Promise<OrderComment> {
    const { data } = await apiClient.patch(`/orders/${id}/comments/${commentId}/`, payload);
    return data;
  },

  async resolveComment(id: number | string, commentId: number | string): Promise<OrderComment> {
    const { data } = await apiClient.post(`/orders/${id}/comments/${commentId}/resolve/`);
    return data;
  },

  async unresolveComment(id: number | string, commentId: number | string): Promise<OrderComment> {
    const { data } = await apiClient.post(`/orders/${id}/comments/${commentId}/unresolve/`);
    return data;
  },

  async setCommentStatus(
    id: number | string,
    commentId: number | string,
    status: 'active' | 'resolved' | 'approved' | 'deleted',
  ): Promise<OrderComment> {
    const { data } = await apiClient.post(`/orders/${id}/comments/${commentId}/set-status/`, { status });
    return data;
  },

  async getActivityLog(id: number | string): Promise<OrderActivityLog[]> {
    const { data } = await apiClient.get(`/orders/${id}/activity-log/`);
    return Array.isArray(data) ? data : data.results ?? [];
  },

  async getStatusHistory(id: number | string): Promise<OrderStatusHistory[]> {
    const { data } = await apiClient.get(`/orders/${id}/status-history/`);
    return Array.isArray(data) ? data : data.results ?? [];
  },
};
