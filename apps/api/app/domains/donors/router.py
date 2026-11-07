from fastapi import APIRouter
from .schemas import (
    CampaignListResponse, PledgePreviewRequest, PledgePreviewResponse,
    AllocationPreviewRequest, AllocationPreviewResponse,
)
from . import service
router = APIRouter()


# Purpose: Display verified-organization donation targets; synthetic in scaffold.
# Inputs: Empty GET request.
# Outputs: CampaignListResponse.
@router.get("/donors/campaigns", response_model=CampaignListResponse)
def campaigns() -> CampaignListResponse:
    return service.list_campaigns()


# Purpose: Preview contribution amount and campaign selection without taking payment.
# Inputs: PledgePreviewRequest JSON payload.
# Outputs: PledgePreviewResponse confirming nothing was charged.
@router.post("/donors/pledge-preview", response_model=PledgePreviewResponse)
def pledge_preview(body: PledgePreviewRequest) -> PledgePreviewResponse:
    return service.preview_pledge(body)


# Purpose: Compute a hypothetical queue-based funding suggestion.
# Inputs: AllocationPreviewRequest with total available fictional money.
# Outputs: AllocationPreviewResponse containing nonbinding recommendations.
@router.post("/donors/allocate-preview", response_model=AllocationPreviewResponse)
def allocate_preview(body: AllocationPreviewRequest) -> AllocationPreviewResponse:
    return service.preview_allocations(body)
