/** Homebuyer financial values are serialized decimal strings, not JavaScript money floats. */
export interface HomebuyerProfile {
  profile_id: string;
  county: string;
  purchase_county?: string | null;
  purchase_city?: string | null;
  purchase_zip?: string | null;
  residence_county?: string | null;
  residence_city?: string | null;
  purchase_price_usd?: string | null;
  household_size: number;
  annual_income_usd: string;
  first_time_buyer: boolean | null;
  employer_name: string | null;
  preferred_language: string;
}

export interface MatchRequest {
  profile: HomebuyerProfile;
}
export interface MatchResult {
  program_id: string;
  program_name: string;
  outcome:
    | "NEEDS_MANUAL_REVIEW"
    | "OUTSIDE_SERVICE_AREA"
    | "POTENTIALLY_ELIGIBLE"
    | "KNOWN_CRITERIA_NOT_MET"
    | "ADDITIONAL_INFORMATION_REQUIRED"
    | "PROGRAM_UNAVAILABLE"
    | "ELIGIBILITY_NOT_VERIFIED";
  explanations: string[];
  application_url?: string | null;
  detail_url?: string | null;
  channel?: string | null;
  max_assistance_usd?: string | null;
  verified_open: boolean;
  source_url: string | null;
  last_verified_at: string | null;
  availability: string;
}
export interface MatchResponse {
  demo: boolean;
  disclaimer: string;
  matches: MatchResult[];
}
