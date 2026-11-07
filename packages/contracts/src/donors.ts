/** Donor workflows never trigger live payments in the demo. */
export interface Campaign {
  id: string;
  organization_id: string;
  project_id: string;
  title: string;
  remaining_project_gap_usd: string;
  status: "SYNTHETIC";
  organization_verified: boolean;
}
export interface CampaignListResponse { demo: boolean; campaigns: Campaign[] }
export interface PledgePreviewResponse {
  demo: boolean; amount_usd: string; campaign_id: string;
  designation: "RESTRICTED_CAMPAIGN" | "UNRESTRICTED";
  status: "NOT_SUBMITTED"; message: string;
}
export interface PledgePreviewRequest { campaign_id: string; amount_usd: string; designation?: "RESTRICTED_CAMPAIGN" | "UNRESTRICTED" }
export interface AllocationPreviewRequest { total_available_usd: string; designated_campaign_ids?: string[] }
export interface AllocationLine { campaign_id: string; suggested_usd: string; reason: string }
export interface AllocationPreviewResponse {
  demo: boolean; lines: AllocationLine[]; unallocated_usd: string; message: string;
}
