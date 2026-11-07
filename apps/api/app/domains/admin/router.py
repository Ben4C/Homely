from fastapi import APIRouter
from .schemas import AdminReviewResponse
from . import service
router = APIRouter()


# Purpose: Show fake admin verification queue for routing/UI demonstration only.
# Inputs: Empty GET; future authenticated platform-admin context.
# Outputs: AdminReviewResponse with synthetic items.
@router.get("/admin/review-queue", response_model=AdminReviewResponse)
def review_queue() -> AdminReviewResponse:
    return service.list_review_items()
