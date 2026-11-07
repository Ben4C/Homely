from decimal import Decimal
from pydantic import BaseModel, Field


class HousingProject(BaseModel):
    id: str
    project_name: str
    county: str
    units: int = Field(ge=1)
    status: str


class ProjectListResponse(BaseModel):
    demo: bool = True
    projects: list[HousingProject]


class GapRequest(BaseModel):
    cost_to_create_usd: Decimal = Field(ge=0, decimal_places=2)
    affordable_buyer_proceeds_usd: Decimal = Field(ge=0, decimal_places=2)
    public_development_subsidies_usd: Decimal = Field(ge=0, decimal_places=2)
    earned_project_revenue_usd: Decimal = Field(ge=0, decimal_places=2)
    nonprofit_donations_usd: Decimal = Field(ge=0, decimal_places=2)
    employer_project_sponsorship_usd: Decimal = Field(ge=0, decimal_places=2)


class GapResponse(BaseModel):
    demo: bool = True
    total_funding_usd: Decimal
    cost_to_create_usd: Decimal
    remaining_gap_usd: Decimal
    surplus_usd: Decimal
    explanation: str
