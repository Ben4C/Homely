"""Dev 4: deterministic corporate matching and sponsorship calculations, preview only."""
from decimal import Decimal
from typing import Literal
from fastapi import HTTPException
from pydantic import BaseModel, Field
from app.core.money import usd


class MatchingGiftRequest(BaseModel):
    employer_program_id: str
    employee_donation_usd: Decimal = Field(gt=0, le=1000000, decimal_places=2)
    verified_eligible_donation: bool = False


class MatchingGiftResponse(BaseModel):
    demo: bool = True
    employer_program_id: str
    requested_donation_usd: Decimal
    possible_employer_match_usd: Decimal
    total_potential_support_usd: Decimal
    status: Literal["PREVIEW_ONLY"] = "PREVIEW_ONLY"
    limitations: list[str]


class SponsorshipPreviewRequest(BaseModel):
    employer_label: str = Field(min_length=1, max_length=100)
    campaign_id: str
    amount_usd: Decimal = Field(gt=0, le=100000000, decimal_places=2)
    contribution_kind: Literal["CASH", "IN_KIND"]


class SponsorshipPreviewResponse(BaseModel):
    demo: bool = True
    campaign_id: str
    contribution_kind: Literal["CASH", "IN_KIND"]
    proposed_usd: Decimal
    available_for_allocation_usd: Decimal = Decimal("0.00")
    status: Literal["UNVERIFIED_PREVIEW"] = "UNVERIFIED_PREVIEW"
    next_steps: list[str]


# Purpose: Compute a potential matching gift under a fictitious employer policy.
# Inputs: MatchingGiftRequest, synthetic fixed 1:1 policy with $500 cap, $20k program budget.
# Outputs: Candidate match amount only; nothing is reserved/paid.
# TODO(prod): Authorized employer-specific policy lookup, actual per-employee history and budget locks.
def preview_match(request: MatchingGiftRequest) -> MatchingGiftResponse:
    if request.employer_program_id != "demo-employer-match":
        raise HTTPException(404, "Demo matching policy not found")
    donation = usd(request.employee_donation_usd)
    # Eligibility is not verified on this platform; even a user-attested flag is not proof.
    candidate = min(donation, Decimal("500.00"), Decimal("20000.00"))
    return MatchingGiftResponse(
        employer_program_id=request.employer_program_id, requested_donation_usd=donation,
        possible_employer_match_usd=candidate,
        total_potential_support_usd=donation + candidate,
        limitations=[
            "Illustrative 1:1 matching policy and $500 cap; no real employer is offering this program.",
            "Employee status, donation eligibility, policy limits, and remaining budget require administrator verification.",
            "No payment, pledge, fund reservation, or tax determination has occurred.",
        ],
    )


# Purpose: Preview sponsor support to a fictional nonprofit campaign without changing project funds.
# Inputs: Sponsor name, campaign ID, cash/in-kind classification, proposed USD value.
# Outputs: UNVERIFIED_PREVIEW, zero amount available for actual allocation, required confirmations.
# TODO(prod): Sponsorship agreements, in-kind acceptance/valuation, ledger integration with Dev 3.
def preview_sponsorship(request: SponsorshipPreviewRequest) -> SponsorshipPreviewResponse:
    from app.domains.donors.fixtures import SYNTHETIC_CAMPAIGNS
    if not any(c.id == request.campaign_id for c in SYNTHETIC_CAMPAIGNS):
        raise HTTPException(404, "Campaign not found")
    steps = ["Confirm sponsor identity and authorized signatory.", "Obtain nonprofit approval and signed terms."]
    if request.contribution_kind == "IN_KIND":
        steps.append("Validate item usefulness and avoided project costs; do not book as received cash.")
    else:
        steps.append("Verify received funds before treating as available for allocation.")
    return SponsorshipPreviewResponse(campaign_id=request.campaign_id, contribution_kind=request.contribution_kind,
                                      proposed_usd=usd(request.amount_usd), next_steps=steps)
