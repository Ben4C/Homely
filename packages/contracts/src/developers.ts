/** Developer finance is distinct from homebuyer down-payment assistance. */
export interface HousingProject { id: string; project_name: string; county: string; units: number; status: string }
export interface ProjectListResponse { demo: boolean; projects: HousingProject[] }
export interface GapRequest {
  cost_to_create_usd: string;
  affordable_buyer_proceeds_usd: string;
  public_development_subsidies_usd: string;
  earned_project_revenue_usd: string;
  nonprofit_donations_usd: string;
  employer_project_sponsorship_usd: string;
}
export interface GapResponse {
  demo: boolean;
  total_funding_usd: string;
  cost_to_create_usd: string;
  remaining_gap_usd: string;
  surplus_usd: string;
  explanation: string;
}
