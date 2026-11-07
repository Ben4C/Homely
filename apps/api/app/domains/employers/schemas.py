from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field


class EmployerProgram(BaseModel):
    id: str
    employer_label: str
    program_name: str
    county: str
    assistance_type: Literal["EMPLOYEE_DOWN_PAYMENT", "NONPROFIT_PROJECT_SPONSORSHIP"]
    award_cap_usd: Decimal = Field(ge=0)
    status: Literal["DEMO_UNVERIFIED"] = "DEMO_UNVERIFIED"


class EmployerProgramListResponse(BaseModel):
    demo: bool = True
    programs: list[EmployerProgram]


class EmployerCheckRequest(BaseModel):
    program_id: str
    county: str
    tenure_months: int = Field(ge=0, le=900)
    employee_consent: bool


class EmployerCheckResponse(BaseModel):
    demo: bool = True
    result: Literal["REQUIRES_VERIFICATION", "OUTSIDE_SERVICE_AREA"]
    required_steps: list[str]
