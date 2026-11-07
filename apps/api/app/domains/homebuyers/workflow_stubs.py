"""Developer 1 future workflows. Intentionally not wired to live endpoints."""


# Purpose: Save a user's minimum-necessary housing profile for later consent-based reuse.
# Inputs: profile_id (string) and validated buyer fields (dictionary).
# Outputs: Persisted profile record with version/updated timestamp (dictionary).
def save_homebuyer_profile(profile_id: str, fields: dict[str, object]) -> dict[str, object]:
    raise NotImplementedError("TODO(dev1): encrypted storage, owner-scoped access, explicit consent")


# Purpose: Load authoritative program-specific household income limits and their effective dates.
# Inputs: Program ID, county, household size and evaluation date.
# Outputs: Dated thresholds and official document provenance; unknown if unavailable.
def lookup_income_limits(program_id: str, county: str, household_size: int, as_of_date: str) -> dict[str, object]:
    raise NotImplementedError("TODO(dev1): distinguish State, HOME and HUD; never guess limit data")


# Purpose: Test whether proposed buyer grants and loans may legally be combined.
# Inputs: Homebuyer profile ID and list of candidate program IDs.
# Outputs: Per-pair compatibility, conflicts, missing rules and source citations.
def evaluate_buyer_funding_stack(profile_id: str, program_ids: list[str]) -> dict[str, object]:
    raise NotImplementedError("TODO(dev1): lender/mortgage requirements, lien order, benefit restrictions")


# Purpose: Assemble a minimal document checklist for an authorized program submission.
# Inputs: Verified program ID and buyer profile ID.
# Outputs: Required documents and permitted reuse permissions; no documents uploaded yet.
def prepare_application_checklist(program_id: str, profile_id: str) -> dict[str, object]:
    raise NotImplementedError("TODO(dev1): coordinate with dev2 intake and privacy workflow")
