"""Dev 2: replace fixture-only behaviors with authorized program management."""
from fastapi import HTTPException
from .fixtures import SYNTHETIC_PROGRAMS, SYNTHETIC_APPLICATIONS
from .schemas import (
    ProgramListResponse, ProgramCheckRequest, ProgramCheckResponse,
    ApplicationCreate, ApplicationResponse, ApplicationListResponse,
)


# Purpose: Return verified-source-aware funding program listings, optionally by county.
# Inputs: county: optional case-insensitive county name; eventually authenticated viewer context.
# Outputs: ProgramListResponse; starter lists SYNTHETIC programs only.
# TODO(prod): Add source verification, real provider IDs, expiry/status checks, SQL query, paging.
def list_programs(county: str | None = None) -> ProgramListResponse:
    programs = SYNTHETIC_PROGRAMS
    if county:
        programs = [p for p in programs if p.county.casefold() == county.strip().casefold()]
    return ProgramListResponse(programs=programs)


# Purpose: Determine whether an authorized manager must reverify a program's rules/status.
# Inputs: ProgramCheckRequest containing program ID.
# Outputs: ProgramCheckResponse with next human verification step; never claims live availability.
# TODO(prod): Validate official source, program owner authority, published date, terms and capacity.
def check_program(request: ProgramCheckRequest) -> ProgramCheckResponse:
    if not any(p.id == request.program_id for p in SYNTHETIC_PROGRAMS):
        raise HTTPException(404, "Program ID not found")
    return ProgramCheckResponse(program_id=request.program_id, next_action="Authorized manager must confirm current official source and funding availability.")


# Purpose: Preview a housing assistance application for the program administrator.
# Inputs: ApplicationCreate with program ID, profile ID, and explicit sharing consent.
# Outputs: ApplicationResponse in DRAFT_PREVIEW status; no real submission or storage.
# TODO(prod): Authenticate, scope owner, enforce consent, persist idempotently, notify reviewers.
def create_application(request: ApplicationCreate) -> ApplicationResponse:
    if not request.consent_to_share:
        raise HTTPException(400, "Consent is required to share an application")
    if not any(p.id == request.program_id for p in SYNTHETIC_PROGRAMS):
        raise HTTPException(404, "Program ID not found")
    return ApplicationResponse(
        application_id="preview-not-persisted", message="Demo only: application was NOT submitted to any organization."
    )


# Purpose: Provide a manager's authorized application review queue.
# Inputs: Eventually authenticated organization ID, reviewer role, filters and paging.
# Outputs: ApplicationListResponse; starter returns fictional applicants only.
# TODO(prod): Replace with tenant-isolated database query and permission checks.
def list_applications() -> ApplicationListResponse:
    return ApplicationListResponse(applications=SYNTHETIC_APPLICATIONS)
