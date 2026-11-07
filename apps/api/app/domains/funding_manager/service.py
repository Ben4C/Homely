"""Dev 2: replace fixture-only behaviors with authorized program management."""

from datetime import datetime, timezone
import os
from contextlib import contextmanager
from app.core.database import directory_session
from app.data.repository import search_programs
from fastapi import HTTPException
from .fixtures import SYNTHETIC_PROGRAMS, SYNTHETIC_APPLICATIONS
from .schemas import (
    ProgramListResponse,
    ProgramCheckRequest,
    ProgramCheckResponse,
    ApplicationCreate,
    ApplicationResponse,
    ApplicationListResponse,
)

VERIFICATION_MAX_AGE_DAYS = 30


def _apply_verification_freshness(program):
    """Never return a verified availability claim without a recent dated source."""
    if program.availability not in {"VERIFIED_OPEN", "VERIFIED_CLOSED", "WAITLIST"}:
        return program
    if not program.source_url or not program.last_verified_at:
        return program.model_copy(update={"availability": "UNKNOWN"})
    try:
        verified_at = datetime.fromisoformat(
            program.last_verified_at.replace("Z", "+00:00")
        )
        if verified_at.tzinfo is None:
            verified_at = verified_at.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return program.model_copy(update={"availability": "UNKNOWN"})
    age_days = (
        datetime.now(timezone.utc) - verified_at.astimezone(timezone.utc)
    ).total_seconds() / 86400
    if age_days < 0 or age_days > VERIFICATION_MAX_AGE_DAYS:
        return program.model_copy(update={"availability": "UNKNOWN"})
    return program


# Purpose: Return verified-source-aware funding program listings, optionally by county.
# Inputs: county: optional case-insensitive county name; eventually authenticated viewer context.
# Outputs: ProgramListResponse from the persistent directory, or explicit demo fixtures.
# Compatibility adapter retains the original contract; paginated discovery uses /funding-programs/search.
def list_programs(county: str | None = None, session=None) -> ProgramListResponse:
    if os.getenv("REGISTRY_MODE", "database") != "demo":
        from .schemas import FundingProgram

        if session is None:
            with contextmanager(directory_session)() as db_session:
                return list_programs(county, db_session)
        rows = search_programs(session, county=county, page_size=10000)["programs"]
        return ProgramListResponse(
            demo=False,
            programs=[
                FundingProgram(
                    id=p["id"],
                    organization_id=p["organization_id"],
                    name=p["name"],
                    county=county or "California",
                    assistance_type=p["assistance_type"],
                    max_assistance_usd=p["max_assistance_usd"],
                    source_url=p["source_url"],
                    last_verified_at=(
                        p["last_verified_at"].isoformat()
                        if p["last_verified_at"]
                        else None
                    ),
                    availability=p["availability"],
                    eligibility_summary=p["description"],
                )
                for p in rows
            ],
        )
    programs = [_apply_verification_freshness(p) for p in SYNTHETIC_PROGRAMS]
    if county:
        programs = [
            p for p in programs if p.county.casefold() == county.strip().casefold()
        ]
    return ProgramListResponse(programs=programs)


# Purpose: Determine whether an authorized manager must reverify a program's rules/status.
# Inputs: ProgramCheckRequest containing program ID.
# Outputs: ProgramCheckResponse with next human verification step; never claims live availability.
# TODO(prod): Validate official source, program owner authority, published date, terms and capacity.
def check_program(request: ProgramCheckRequest, session=None) -> ProgramCheckResponse:
    if not any(
        p.id == request.program_id for p in list_programs(session=session).programs
    ):
        raise HTTPException(404, "Program ID not found")
    return ProgramCheckResponse(
        program_id=request.program_id,
        next_action="Authorized manager must confirm current official source and funding availability.",
    )


# Purpose: Preview a housing assistance application for the program administrator.
# Inputs: ApplicationCreate with program ID, profile ID, and explicit sharing consent.
# Outputs: ApplicationResponse in DRAFT_PREVIEW status; no real submission or storage.
# TODO(prod): Authenticate, scope owner, enforce consent, persist idempotently, notify reviewers.
def create_application(request: ApplicationCreate, session=None) -> ApplicationResponse:
    if not request.consent_to_share:
        raise HTTPException(400, "Consent is required to share an application")
    if not any(
        p.id == request.program_id for p in list_programs(session=session).programs
    ):
        raise HTTPException(404, "Program ID not found")
    return ApplicationResponse(
        application_id="preview-not-persisted",
        message="Demo only: application was NOT submitted to any organization.",
    )


# Purpose: Provide a manager's authorized application review queue.
# Inputs: Eventually authenticated organization ID, reviewer role, filters and paging.
# Outputs: ApplicationListResponse; starter returns fictional applicants only.
# TODO(prod): Replace with tenant-isolated database query and permission checks.
def list_applications() -> ApplicationListResponse:
    return ApplicationListResponse(applications=SYNTHETIC_APPLICATIONS)
