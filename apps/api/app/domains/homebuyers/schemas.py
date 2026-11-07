from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field


class HomebuyerProfile(BaseModel):
    profile_id: str = Field(min_length=1)
    county: str = Field(min_length=1)
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
    outcome: Literal["NEEDS_MANUAL_REVIEW", "OUTSIDE_SERVICE_AREA"]
    explanations: list[str]
    verified_open: bool = False


class MatchResponse(BaseModel):
    demo: bool = True
    disclaimer: str
    matches: list[MatchResult]
