/** IMPORTANT: These are mirrored from the funding manager Pydantic models. */
export type Availability = "DEMO_UNVERIFIED" | "VERIFIED_OPEN" | "VERIFIED_CLOSED" | "WAITLIST" | "UNKNOWN";
export interface FundingProgram {
  id: string;
  organization_id: string;
  name: string;
  county: string;
  assistance_type: string;
  max_assistance_usd: string;
  source_url: string | null;
  last_verified_at: string | null;
  availability: Availability;
  eligibility_summary: string;
}
export interface ProgramListResponse { demo: boolean; programs: FundingProgram[] }
export interface ProgramCheckRequest { program_id: string }
export interface ProgramCheckResponse { program_id: string; result: "REQUIRES_SOURCE_VERIFICATION"; next_action: string }
export interface ApplicationCreate { program_id: string; homebuyer_profile_id: string; consent_to_share: boolean }
export interface ApplicationResponse { application_id: string; status: "DRAFT_PREVIEW"; demo: boolean; message: string }
export interface ApplicationSummary {
  id: string; program_id: string; status: string; applicant_label: string;
  missing_documents: string[]; updated_at: string | null; last_reviewed_by: string | null;
}
export interface ApplicationListResponse { demo: boolean; applications: ApplicationSummary[] }
