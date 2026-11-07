from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field


class Campaign(BaseModel):
    id: str
    organization_id: str
    project_id: str
    title: str
    remaining_project_gap_usd: Decimal = Field(ge=0, decimal_places=2)
    status: Literal["SYNTHETIC"] = "SYNTHETIC"


class CampaignListResponse(BaseModel):
    demo: bool = True
    campaigns: list[Campaign]


class PledgePreviewRequest(BaseModel):
    campaign_id: str
    amount_usd: Decimal = Field(gt=0, le=100000000, decimal_places=2)


class PledgePreviewResponse(BaseModel):
    demo: bool = True
    amount_usd: Decimal
    campaign_id: str
    status: Literal["NOT_SUBMITTED"] = "NOT_SUBMITTED"
    message: str


class AllocationPreviewRequest(BaseModel):
    total_available_usd: Decimal = Field(ge=0, le=100000000, decimal_places=2)


class AllocationLine(BaseModel):
    campaign_id: str
    suggested_usd: Decimal = Field(ge=0, decimal_places=2)
    reason: str


class AllocationPreviewResponse(BaseModel):
    demo: bool = True
    lines: list[AllocationLine]
    unallocated_usd: Decimal = Field(ge=0, decimal_places=2)
    message: str
