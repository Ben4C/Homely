from fastapi import APIRouter
from .schemas import (
    ProgramListResponse, ProgramCheckRequest, ProgramCheckResponse,
    ApplicationCreate, ApplicationResponse, ApplicationListResponse,
)
from . import service
router = APIRouter()


# Purpose: List geographically relevant funding programs and verifiable metadata.
# Inputs: Optional county query string.
# Outputs: ProgramListResponse (demo records; no live funds claimed).
@router.get("/programs", response_model=ProgramListResponse)
def programs(county: str | None = None) -> ProgramListResponse:
    return service.list_programs(county)


# Purpose: Initiate a program source/availability verification check.
# Inputs: ProgramCheckRequest JSON object.
# Outputs: ProgramCheckResponse with next verification action.
@router.post("/programs/check", response_model=ProgramCheckResponse)
def program_check(body: ProgramCheckRequest) -> ProgramCheckResponse:
    return service.check_program(body)


# Purpose: Preview an application intake workflow, not submit a real request.
# Inputs: ApplicationCreate JSON payload and consent flag.
# Outputs: ApplicationResponse with explicit demo status.
@router.post("/applications", response_model=ApplicationResponse)
def application_create(body: ApplicationCreate) -> ApplicationResponse:
    return service.create_application(body)


# Purpose: Display a manager's applicant review queue.
# Inputs: None in demo; production requires organization-scoped auth.
# Outputs: ApplicationListResponse with synthetic cases.
@router.get("/applications", response_model=ApplicationListResponse)
def applications() -> ApplicationListResponse:
    return service.list_applications()


# Purpose: Ask Claude to draft program rules from a consented source PDF/text.
# Inputs: ProgramExtractRequest; outputs an unpublished ProgramExtractResponse for manager verification.
from .ai_program import ProgramExtractRequest, ProgramExtractResponse, extract_program

@router.post("/programs/ai-extract", response_model=ProgramExtractResponse)
async def ai_extract_program(body: ProgramExtractRequest) -> ProgramExtractResponse:
    return await extract_program(body)
