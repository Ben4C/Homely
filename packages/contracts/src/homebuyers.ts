/** Homebuyer financial values are serialized decimal strings, not JavaScript money floats. */
export interface HomebuyerProfile {
  profile_id: string;
  county: string;
  household_size: number;
  annual_income_usd: string;
  first_time_buyer: boolean | null;
  employer_name: string | null;
  preferred_language: string;
}

export interface MatchRequest { profile: HomebuyerProfile }
export interface MatchResult {
  program_id: string;
  program_name: string;
  outcome: "NEEDS_MANUAL_REVIEW" | "OUTSIDE_SERVICE_AREA";
  explanations: string[];
  verified_open: boolean;
}
export interface MatchResponse {
  demo: boolean;
  disclaimer: string;
  matches: MatchResult[];
}
