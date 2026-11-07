from fastapi import APIRouter
from .schemas import ProjectListResponse, GapRequest, GapResponse
from . import service
router = APIRouter()


# Purpose: List fictional developer projects for dashboard display.
# Inputs: Empty GET request.
# Outputs: ProjectListResponse.
@router.get("/projects", response_model=ProjectListResponse)
def projects() -> ProjectListResponse:
    return service.list_projects()


# Purpose: Calculate demo development funding gap from a sources-and-uses model.
# Inputs: GapRequest JSON containing cost and separately classified financing sources.
# Outputs: GapResponse with gap or surplus, not a payment instruction.
@router.post("/projects/gap", response_model=GapResponse)
def project_gap(body: GapRequest) -> GapResponse:
    return service.calculate_gap(body)


# Purpose: Explain candidate funding sources with Claude while calculating actual gap deterministically.
# Inputs: FundingAdviceRequest; outputs advisory notes and unchanged authoritative calculation.
from .ai_advisor import FundingAdviceRequest, FundingAdviceResponse, advise_funding

@router.post("/projects/ai-funding-advice", response_model=FundingAdviceResponse)
async def ai_funding_advice(body: FundingAdviceRequest) -> FundingAdviceResponse:
    return await advise_funding(body)
