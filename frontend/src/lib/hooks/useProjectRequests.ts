import { useQuery } from '@tanstack/react-query';

import { workflowDashboardAPI } from '@/lib/api/workflow-dashboard';

export function useProjectRequests() {
  return useQuery({
    queryKey: ['workflow-dashboard', 'project-requests'],
    queryFn: workflowDashboardAPI.listProjectRequests,
  });
}

export function useProjectTimeline(projectId: number | null) {
  return useQuery({
    queryKey: [
      'workflow-dashboard',
      'project-requests',
      projectId,
      'timeline',
    ],
    queryFn: () =>
      workflowDashboardAPI.getProjectTimeline(projectId as number),
    enabled: Boolean(projectId),
  });
}
