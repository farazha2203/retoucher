export interface WorkflowStage {
  key: string;
  title_fa: string;
  title_en: string;
}

export interface WorkflowDeadline {
  at: string | null;
  state: 'active' | 'met' | 'missed' | 'cancelled' | null;
  is_overdue: boolean;
  stage?: string | null;
  owner_role?: string | null;
  timeout_action?: string | null;
}

export interface WorkflowSummary {
  workflow_type: 'order' | 'project_request';
  request_type?: string;
  status: string;
  stage: WorkflowStage;
  progress_percent: number;
  terminal: boolean;
  successful: boolean;
  waiting_for_role: string | null;
  next_action: string | null;
  deadline: WorkflowDeadline | null;
}

export interface TimelineActor {
  id: number;
  username: string;
}

export interface TimelineEvent {
  event_id: string;
  event_key: string;
  entity_type: 'order' | 'project_request';
  entity_id: number;
  source: string;
  actor: TimelineActor | null;
  from_status?: string | null;
  to_status?: string | null;
  message: string;
  metadata: Record<string, unknown>;
  occurred_at: string;
}

export interface TimelineResponse {
  workflow: WorkflowSummary;
  events: TimelineEvent[];
}
