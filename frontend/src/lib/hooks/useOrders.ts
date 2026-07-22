import { useQuery } from '@tanstack/react-query';

import { workflowDashboardAPI } from '@/lib/api/workflow-dashboard';

export function useOrders() {
  return useQuery({
    queryKey: ['workflow-dashboard', 'orders'],
    queryFn: workflowDashboardAPI.listOrders,
  });
}

export function useOrderTimeline(orderId: number | null) {
  return useQuery({
    queryKey: ['workflow-dashboard', 'orders', orderId, 'timeline'],
    queryFn: () =>
      workflowDashboardAPI.getOrderTimeline(orderId as number),
    enabled: Boolean(orderId),
  });
}
