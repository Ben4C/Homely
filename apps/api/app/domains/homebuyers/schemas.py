from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field


class HomebuyerProfile(BaseModel):
    profile_id: str = Field(min_length=1)
    county: str = Field(min_length=1)
    purchase_county: str | None = Field(default=None, max_length=120)
    purchase_city: str | None = Field(default=None, max_length=120)
    purchase_zip: str | None = Field(default=None, pattern=r"^\d{5}$")
    residence_county: str | None = Field(default=None, max_length=120)
    residence_city: str | None = Field(default=None, max_length=120)
    purchase_price_usd: Decimal | None = Field(default=None, ge=0)
    household_size: int = Field(ge=1, le=30)
    annual_income_usd: Decimal = Field(ge=0)
    first_time_buyer: bool | None = None
    employer_name: str | None = None
    preferred_language: str = "en"


class MatchRequest(BaseModel):
    profile: HomebuyerProfile


class MatchResult(BaseModel):
    program_id: str
    program_name: str
    outcome: Literal[
        "NEEDS_MANUAL_REVIEW",
        "OUTSIDE_SERVICE_AREA",
        "POTENTIALLY_ELIGIBLE",
        "KNOWN_CRITERIA_NOT_MET",
        "ADDITIONAL_INFORMATION_REQUIRED",
        "PROGRAM_UNAVAILABLE",
        "ELIGIBILITY_NOT_VERIFIED",
    ]
    explanations: list[str]
    application_url: str | None = None
    detail_url: str | None = None
    channel: str | None = None
    max_assistance_usd: Decimal | None = None
    verified_open: bool = False
    source_url: str | None = None
    last_verified_at: str | None = None
    availability: str = "UNKNOWN"


class MatchResponse(BaseModel):
    demo: bool = True
    disclaimer: str
    matches: list[MatchResult]
