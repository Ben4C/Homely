from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field


class FundingProgram(BaseModel):
    id: str
    organization_id: str
    name: str
    county: str
    assistance_type: str
    max_assistance_usd: Decimal = Field(ge=0)
    source_url: str | None = None
    last_verified_at: str | None = None
    availability: Literal["DEMO_UNVERIFIED", "VERIFIED_OPEN", "VERIFIED_CLOSED", "WAITLIST", "UNKNOWN"]
    eligibility_summary: str


class ProgramListResponse(BaseModel):
    demo: bool = True
    programs: list[FundingProgram]


class ProgramCheckRequest(BaseModel):
    program_id: str


class ProgramCheckResponse(BaseModel):
    program_id: str
    result: Literal["REQUIRES_SOURCE_VERIFICATION"] = "REQUIRES_SOURCE_VERIFICATION"
    next_action: str


class ApplicationCreate(BaseModel):
    program_id: str
    homebuyer_profile_id: str = Field(min_length=1)
    consent_to_share: bool


class ApplicationResponse(BaseModel):
    application_id: str
    status: Literal["DRAFT_PREVIEW"] = "DRAFT_PREVIEW"
    demo: bool = True
    message: str


class ApplicationSummary(BaseModel):
    id: str
    program_id: str
    status: str
    applicant_label: str
    missing_documents: list[str] = Field(default_factory=list)
    updated_at: str | None = None
    last_reviewed_by: str | None = None


class ApplicationListResponse(BaseModel):
    demo: bool = True
    applications: list[ApplicationSummary]
