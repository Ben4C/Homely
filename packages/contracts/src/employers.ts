/** Employer screening must not disclose an employee's private income documents. */
export interface EmployerProgram {
  id: string;
  employer_label: string;
  program_name: string;
  county: string;
  assistance_type: "EMPLOYEE_DOWN_PAYMENT" | "NONPROFIT_PROJECT_SPONSORSHIP";
  award_cap_usd: string;
  status: "DEMO_UNVERIFIED";
}
export interface EmployerProgramListResponse { demo: boolean; programs: EmployerProgram[] }
export interface EmployerCheckRequest {
  program_id: string; county: string; tenure_months: number; employee_consent: boolean;
}
export interface EmployerCheckResponse {
  demo: boolean; result: "REQUIRES_VERIFICATION" | "OUTSIDE_SERVICE_AREA"; required_steps: string[];
}

/** Synthetic matching policy preview; no employer offer, donation, or match is confirmed. */
export interface MatchingGiftRequest {
  employer_program_id: string; employee_donation_usd: string; verified_eligible_donation: boolean;
}
export interface MatchingGiftResponse {
  demo: boolean; employer_program_id: string; requested_donation_usd: string;
  possible_employer_match_usd: string; total_potential_support_usd: string;
  status: "PREVIEW_ONLY"; limitations: string[];
}
export interface SponsorshipPreviewRequest {
  employer_label: string; campaign_id: string; amount_usd: string; contribution_kind: "CASH" | "IN_KIND";
}
export interface SponsorshipPreviewResponse {
  demo: boolean; campaign_id: string; contribution_kind: "CASH" | "IN_KIND";
  proposed_usd: string; available_for_allocation_usd: string;
  status: "UNVERIFIED_PREVIEW"; next_steps: string[];
}
