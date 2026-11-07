"""Dev 5: project planning and funding-gap arithmetic."""
from decimal import Decimal
from app.core.money import usd
from .fixtures import SYNTHETIC_PROJECTS
from .schemas import ProjectListResponse, GapRequest, GapResponse


# Purpose: Show fictional affordable housing development examples for a starter dashboard.
# Inputs: None, later developer organization + access filters.
# Outputs: ProjectListResponse with synthetic project records.
def list_projects() -> ProjectListResponse:
    return ProjectListResponse(projects=SYNTHETIC_PROJECTS)


# Purpose: Calculate the remaining *development* funding gap without double-counting buyer aid.
# Inputs: GapRequest fields for project cost, affordable buyer proceeds, subsidies, revenue,
#         donations, and employer sponsorship (all USD, separate confirmed categories).
# Outputs: GapResponse showing total sources, nonnegative remaining gap and surplus.
# TODO(prod): Dated affordability model, provenance, approved commitments, mortgage sensitivity, compliance.
def calculate_gap(request: GapRequest) -> GapResponse:
    cost = usd(request.cost_to_create_usd)
    sources = sum([
        usd(request.affordable_buyer_proceeds_usd),
        usd(request.public_development_subsidies_usd),
        usd(request.earned_project_revenue_usd),
        usd(request.nonprofit_donations_usd),
        usd(request.employer_project_sponsorship_usd),
    ], Decimal("0.00"))
    return GapResponse(
        total_funding_usd=sources,
        cost_to_create_usd=cost,
        remaining_gap_usd=max(Decimal("0.00"), cost - sources),
        surplus_usd=max(Decimal("0.00"), sources - cost),
        explanation="Demo arithmetic using user-provided assumptions; funds are not verified or committed.",
    )
