import { MatchingGiftDemo } from "@/components/donor/MatchingGiftDemo";
"use client";
import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { Status } from "@/components/shared/Status";
import type { CampaignListResponse, PledgePreviewRequest, PledgePreviewResponse, AllocationPreviewRequest, AllocationPreviewResponse } from "@homely/contracts/donors";

/**
 * Purpose: Show simulated nonprofit campaigns and nonbinding donation/allocation previews.
 * Inputs: Campaign selection, amount and sample available allocation budget.
 * Outputs: Visible preview receipt and allocation recommendations; no payment execution.
 * TODO(prod): Connect authorized charity/provider flow, restricted gifts and auditable ledger.
 */
export function DonorDashboard() {
  const [campaigns,setCampaigns] = useState<CampaignListResponse|null>(null);
  const [selected,setSelected] = useState("demo-campaign-1");
  const [amount,setAmount] = useState("250.00");
  const [preview,setPreview] = useState<PledgePreviewResponse|null>(null);
  const [allocations,setAllocations] = useState<AllocationPreviewResponse|null>(null);
  const [error,setError] = useState<string|null>(null);
  const [loading,setLoading] = useState(true);

  /**
   * Purpose: Load fictional project campaigns for the donor portal.
   * Inputs: Component mount.
   * Outputs: CampaignListResponse state, or an API error message.
   */
  useEffect(()=>{ apiGet<CampaignListResponse>("/donors/campaigns")
    .then(setCampaigns).catch(e=>setError(e instanceof Error?e.message:"Campaign loading failed"))
    .finally(()=>setLoading(false)); },[]);

  /**
   * Purpose: Generate a pledge-only receipt without charging any funds.
   * Inputs: Selected campaign and an entered dollar amount.
   * Outputs: PledgePreviewResponse for display or error.
   */
  async function previewPledge() {
    setError(null); setPreview(null);
    try { setPreview(await apiPost<PledgePreviewRequest,PledgePreviewResponse>("/donors/pledge-preview",{campaign_id:selected, amount_usd:amount})); }
    catch(e){ setError(e instanceof Error?e.message:"Pledge preview failed"); }
  }

  /**
   * Purpose: Preview deterministic queue-based distribution for fictional unrestricted money.
   * Inputs: $50,000 synthetic available budget.
   * Outputs: AllocationPreviewResponse listing nonbinding recommendations.
   */
  async function previewAllocation() {
    setError(null); setAllocations(null);
    try { setAllocations(await apiPost<AllocationPreviewRequest,AllocationPreviewResponse>("/donors/allocate-preview",{total_available_usd:"50000.00"})); }
    catch(e){ setError(e instanceof Error?e.message:"Allocation preview failed"); }
  }

  return <><div className="split">
    <section className="panel"><h2>Housing projects</h2><Status loading={loading} error={error}/>
      {campaigns?.campaigns.map(c=><div className="item" key={c.id}><h3>{c.title}</h3><div className="metric">${Number(c.remaining_project_gap_usd).toLocaleString()}</div>
        <p className="small">Remaining assumed project gap · {c.status}</p></div>)}
      <h2>Preview a gift</h2><div className="field"><label htmlFor="donor-campaign">Campaign</label><select id="donor-campaign" value={selected} onChange={e=>setSelected(e.target.value)}>
        {campaigns?.campaigns.map(c=><option key={c.id} value={c.id}>{c.title}</option>)}
      </select></div><div className="field"><label htmlFor="donor-amount">Amount (USD)</label><input id="donor-amount" value={amount} onChange={e=>setAmount(e.target.value)} inputMode="decimal"/></div>
      <button onClick={previewPledge}>Preview pledge — do not pay</button>{preview && <p role="status" className="success">{preview.message}</p>}
    </section>
    <section className="panel"><h2>Funding allocation queue</h2><p>Illustrative queue recommendations using an unrestricted $50,000 budget. No financial decisions are made.</p>
      <button className="secondary" onClick={previewAllocation}>Simulate allocation</button>
      {allocations?.lines.map(l=><div className="item" key={l.campaign_id}><strong>{l.campaign_id}</strong><div className="metric">${Number(l.suggested_usd).toLocaleString()}</div><p className="small">{l.reason}</p></div>)}
      {allocations && <p className="small">Unallocated: ${Number(allocations.unallocated_usd).toLocaleString()}</p>}
    </section>
  </div>
    <MatchingGiftDemo />
  </>;
}
