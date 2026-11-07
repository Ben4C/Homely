from fastapi import APIRouter
from .schemas import EmployerProgramListResponse, EmployerCheckRequest, EmployerCheckResponse
from . import service
router = APIRouter()


# Purpose: List synthetic EAH program types available for a demo screen.
# Inputs: Empty GET request.
# Outputs: EmployerProgramListResponse.
@router.get("/employers/programs", response_model=EmployerProgramListResponse)
def employer_programs() -> EmployerProgramListResponse:
    return service.list_employer_programs()


# Purpose: Provide an employer-assisted housing pre-screen with explicit consent.
# Inputs: EmployerCheckRequest JSON payload.
# Outputs: EmployerCheckResponse describing required manual checks.
@router.post("/employers/check", response_model=EmployerCheckResponse)
def employer_check(body: EmployerCheckRequest) -> EmployerCheckResponse:
    return service.check_employer_program(body)


# Purpose: Preview fictional employer matching gift, without payment or verification.
# Inputs: MatchingGiftRequest; outputs capped MatchingGiftResponse.
from .sponsorship import (MatchingGiftRequest, MatchingGiftResponse, SponsorshipPreviewRequest,
                          SponsorshipPreviewResponse, preview_match, preview_sponsorship)

@router.post("/employers/matching-preview", response_model=MatchingGiftResponse)
def matching_preview(body: MatchingGiftRequest) -> MatchingGiftResponse:
    return preview_match(body)


# Purpose: Preview nonprofit project sponsorship, keeping cash and in-kind separate.
# Inputs: SponsorshipPreviewRequest; outputs unverified preview, zero allocatable funds.
@router.post("/employers/sponsorship-preview", response_model=SponsorshipPreviewResponse)
def sponsorship_preview(body: SponsorshipPreviewRequest) -> SponsorshipPreviewResponse:
    return preview_sponsorship(body)
