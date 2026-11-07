/** Developer finance is distinct from homebuyer down-payment assistance. */
export interface HousingProject {
  id: string;
  project_name: string;
  county: string;
  units: number;
  status: string;
}
export interface ProjectListResponse {
  demo: boolean;
  projects: HousingProject[];
}
export interface GapRequest {
  itemized_costs?: DevelopmentCosts | null;
  funding_sources?: FinancingSource[];
  cost_to_create_usd: string;
  affordable_buyer_proceeds_usd: string;
  public_development_subsidies_usd: string;
  earned_project_revenue_usd: string;
  nonprofit_donations_usd: string;
  employer_project_sponsorship_usd: string;
}
export interface GapResponse {
  source_breakdown: Record<string, string>;
  source_percentages: Record<string, string>;
  potential_funding_usd: string;
  excluded_funding_usd: string;
  financing_identified_percent: string;
  demo: boolean;
  total_funding_usd: string;
  cost_to_create_usd: string;
  remaining_gap_usd: string;
  surplus_usd: string;
  explanation: string;
}

export interface DevelopmentCosts {
  land: string;
  construction: string;
  rehabilitation: string;
  carrying: string;
  financing: string;
  fees_design_legal: string;
}
export interface FinancingSource {
  id: string;
  category: "PUBLIC" | "NONPROFIT" | "EMPLOYER" | "OTHER";
  amount_usd: string;
  status: "CONFIRMED" | "RECEIVED" | "PLEDGED" | "UNVERIFIED";
  funding_track: "DEVELOPMENT" | "BUYER";
  contribution_kind: "CASH" | "IN_KIND";
}
