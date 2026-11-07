"""Dev 3: donor program and preview-only allocation logic."""
from decimal import Decimal
from fastapi import HTTPException
from app.core.money import usd
from .fixtures import SYNTHETIC_CAMPAIGNS
from .schemas import (
    CampaignListResponse, PledgePreviewRequest, PledgePreviewResponse,
    AllocationPreviewRequest, AllocationPreviewResponse, AllocationLine,
)


# Purpose: Return a set of organization-controlled synthetic fundraising campaigns.
# Inputs: None in demo; later filter by county, organization verification, campaign restrictions.
# Outputs: CampaignListResponse with no active real campaigns.
def list_campaigns() -> CampaignListResponse:
    return CampaignListResponse(campaigns=SYNTHETIC_CAMPAIGNS)


# Purpose: Validate a donation intent without charging a payment method or reserving funds.
# Inputs: PledgePreviewRequest campaign ID and positive USD amount.
# Outputs: PledgePreviewResponse in NOT_SUBMITTED state.
# TODO(prod): Restricted gift agreement, charity verification, payment provider and reconciliation.
def preview_pledge(request: PledgePreviewRequest) -> PledgePreviewResponse:
    if not any(c.id == request.campaign_id for c in SYNTHETIC_CAMPAIGNS):
        raise HTTPException(404, "Campaign not found")
    amount = usd(request.amount_usd)
    if amount <= 0:
        raise HTTPException(400, "Pledge must be positive")
    return PledgePreviewResponse(
        campaign_id=request.campaign_id, amount_usd=amount,
        message="Demo only: no donation was submitted, charged, reserved, or allocated.",
    )


# Purpose: Preview allocation of unrestricted hypothetical funding to eligible campaigns in queue order.
# Inputs: AllocationPreviewRequest containing an illustrative available balance.
# Outputs: AllocationPreviewResponse with recommendations only; never financial commitments.
# TODO(prod): Donor restrictions, manager authorization, queue priority versioning, approval audit, DB transactions.
def preview_allocations(request: AllocationPreviewRequest) -> AllocationPreviewResponse:
    remaining = usd(request.total_available_usd)
    result: list[AllocationLine] = []
    for campaign in SYNTHETIC_CAMPAIGNS:
        proposed = min(remaining, campaign.remaining_project_gap_usd)
        if proposed:
            result.append(AllocationLine(
                campaign_id=campaign.id, suggested_usd=proposed,
                reason="Illustrative queue order only; actual restricted funding priorities must be authorized.",
            ))
        remaining -= proposed
    return AllocationPreviewResponse(
        lines=result, unallocated_usd=remaining,
        message="Preview only. No funds moved and no project commitments created.",
    )
