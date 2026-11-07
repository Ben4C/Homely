"""Synthetic only — never publish these as available real funding programs."""
from decimal import Decimal
from .schemas import FundingProgram, ApplicationSummary

SYNTHETIC_PROGRAMS = [
    FundingProgram(
        id="demo-oc-downpayment", organization_id="demo-oc-nonprofit", name="DEMO Orange County Homebuyer Assistance",
        county="Orange", assistance_type="DOWN_PAYMENT", max_assistance_usd=Decimal("15000.00"),
        source_url=None, last_verified_at=None, availability="DEMO_UNVERIFIED",
        eligibility_summary="Illustrative only: household, geography and program funding verification required.",
    ),
    FundingProgram(
        id="demo-la-homebuyer", organization_id="demo-la-nonprofit", name="DEMO Los Angeles Homebuyer Support",
        county="Los Angeles", assistance_type="CLOSING_COST", max_assistance_usd=Decimal("8000.00"),
        source_url=None, last_verified_at=None, availability="DEMO_UNVERIFIED",
        eligibility_summary="Illustrative only: no current public funding offer is implied.",
    ),
]
SYNTHETIC_APPLICATIONS = [
    ApplicationSummary(id="demo-app-001", program_id="demo-oc-downpayment", status="INCOMPLETE_DOCUMENTS_DEMO",
        applicant_label="Fictional buyer A", missing_documents=["Income verification", "Photo ID"],
        updated_at="2026-11-01T16:00:00Z", last_reviewed_by=None)
]
