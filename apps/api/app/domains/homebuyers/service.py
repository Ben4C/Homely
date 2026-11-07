"""Dev 1: homebuyer matching services."""
from app.domains.funding_manager.service import list_programs
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
            program_id=program.id, program_name=program.name, outcome="OUTSIDE_SERVICE_AREA",
            explanations=["County does not match the listed service area; geographic eligibility is not met."],
            source_url=program.source_url, last_verified_at=program.last_verified_at,
            availability=program.availability,
        )
    return MatchResult(
        program_id=program.id, program_name=program.name, outcome="NEEDS_MANUAL_REVIEW",
        explanations=explanations,
        source_url=program.source_url, last_verified_at=program.last_verified_at,
        availability=program.availability,
    )


# Purpose: Produce preliminary program matches for a prospective homebuyer.
# Inputs: HomebuyerProfile with county, household size, income and optional employer.
# Outputs: MatchResponse, never an approval or guarantee of available money.
# TODO(prod): Source-verified rules, privacy controls, consent, program ranking and audit traces.
def match_homebuyer(profile: HomebuyerProfile) -> MatchResponse:
    programs = list_programs().programs
    return MatchResponse(
        disclaimer="Synthetic demo: these are not current funding offers or eligibility approvals.",
        matches=[assess_program(profile, program) for program in programs],
    )
