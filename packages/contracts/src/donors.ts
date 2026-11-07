/** Donor workflows never trigger live payments in the demo. */
export interface Campaign {
  id: string;
  organization_id: string;
  project_id: string;
  title: string;
  remaining_project_gap_usd: string;
  status: "SYNTHETIC";
}
export interface CampaignListResponse { demo: boolean; campaigns: Campaign[] }
export interface PledgePreviewRequest { campaign_id: string; amount_usd: string }
export interface PledgePreviewResponse {
  demo: boolean; amount_usd: string; campaign_id: string;
  status: "NOT_SUBMITTED"; message: string;
}
export interface AllocationPreviewRequest { total_available_usd: string }
export interface AllocationLine { campaign_id: string; suggested_usd: string; reason: string }
export interface AllocationPreviewResponse {
  demo: boolean; lines: AllocationLine[]; unallocated_usd: string; message: string;
}
