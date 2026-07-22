// Generated frontend contract for Retoucher API v1.
// Keep this file synchronized with backend/docs/frontend_contract.v1.json.

export type WorkflowEntityType = "order" | "project_request";

export type DeadlineState =
  | "active"
  | "met"
  | "missed"
  | "cancelled"
  | null;

export interface WorkflowStage {
  key: string;
  title_fa: string;
  title_en: string;
}

export interface WorkflowDeadline {
  at: string | null;
  state: DeadlineState;
  is_overdue: boolean;
  stage?: string | null;
  owner_role?: string | null;
  timeout_action?: string | null;
}

export interface WorkflowSummary {
  workflow_type: WorkflowEntityType;
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
  entity_type: WorkflowEntityType;
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

export interface JwtTokenPair {
  access: string;
  refresh: string;
}

export interface JwtRefreshResponse {
  access: string;
  refresh?: string;
}
