export interface ReviewItem { id: string; category: string; reason: string; status: string }
export interface AdminReviewResponse { demo: boolean; items: ReviewItem[] }
