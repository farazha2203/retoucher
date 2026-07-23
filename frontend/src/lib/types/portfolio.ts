export interface PortfolioComment {
  id: number;
  username: string;
  body: string;
  status: string;
  is_edited: boolean;
  created_at: string;
  replies: PortfolioComment[];
}

export interface PortfolioSocialItem {
  id: number;
  editor_id: number;
  editor_name: string;
  title: string;
  description: string;
  style_title: string | null;
  before_image: string | null;
  after_image: string | null;
  is_featured: boolean;
  likes_count: number;
  comments_count: number;
  is_liked: boolean;
  comments: PortfolioComment[];
}
