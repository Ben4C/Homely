export interface ReviewItem {
  id: string;
  category: string;
  reason: string;
  status: string;
  organization_id: string | null;
  source_verified_on: string | null;
  application_deadline: string | null;
  eligibility_verified: boolean;
  review_flags: string[];
}
export interface AdminReviewResponse {
  demo: boolean;
  items: ReviewItem[];
  metrics: Record<string, number>;
  warnings: string[];
  decisions_enabled: boolean;
}
