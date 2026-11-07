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
#         Optional itemized costs replace the aggregate; additional classified sources are additive.
# Outputs: GapResponse showing source breakdown, percentages, potential/excluded amounts, gap and surplus.
# Constraints: Decimal only; legacy financing remains user assumptions. Include only confirmed/received
# development cash from classified sources; callers must not repeat a source in legacy totals.
# TODO(prod): Dated affordability model, provenance, approved commitments, mortgage sensitivity, compliance.
def calculate_gap(request: GapRequest) -> GapResponse:
    cost = usd(request.cost_to_create_usd)
    if request.itemized_costs is not None:
        cost = sum((usd(value) for value in request.itemized_costs.model_dump().values()), Decimal('0.00'))
    breakdown = {name: usd(getattr(request, name)) for name in (
        'affordable_buyer_proceeds_usd', 'public_development_subsidies_usd',
        'earned_project_revenue_usd', 'nonprofit_donations_usd', 'employer_project_sponsorship_usd')}
    potential = Decimal('0.00')
    excluded = Decimal('0.00')
    for source in request.funding_sources:
        amount = usd(source.amount_usd)
        if source.funding_track == 'BUYER' or source.contribution_kind == 'IN_KIND':
            excluded += amount
        elif source.status in {'CONFIRMED', 'RECEIVED'}:
            breakdown[f'source:{source.id}'] = amount
        else:
            potential += amount
    sources = sum(breakdown.values(), Decimal('0.00'))
    return GapResponse(
        total_funding_usd=sources,
        source_breakdown=breakdown,
        source_percentages={name: (amount * 100 / cost).quantize(Decimal('0.01')) if cost else Decimal('0.00')
                            for name, amount in breakdown.items()},
        potential_funding_usd=potential,
        excluded_funding_usd=excluded,
        financing_identified_percent=(sources * 100 / cost).quantize(Decimal('0.01')) if cost else Decimal('0.00'),
        cost_to_create_usd=cost,
        remaining_gap_usd=max(Decimal("0.00"), cost - sources),
        surplus_usd=max(Decimal("0.00"), sources - cost),
        explanation='Synthetic planning arithmetic: legacy inputs are entered financing assumptions. Additional sources count only confirmed or received development cash; pledges, buyer assistance and in-kind support are excluded. Enter each source once. Itemized costs replace the aggregate cost when provided.',
    )
