from pydantic import BaseModel, Field
from datetime import date


class ReviewItem(BaseModel):
    id: str
    category: str
    reason: str
    status: str
    organization_id: str | None = None
    source_verified_on: date | None = None
    application_deadline: date | None = None
    eligibility_verified: bool = False
    review_flags: list[str] = Field(default_factory=list)


class AdminReviewResponse(BaseModel):
    demo: bool = True
    items: list[ReviewItem]
    metrics: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    decisions_enabled: bool = False
