export interface DirectoryArea {
  id: string;
  name: string;
  kind: string;
  parent_id?: string | null;
  purpose?: string;
}
export interface DirectoryProgram {
  id: string;
  name: string;
  description: string;
  organization_id: string;
  organization_name: string;
  organization_type: string;
  originating_source: string | null;
  government_level: string | null;
  category: string;
  assistance_type: string;
  loan_grant: string;
  channel: string;
  funding_track: string;
  max_assistance_usd: string | null;
  min_assistance_usd: string | null;
  assistance_formula: string | null;
  application_url: string | null;
  official_url: string;
  application_opens_on: string | null;
  application_closes_on: string | null;
  availability: string;
  last_verified_at: string | null;
  source_url: string;
  source_title: string;
  source_retrieved_at: string;
  source_published_on: string | null;
  source_evidence: string;
  source_verified: boolean;
  revision: number;
  eligibility_rule_version: number;
  rules: {
    criterion: string;
    value: Record<string, unknown>;
    explanation: string;
  }[];
  rule_history?: {
    version: number;
    reviewed_at: string | null;
    effective_on: string | null;
    source_url: string;
  }[];
  restrictions: string[];
  areas: DirectoryArea[];
  outcome: string;
  explanations: string[];
}
export interface ProgramSearch {
  demo: false;
  programs: DirectoryProgram[];
  total: number;
  page: number;
  page_size: number;
  disclaimer: string;
}
export interface DirectoryOrganization {
  id: string;
  legal_name: string;
  name: string;
  kind: string;
  website: string;
  headquarters: string | null;
  services: string[];
  contact: Record<string, string>;
  charitable_status: Record<string, string>;
  verification_status: string;
  last_verified_at: string | null;
  source_url: string;
  source_title: string;
  source_evidence: string;
  source_retrieved_at: string;
  areas: { id: string; name: string }[];
  revision: number;
  homely_partner: false;
  programs?: DirectoryProgram[];
}
export interface OrganizationSearch {
  organizations: DirectoryOrganization[];
  total: number;
  page: number;
  page_size: number;
}
