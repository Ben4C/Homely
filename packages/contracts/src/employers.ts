/**
 * Employer / corporate sponsorship contracts (Dev 4). Hand-maintained mirror of
 * apps/api/app/domains/employers/{schemas,sponsorship}.py.
 *
 * Rules every consumer must respect:
 *  - Money is always a decimal USD string ("500.00"). The API serializes Decimal as a string.
 *  - Every response is a DEMO / PREVIEW. A matching gift is not paid money, and a pending
 *    sponsorship is not development revenue.
 *  - IN_KIND is never cash. Presently allocatable dollars from a preview are always "0.00".
 *  - Employer screening must not disclose an employee's private income documents.
 */

// ---------------------------------------------------------------------------
// Shared aliases and demo constants
// ---------------------------------------------------------------------------

/** Decimal USD string with at most two decimal places, e.g. "250.00". Never a float. */
export type UsdString = string;

export type EmployerAssistanceType = "EMPLOYEE_DOWN_PAYMENT" | "NONPROFIT_PROJECT_SPONSORSHIP";
export type ContributionKind = "CASH" | "IN_KIND";
export type EmployerProgramStatus = "DEMO_UNVERIFIED";

/** Fictional matching policy the API accepts. Keep in sync with sponsorship.py::preview_match. */
export const EMPLOYER_DEMO_MATCH_PROGRAM_ID = "demo-employer-match";
export const EMPLOYER_DEMO_MATCH_CAP_USD: UsdString = "500.00";
export const EMPLOYER_DEMO_MATCH_BUDGET_USD: UsdString = "20000.00";

/** Previews never make dollars allocatable. Use this to assert the invariant in UI code. */
export const EMPLOYER_ZERO_ALLOCATABLE_USD: UsdString = "0.00";

/** Program IDs served by GET /employers/programs (see fixtures.py). */
export const EMPLOYER_DEMO_PROGRAM_IDS = ["demo-employer-aid", "demo-employer-project"] as const;
export type EmployerDemoProgramId = (typeof EMPLOYER_DEMO_PROGRAM_IDS)[number];

// ---------------------------------------------------------------------------
// GET /employers/programs and POST /employers/check
// ---------------------------------------------------------------------------

/** Employer screening must not disclose an employee's private income documents. */
export interface EmployerProgram {
  id: string;
  employer_label: string;
  program_name: string;
  county: string;
  assistance_type: EmployerAssistanceType;
  award_cap_usd: UsdString;
  status: EmployerProgramStatus;
}
export interface EmployerProgramListResponse { demo: boolean; programs: EmployerProgram[] }

/** Consent-gated prescreen. 400 without employee_consent; 404 for an unknown program_id. */
export interface EmployerCheckRequest {
  program_id: string; county: string; tenure_months: number; employee_consent: boolean;
}
/** Never confirms employment, eligibility, or an award. */
export interface EmployerCheckResponse {
  demo: boolean; result: "REQUIRES_VERIFICATION" | "OUTSIDE_SERVICE_AREA"; required_steps: string[];
}

// ---------------------------------------------------------------------------
// POST /employers/matching-preview (consumed by Dev 3)
// ---------------------------------------------------------------------------

/**
 * Synthetic matching policy preview; no employer offer, donation, or match is confirmed.
 * employee_donation_usd must be > 0 and <= 1,000,000.00 with two decimals (otherwise 422).
 * employer_program_id other than EMPLOYER_DEMO_MATCH_PROGRAM_ID returns 404.
 * verified_eligible_donation is a self-attested flag; the API does not treat it as proof.
 */
export interface MatchingGiftRequest {
  employer_program_id: string; employee_donation_usd: UsdString; verified_eligible_donation: boolean;
}
export interface MatchingGiftResponse {
  demo: boolean; employer_program_id: string; requested_donation_usd: UsdString;
  possible_employer_match_usd: UsdString; total_potential_support_usd: UsdString;
  status: "PREVIEW_ONLY"; limitations: string[];
}

// ---------------------------------------------------------------------------
// POST /employers/sponsorship-preview (consumed by the employer GUI)
// ---------------------------------------------------------------------------

/**
 * amount_usd must be > 0 and <= 100,000,000.00 (otherwise 422). employer_label is 1 to 100
 * characters. An unknown campaign_id returns 404.
 */
export interface SponsorshipPreviewRequest {
  employer_label: string; campaign_id: string; amount_usd: UsdString; contribution_kind: ContributionKind;
}
export interface SponsorshipPreviewResponse {
  demo: boolean; campaign_id: string; contribution_kind: ContributionKind;
  proposed_usd: UsdString; available_for_allocation_usd: UsdString;
  status: "UNVERIFIED_PREVIEW"; next_steps: string[];
}

// ---------------------------------------------------------------------------
// Organization permissions (design only; no auth exists in the demo)
// ---------------------------------------------------------------------------

/** Sponsor roles see program and sponsorship data; only nonprofit roles see applicant review. */
export type EmployerOrgRole =
  | "SPONSOR_ADMIN" | "SPONSOR_VIEWER" | "NONPROFIT_ADMIN" | "NONPROFIT_REVIEWER";

export interface EmployerRolePermissions {
  view_sponsor_dashboard: boolean;
  preview_matching_and_sponsorship: boolean;
  /** Private applicant documents and finances. Always false for sponsor roles. */
  view_applicant_review: boolean;
  /** Requests the minimum-data employment attestation from HR/payroll. */
  request_employment_attestation: boolean;
}

export const EMPLOYER_ROLE_PERMISSIONS: Readonly<Record<EmployerOrgRole, EmployerRolePermissions>> = {
  SPONSOR_ADMIN: { view_sponsor_dashboard: true, preview_matching_and_sponsorship: true, view_applicant_review: false, request_employment_attestation: false },
  SPONSOR_VIEWER: { view_sponsor_dashboard: true, preview_matching_and_sponsorship: false, view_applicant_review: false, request_employment_attestation: false },
  NONPROFIT_ADMIN: { view_sponsor_dashboard: true, preview_matching_and_sponsorship: true, view_applicant_review: true, request_employment_attestation: true },
  NONPROFIT_REVIEWER: { view_sponsor_dashboard: true, preview_matching_and_sponsorship: false, view_applicant_review: true, request_employment_attestation: false },
};

// ---------------------------------------------------------------------------
// Future workflows (types only; NO endpoint serves these yet)
// See workflow_stubs.py. Not implemented, so do not call them from the UI.
// ---------------------------------------------------------------------------

/** Minimum-data employment attestation. Carries no wages and no finance documents. */
export interface EmploymentAttestation {
  program_id: string;
  outcome: "PASS" | "FAIL" | "UNKNOWN";
  expires_at: string | null; // ISO 8601
  provenance: string;        // who attested, via which nonprofit administrator
}

/**
 * A sponsorship moves PENDING -> APPROVED -> RECEIVED. Only APPROVED or RECEIVED values may
 * be surfaced to Dev 5 as employer_project_sponsorship_usd. IN_KIND needs a documented
 * valuation; CASH needs a receipt. In-kind is never booked as received cash.
 */
export interface PendingProjectSponsorship {
  program_id: string;
  project_id: string;
  contribution_kind: ContributionKind;
  proposed_usd: UsdString;
  state: "PENDING" | "APPROVED" | "RECEIVED" | "DECLINED";
  in_kind_valuation_doc_id: string | null;
  cash_receipt_id: string | null;
}