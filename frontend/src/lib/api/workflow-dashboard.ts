import { apiClient } from '@/lib/api/client';
import type {
  OrderListItem,
  PaginatedResponse,
} from '@/lib/types/orders';
import type { ProjectRequestListItem } from '@/lib/types/projects';
import type { TimelineResponse } from '@/lib/types/workflow';

function unwrapList<T>(data: T[] | PaginatedResponse<T>): T[] {
  return Array.isArray(data) ? data : data.results;
}

export const workflowDashboardAPI = {
  async listOrders(): Promise<OrderListItem[]> {
    const response = await apiClient.get<
      OrderListItem[] | PaginatedResponse<OrderListItem>
    >('/orders/');

    return unwrapList(response.data);
  },

  async getOrderTimeline(orderId: number): Promise<TimelineResponse> {
    const response = await apiClient.get<TimelineResponse>(
      `/orders/${orderId}/timeline/`,
    );

    return response.data;
  },

  async listProjectRequests(): Promise<ProjectRequestListItem[]> {
    const response = await apiClient.get<
      ProjectRequestListItem[] | PaginatedResponse<ProjectRequestListItem>
    >('/projects/requests/');

    return unwrapList(response.data);
  },

  async getProjectTimeline(projectId: number): Promise<TimelineResponse> {
    const response = await apiClient.get<TimelineResponse>(
      `/projects/requests/${projectId}/timeline/`,
    );

    return response.data;
  },
};
