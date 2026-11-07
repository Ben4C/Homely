from .schemas import AdminReviewResponse, ReviewItem


# Purpose: Return synthetic organization/program verification tasks to platform admins.
# Inputs: None; production requires platform-admin authorization, pagination and audit.
# Outputs: AdminReviewResponse (fictional review items only).
# TODO(prod): Ownership proof checks, source freshness, least-privilege admin tooling.
def list_review_items() -> AdminReviewResponse:
    return AdminReviewResponse(items=[
        ReviewItem(id="demo-review-1", category="PROGRAM_SOURCE", reason="Official funding source not verified", status="SIMULATED_PENDING"),
        ReviewItem(id="demo-review-2", category="ORGANIZATION", reason="Organization authorization evidence missing", status="SIMULATED_PENDING"),
    ])
