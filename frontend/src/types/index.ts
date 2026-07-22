
// ─── Workflow additions for Phase 2.3 ───

export interface WorkflowStage {
  key: string;
  title_fa: string;
  title_en: string;
}

export interface WorkflowDeadline {
  at: string | null;
  state: string | null;
  is_overdue: boolean;
  stage?: string | null;
  owner_role?: string | null;
  timeout_action?: string | null;
}

export interface WorkflowSummary {
  workflow_type: 'order' | 'project_request';
  status: string;
  stage: WorkflowStage;
  progress_percent: number;
  terminal: boolean;
  successful: boolean;
  waiting_for_role: string | null;
  next_action: string | null;
  deadline: WorkflowDeadline | null;
}

export interface WorkflowTimelineActor {
  id: number;
  username: string;
}

export interface WorkflowTimelineEvent {
  event_id: string;
  event_key: string;
  entity_type: 'order' | 'project_request';
  entity_id: number;
  source: string;
  actor: WorkflowTimelineActor | null;
  from_status?: string | null;
  to_status?: string | null;
  message: string;
  metadata: Record<string, unknown>;
  occurred_at: string;
}

export interface OrderTimelineResponse {
  workflow: WorkflowSummary;
  events: WorkflowTimelineEvent[];
}

// ─── User & Auth ───
export type UserRole = 'client' | 'editor' | 'support' | 'supervisor' | 'admin';

export interface User {
  id: number;
  username: string;
  email: string | null;
  phone_number: string | null;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_verified: boolean;
  avatar?: string;
  date_joined: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  role: Extract<UserRole, 'client' | 'editor'>;
  phone_number?: string;
}

// ─── Catalog ───
export interface EditCategory {
  id: number;
  title: string;
  slug: string;
  description: string;
  is_active: boolean;
}

export interface EditStyle {
  id: number;
  category: number;
  title: string;
  slug: string;
  description: string;
  min_price: number;
  max_price: number;
  suggested_price: number;
  estimated_delivery_hours: number;
}

// ─── Project Request ───
export type ProjectRequestType =
  | 'direct_editor'
  | 'public_quote'
  | 'sample_challenge'
  | 'managed_order';

export type ProjectRequestStatus =
  | 'draft'
  | 'submitted'
  | 'open_for_quotes'
  | 'open_for_samples'
  | 'waiting_for_editor'
  | 'under_review'
  | 'editor_selected'
  | 'converted_to_order'
  | 'cancelled'
  | 'expired';

export interface ProjectRequest {
  id: number;
  title: string;
  description: string;
  request_type: ProjectRequestType;
  status: ProjectRequestStatus;
  edit_style: number;
  budget_min?: number;
  budget_max?: number;
  deadline_days?: number;
  submitted_at?: string;
  expires_at?: string;
  is_expired: boolean;
  time_remaining_hours?: number;
  images: ProjectImage[];
  workflow?: WorkflowSummary;
  created_at: string;
}

export interface ProjectImage {
  id: number;
  image: string;
  caption: string;
  sort_order: number;
}

export interface CreateProjectPayload {
  title: string;
  description: string;
  request_type: ProjectRequestType;
  edit_style: number;
  budget_min?: number;
  budget_max?: number;
  deadline_days?: number;
}

// ─── Order ───
export type OrderStatus =
  | 'draft'
  | 'submitted'
  | 'in_review'
  | 'assigned'
  | 'in_progress'
  | 'delivered'
  | 'cancelled'
  | 'client_review'
  | 'revision_required'
  | 'client_revision_requested'
  | 'completed'
  | 'settlement_pending'
  | 'paid'
  | 'closed';

export interface OrderImage {
  id: number;
  image: string;
  note: string;
  uploaded_at: string;
}

export interface OrderDelivery {
  id: number;
  order: number;
  file: string;
  note: string;
  uploaded_by: number | null;
  uploaded_by_username: string | null;
  uploaded_at: string;
  publication_status: 'private' | 'requested' | 'approved' | 'rejected';
  publication_requested_by: number | null;
  publication_requested_at: string | null;
  publication_reviewed_by: number | null;
  publication_reviewed_at: string | null;
  publication_note: string;
  is_public: boolean;
}

export interface OrderRevision {
  id: number;
  source: 'supervisor' | 'client';
  note: string;
  requested_by: number | null;
  requested_by_username: string | null;
  created_at: string;
}

export interface OrderRating {
  id: number;
  source: 'supervisor' | 'client';
  score: number;
  comment: string;
  rated_by: number | null;
  rated_by_username: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrderComment {
  id: number;
  order: number;
  sender: number | null;
  sender_username: string | null;
  target_type: 'order' | 'image' | 'delivery' | 'revision';
  image: number | null;
  delivery: number | null;
  revision: number | null;
  text: string;
  x: number | null;
  y: number | null;
  status: 'active' | 'resolved' | 'approved' | 'deleted';
  is_edited: boolean;
  edited_at: string | null;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
  parent: number | null;
  parent_text: string | null;
  parent_sender_username: string | null;
  is_resolved: boolean;
  resolved_by: number | null;
  resolved_by_username: string | null;
  resolved_at: string | null;
  annotation_type: 'none' | 'point' | 'rectangle' | 'circle' | 'arrow' | 'freehand';
  annotation_label: string;
  annotation_color: string;
  annotation_data: Record<string, unknown>;
  is_publicly_visible: boolean;
  replies?: OrderComment[];
}

export interface OrderStatusHistory {
  id: number;
  order: number;
  changed_by: number | null;
  changed_by_username: string | null;
  from_status: string;
  to_status: string;
  note: string;
  created_at: string;
}

export interface OrderActivityLog {
  id: number;
  order: number;
  actor: number | null;
  actor_username: string | null;
  activity_type: string;
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface Order {
  id: number;

  client: number;
  client_username: string;

  editor: number | null;
  editor_username: string | null;

  title: string;
  description?: string;

  status: OrderStatus;
  revision_count: number;

  supervisor_approved_at: string | null;
  client_approved_at: string | null;
  settlement_started_at?: string | null;
  paid_at?: string | null;
  closed_at?: string | null;

  deadline: string | null;
  workflow?: WorkflowSummary;

  images?: OrderImage[];
  deliveries?: OrderDelivery[];
  revisions?: OrderRevision[];
  ratings?: OrderRating[];
  comments?: OrderComment[];
  status_history?: OrderStatusHistory[];
  activity_logs?: OrderActivityLog[];

  created_at: string;
  updated_at: string;
}



// ─── Wallet ───
export interface Wallet {
  id: number;
  balance: string;
  user: number;
}

export interface Transaction {
  id: number;
  tx_type: string;
  amount: number;
  description: string;
  created_at: string;
}

// ─── API Response ───
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail?: string;
  [key: string]: unknown;
}

// ─── Editors ───
export interface EditorProfile {
  id: number;
  user?: number;
  full_name?: string;
  display_name?: string;
  first_name?: string;
  last_name?: string;
  username?: string;
  email?: string;
  avatar?: string | null;
  profile_image?: string | null;
  bio?: string;
  about?: string;
  city?: string | null;
  province?: string | null;
  rating?: number;
  average_rating?: number;
  completed_orders?: number;
  orders_completed?: number;
  specialties?: string[];
  skills?: string[];
  portfolio?: Array<{
    id: number;
    title?: string;
    image?: string;
    before_image?: string;
    after_image?: string;
    description?: string;
  }>;
}