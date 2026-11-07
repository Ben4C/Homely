"""Dev 5: Claude explains candidate funding; deterministic arithmetic remains authoritative."""
from decimal import Decimal
import json
from typing import Literal
from pydantic import BaseModel, Field
from app.core.claude_client import claude_json
from .schemas import GapRequest, GapResponse
from .service import calculate_gap


class CandidateFundingSource(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=140)
    funding_track: Literal["DEVELOPMENT", "BUYER"]
    type: Literal["GOVERNMENT", "NONPROFIT", "EMPLOYER", "DONOR", "LENDER"]
    proposed_amount_usd: Decimal = Field(ge=0, decimal_places=2)
    availability: Literal["UNVERIFIED", "CONFIRMED_BY_MANAGER", "CLOSED"]
    program_terms: str = Field(max_length=1500)
    source_url: str | None = None


class FundingAdviceRequest(BaseModel):
    financials: GapRequest
    sources: list[CandidateFundingSource] = Field(min_length=1, max_length=12)
    question: str = Field(default="How could we close the development gap?", max_length=600)
    consent_to_send_to_claude: bool


class AdviceItem(BaseModel):
    source_id: str
    opportunity_or_constraint: str
    missing_verification: str


class FundingAdviceAnalysis(BaseModel):
    overall_explanation: str
    source_assessments: list[AdviceItem]
    potential_stack_conflicts: list[str]
    next_actions: list[str]


class FundingAdviceResponse(FundingAdviceAnalysis):
    demo: bool = True
    ai_generated: bool = True
    human_review_required: bool = True
    deterministic_gap: GapResponse
    disclaimer: str = "Claude advice is nonbinding; candidate awards are not approved, stackable, or spendable without verified program review."


# Purpose: Explain potential development financing opportunities without adding unverified awards to the ledger.
# Inputs: Financial assumptions and explicitly classified candidate sources (max 12), consent flag.
# Outputs: Claude's sourced-to-input discussion plus authoritative deterministic gap calculation.
# TODO(prod): Consume only verified current programs, add eligibility graph and finance manager signoff.
async def advise_funding(request: FundingAdviceRequest) -> FundingAdviceResponse:
    from fastapi import HTTPException
    if not request.consent_to_send_to_claude:
        raise HTTPException(400, "Consent required to send financial assumptions to Claude")
    ids = [source.id for source in request.sources]
    if len(set(ids)) != len(ids):
        raise HTTPException(422, "Funding source IDs must be unique")
    gap = calculate_gap(request.financials)
    payload = {
        "question": request.question,
        "deterministic_gap_usd": str(gap.remaining_gap_usd),
        "source_candidates_NOT_awards": [s.model_dump(mode="json") for s in request.sources],
    }
    prompt = (
        "Explain financing options using ONLY the candidate sources and calculated gap included in the input. "
        "Clearly distinguish DEVELOPMENT from BUYER assistance (do not add buyer-specific grants to "
        "development receipts), unverified sources from confirmed commitments, and incompatible or "
        "unknown stacking rules. Do not redo or override financial arithmetic. "
        "For each candidate, use only the exact supplied source_id. Do not invent opportunities."
    )
    result = await claude_json(prompt, [{"type": "text", "text": json.dumps(payload)}], FundingAdviceAnalysis)
    # Do not render fabricated program IDs even if Claude emits one.
    result.source_assessments = [item for item in result.source_assessments if item.source_id in ids]
    return FundingAdviceResponse(**result.model_dump(), deterministic_gap=gap)
