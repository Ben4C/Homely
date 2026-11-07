"""Dev 1: homebuyer matching services."""

from app.domains.funding_manager.service import list_programs
import os
from contextlib import contextmanager
from app.core.database import directory_session
from app.data.repository import search_programs
from .schemas import HomebuyerProfile, MatchResponse, MatchResult


# Purpose: Evaluate geographic compatibility without claiming full financial eligibility.
# Inputs: HomebuyerProfile and a public program listing from the manager service.
# Outputs: MatchResult with explanations and conservative preliminary status.
# TODO(prod): Versioned income limits, affordability and stackability checks, evidence requirements, lawfulness tests.
def assess_program(profile: HomebuyerProfile, program) -> MatchResult:
    """Assess known service geography and explain criteria that lack verified rules."""
    explanations = [
        "County matches the program's listed service area.",
        "Income limit is unknown; no income eligibility conclusion can be made.",
        "Household-size rules are unknown; manual review is required.",
        "First-time buyer requirements are unknown; manual review is required.",
        "Program rules and funding availability are unverified; the required document list is unknown, so missing evidence cannot be assessed yet.",
    ]
    if profile.county.casefold() != program.county.casefold():
        return MatchResult(
            program_id=program.id,
            program_name=program.name,
            outcome="OUTSIDE_SERVICE_AREA",
            explanations=[
                "County does not match the listed service area; geographic eligibility is not met."
            ],
            source_url=program.source_url,
            last_verified_at=program.last_verified_at,
            availability=program.availability,
        )
    return MatchResult(
        program_id=program.id,
        program_name=program.name,
        outcome="NEEDS_MANUAL_REVIEW",
        explanations=explanations,
        source_url=program.source_url,
        last_verified_at=program.last_verified_at,
        availability=program.availability,
    )


# Purpose: Produce preliminary program matches for a prospective homebuyer.
# Inputs: HomebuyerProfile with county, household size, income and optional employer.
# Outputs: MatchResponse, never an approval or guarantee of available money.
# Database mode screens reviewed rule versions; production applicant privacy and consent storage remain future work.
def match_homebuyer(profile: HomebuyerProfile, session=None) -> MatchResponse:
    if os.getenv("REGISTRY_MODE", "database") != "demo":
        if session is None:
            with contextmanager(directory_session)() as db_session:
                return match_homebuyer(profile, db_session)
        result = search_programs(
            session,
            county=profile.purchase_county or profile.county,
            city=profile.purchase_city,
            zip_code=profile.purchase_zip,
            residence_county=profile.residence_county or profile.county,
            residence_city=profile.residence_city,
            household_income=profile.annual_income_usd,
            household_size=profile.household_size,
            first_time_buyer=profile.first_time_buyer,
            employer=profile.employer_name,
            purchase_price=profile.purchase_price_usd,
            page_size=10000,
        )
        return MatchResponse(
            demo=False,
            disclaimer=result["disclaimer"],
            matches=[
                MatchResult(
                    program_id=p["id"],
                    program_name=p["name"],
                    outcome=p["outcome"],
                    explanations=p["explanations"],
                    source_url=p["source_url"],
                    last_verified_at=(
                        p["last_verified_at"].isoformat()
                        if p["last_verified_at"]
                        else None
                    ),
                    availability=p["availability"],
                    verified_open=p["availability"] == "VERIFIED_OPEN",
                    application_url=p["application_url"],
                    detail_url="/funding-programs/" + p["id"],
                    channel=p["channel"],
                    max_assistance_usd=p["max_assistance_usd"],
                )
                for p in result["programs"]
            ],
        )
    programs = list_programs().programs
    return MatchResponse(
        disclaimer="Synthetic demo: these are not current funding offers or eligibility approvals.",
        matches=[assess_program(profile, program) for program in programs],
    )
