import type { WorkflowSummary } from '@/lib/types/workflow';

export interface OrderListItem {
  id: number;
  title: string;
  description?: string;
  status: string;
  status_display?: string;
  client?: number;
  client_username?: string;
  editor?: number | null;
  editor_username?: string | null;
  deadline?: string | null;
  created_at?: string;
  updated_at?: string;
  workflow: WorkflowSummary;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
