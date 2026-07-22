import type { WorkflowSummary } from '@/lib/types/workflow';

export interface ProjectRequestListItem {
  id: number;
  title: string;
  request_type: string;
  request_type_display?: string;
  status: string;
  status_display?: string;
  client?: number;
  client_username?: string;
  preferred_deadline?: string | null;
  image_count?: number;
  created_at?: string;
  updated_at?: string;
  workflow: WorkflowSummary;
}
