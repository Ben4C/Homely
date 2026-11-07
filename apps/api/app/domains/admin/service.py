from .schemas import AdminReviewResponse, ReviewItem
from datetime import date


# Purpose: Flag stale, unverified or expired source metadata without changing program records.
# Inputs: Review item and explicit assessment date; outputs: human-review reasons.
# Constraints: Metadata only; never treats a source as currently open or eligible.
def integrity_flags(item: ReviewItem, today: date) -> list[str]:
    flags = []
    if item.category == 'PROGRAM_SOURCE':
        if item.source_verified_on is None:
            flags.append('Source verification date missing')
        elif item.source_verified_on > today:
            flags.append('Source verification date is in the future')
        elif (today - item.source_verified_on).days > 90:
            flags.append('Source verification older than 90 days')
        if not item.eligibility_verified:
            flags.append('Eligibility requirements unverified')
        if item.application_deadline and item.application_deadline < today:
            flags.append('Application deadline expired')
    elif item.category == 'ORGANIZATION':
        flags.append('Authorized organizational evidence required')
    return flags


# Purpose: Return synthetic organization/program verification tasks to platform admins.
# Inputs: None; production requires platform-admin authorization, pagination and audit.
# Outputs: AdminReviewResponse (fictional review items only).
# TODO(prod): Ownership proof checks, source freshness, least-privilege admin tooling.
def list_review_items() -> AdminReviewResponse:
    items = [
        ReviewItem(id="demo-review-1", category="PROGRAM_SOURCE", reason="Official funding source not verified", status="SIMULATED_PENDING"),
        ReviewItem(id="demo-review-2", category="ORGANIZATION", organization_id='demo-org-1', reason="Organization authorization evidence missing", status="SIMULATED_PENDING"),
    ]
    for item in items:
        item.review_flags = integrity_flags(item, date.today())
    return AdminReviewResponse(items=items, metrics={
        'organizations_in_queue': len({item.organization_id for item in items if item.organization_id}),
        'pending_organization_verifications': sum(item.category == 'ORGANIZATION' for item in items),
        'program_listings_requiring_review': sum(item.category == 'PROGRAM_SOURCE' and bool(item.review_flags) for item in items),
    }, warnings=['Synthetic queue only; platform-wide registration and project totals are unavailable.',
                 'Verification decisions and audit persistence require authenticated admin identity and a database.'])
