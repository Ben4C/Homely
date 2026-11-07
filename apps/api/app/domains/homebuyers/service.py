"""Dev 1: homebuyer matching services."""
from app.domains.funding_manager.service import list_programs
from .schemas import HomebuyerProfile, MatchResponse, MatchResult


# Purpose: Evaluate geographic compatibility without claiming full financial eligibility.
# Inputs: HomebuyerProfile and a public program listing from the manager service.
# Outputs: MatchResult with explanations and conservative preliminary status.
# TODO(prod): Versioned income limits, affordability and stackability checks, evidence requirements, lawfulness tests.
def assess_program(profile: HomebuyerProfile, program) -> MatchResult:
    if profile.county.casefold() != program.county.casefold():
        return MatchResult(
            program_id=program.id, program_name=program.name, outcome="OUTSIDE_SERVICE_AREA",
            explanations=["County does not match the example program's service area."],
        )
    return MatchResult(
        program_id=program.id, program_name=program.name, outcome="NEEDS_MANUAL_REVIEW",
        explanations=["Geography appears relevant.", "Current funding and all eligibility conditions are unverified."],
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
