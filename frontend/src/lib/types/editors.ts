export interface EditorSkill {
  id: number;
  title: string;
  slug: string;
}

export interface EditorPortfolioItem {
  id: number;
  title: string;
  description: string;
  style: number | null;
  style_title: string | null;
  before_image: string | null;
  after_image: string | null;
  is_featured: boolean;
}

export interface EditorProfile {
  id: number;
  user: number;
  username: string;
  display_name: string;
  bio: string;
  level: string;
  skills: EditorSkill[];
  base_price: number;
  average_delivery_hours: number;
  rating_average: string | number;
  completed_orders_count: number;
  is_available: boolean;
  accepts_direct_requests: boolean;
  accepts_public_requests: boolean;
  accepts_sample_challenges: boolean;
  portfolio_items?: EditorPortfolioItem[];
}
