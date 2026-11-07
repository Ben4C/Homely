"""Dev 4: sponsor programs and privacy-preserving eligibility requests."""
from fastapi import HTTPException
from .fixtures import SYNTHETIC_EMPLOYER_PROGRAMS
from .schemas import EmployerProgramListResponse, EmployerCheckRequest, EmployerCheckResponse


# Purpose: Show fictitious employer housing benefit models for UX testing.
# Inputs: None in demo; production requires employer verification and access policy.
# Outputs: EmployerProgramListResponse with DEMO_UNVERIFIED statuses.
def list_employer_programs() -> EmployerProgramListResponse:
    return EmployerProgramListResponse(programs=SYNTHETIC_EMPLOYER_PROGRAMS)


# Purpose: Check preliminary geography and permission before HR verification begins.
# Inputs: EmployerCheckRequest (program ID, county, tenure, explicit consent).
# Outputs: EmployerCheckResponse with required steps; never confirms employment or award.
# TODO(prod): Authorized HR attestation, eligible workforce rules, grants vs loans, no HR access to private finances.
def check_employer_program(request: EmployerCheckRequest) -> EmployerCheckResponse:
    if not request.employee_consent:
        raise HTTPException(400, "Employee consent is required for employer verification")
    program = next((p for p in SYNTHETIC_EMPLOYER_PROGRAMS if p.id == request.program_id), None)
    if program is None:
        raise HTTPException(404, "Employer program not found")
    if request.county.casefold() != program.county.casefold():
        return EmployerCheckResponse(result="OUTSIDE_SERVICE_AREA", required_steps=["Confirm eligible geography with authorized administrator."])
    return EmployerCheckResponse(
        result="REQUIRES_VERIFICATION", required_steps=[
            "Validate actual employer sponsorship and program availability.",
            "Obtain minimum necessary employment proof with user consent.",
            "Check mortgage, program and award compatibility with authorized personnel.",
        ],
    )
