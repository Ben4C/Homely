from pydantic import BaseModel


class ReviewItem(BaseModel):
    id: str
    category: str
    reason: str
    status: str


class AdminReviewResponse(BaseModel):
    demo: bool = True
    items: list[ReviewItem]
