from decimal import Decimal
from typing import Annotated, Literal
from pydantic import BaseModel, Field, model_validator

Money = Annotated[Decimal, Field(ge=0, max_digits=16, decimal_places=2, allow_inf_nan=False)]


class DevelopmentCosts(BaseModel):
    land: Money = Decimal('0')
    construction: Money = Decimal('0')
    rehabilitation: Money = Decimal('0')
    carrying: Money = Decimal('0')
    financing: Money = Decimal('0')
    fees_design_legal: Money = Decimal('0')


class FinancingSource(BaseModel):
    id: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_-]+$')
    category: Literal['PUBLIC', 'NONPROFIT', 'EMPLOYER', 'OTHER']
    amount_usd: Money
    status: Literal['CONFIRMED', 'RECEIVED', 'PLEDGED', 'UNVERIFIED']
    funding_track: Literal['DEVELOPMENT', 'BUYER'] = 'DEVELOPMENT'
    contribution_kind: Literal['CASH', 'IN_KIND'] = 'CASH'


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
    itemized_costs: DevelopmentCosts | None = None
    funding_sources: list[FinancingSource] = Field(default_factory=list, max_length=100)
    cost_to_create_usd: Decimal = Field(ge=0, decimal_places=2)
    affordable_buyer_proceeds_usd: Decimal = Field(ge=0, decimal_places=2)
    public_development_subsidies_usd: Decimal = Field(ge=0, decimal_places=2)
    earned_project_revenue_usd: Decimal = Field(ge=0, decimal_places=2)
    nonprofit_donations_usd: Decimal = Field(ge=0, decimal_places=2)
    employer_project_sponsorship_usd: Decimal = Field(ge=0, decimal_places=2)

    # Purpose: Bound legacy money and prevent duplicate counting of source records.
    # Inputs: Validated pro forma; outputs: compatible request or validation error.
    @model_validator(mode='after')
    def validate_financials(self) -> 'GapRequest':
        for name in type(self).model_fields:
            value = getattr(self, name)
            if isinstance(value, Decimal) and (not value.is_finite() or value > Decimal('99999999999999.99')):
                raise ValueError('Monetary inputs must be finite and at most 14 integer digits')
        ids = [source.id for source in self.funding_sources]
        if len(ids) != len(set(ids)):
            raise ValueError('Funding source IDs must be unique')
        return self


class GapResponse(BaseModel):
    source_breakdown: dict[str, Decimal] = Field(default_factory=dict)
    source_percentages: dict[str, Decimal] = Field(default_factory=dict)
    potential_funding_usd: Decimal = Decimal('0.00')
    excluded_funding_usd: Decimal = Decimal('0.00')
    financing_identified_percent: Decimal = Decimal('0.00')
    demo: bool = True
    total_funding_usd: Decimal
    cost_to_create_usd: Decimal
    remaining_gap_usd: Decimal
    surplus_usd: Decimal
    explanation: str
