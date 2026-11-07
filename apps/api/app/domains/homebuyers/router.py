from fastapi import APIRouter, Depends
from app.core.database import legacy_directory_session
from .schemas import HomebuyerProfile, MatchRequest, MatchResponse
from .fixtures import SYNTHETIC_PROFILE
from . import service
router = APIRouter()


# Purpose: Return a fictional profile to demonstrate buyer onboarding fields.
# Inputs: Empty GET request.
# Outputs: HomebuyerProfile with synthetic data.
@router.get("/homebuyers/profile-template", response_model=HomebuyerProfile)
def profile_template() -> HomebuyerProfile:
    return SYNTHETIC_PROFILE


# Purpose: Generate explanation-first preliminary program matches.
# Inputs: MatchRequest JSON including a homebuyer profile.
# Outputs: MatchResponse with conservative results (no approval).
@router.post("/homebuyers/match", response_model=MatchResponse)
def match(body: MatchRequest, session=Depends(legacy_directory_session)) -> MatchResponse:
    return service.match_homebuyer(body.profile,session)


# Purpose: Send a consented sample applicant document to Claude for nonbinding readiness review.
# Inputs: DocumentReviewRequest with one text/PDF source and a document checklist.
# Outputs: DocumentReviewResponse; never a final eligibility decision or stored application.
from .ai_document import DocumentReviewRequest, DocumentReviewResponse, review_document

@router.post("/homebuyers/ai-document-review", response_model=DocumentReviewResponse)
async def ai_document_review(body: DocumentReviewRequest) -> DocumentReviewResponse:
    return await review_document(body)
