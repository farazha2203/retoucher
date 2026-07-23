export type PortfolioReviewStatus = 'draft' | 'pending' | 'approved' | 'rejected';

export interface EditorWorkspacePortfolioItem {
  id: number;
  title: string;
  description: string;
  before_image: string | null;
  after_image: string | null;
  is_active: boolean;
  is_featured: boolean;
  review_status: PortfolioReviewStatus;
  review_note: string;
}

export interface EditorWorkspaceProfile {
  id: number;
  username: string;
  display_name: string;
  bio: string;
  level: string;
  base_price: number;
  average_delivery_hours: number;
  rating_average: string | number;
  completed_orders_count: number;
  is_available: boolean;
  accepts_direct_requests: boolean;
  accepts_public_requests: boolean;
  accepts_sample_challenges: boolean;
  portfolio_items: EditorWorkspacePortfolioItem[];
}
