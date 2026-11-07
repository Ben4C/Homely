"use client";
import { useState } from "react";
import { apiPost } from "@/lib/api";
import type { MatchingGiftRequest, MatchingGiftResponse, SponsorshipPreviewRequest, SponsorshipPreviewResponse } from "@homely/contracts/employers";

/**
 * Purpose: Demonstrate a corporate matching-gift policy and a nonprofit project sponsorship.
 * Inputs: Fictional matching program, cash/in-kind type, a sample project, dollar amounts.
 * Outputs: Deterministic preview responses; no pledge, escrow, fund reservation, or payment.
 * TODO(prod): Role-based employer authorization, sponsorship contracts, donor-verification and actual budget ledger.
 */
export function SponsorshipTools() {
  const [gift,setGift] = useState("200.00");
  const [giftPreview,setGiftPreview] = useState<MatchingGiftResponse|null>(null);
  const [sponsorAmount,setSponsorAmount] = useState("10000.00");
  const [kind,setKind] = useState<"CASH"|"IN_KIND">("CASH");
  const [sponsorPreview,setSponsorPreview] = useState<SponsorshipPreviewResponse|null>(null);
  const [error,setError] = useState<string|null>(null);

  /** Inputs: sample gift. Outputs: hypothetical match cap computation, no verification. */
  async function previewGift() {
    setError(null);setGiftPreview(null);
    try {setGiftPreview(await apiPost<MatchingGiftRequest,MatchingGiftResponse>("/employers/matching-preview",{
      employer_program_id:"demo-employer-match",employee_donation_usd:gift,verified_eligible_donation:false}));}
    catch(e){setError(e instanceof Error?e.message:"Matching preview failed");}
  }

  /** Inputs: sample sponsor pledge and classification. Outputs: unverified sponsor preview. */
  async function previewSponsor() {
    setError(null);setSponsorPreview(null);
    try {setSponsorPreview(await apiPost<SponsorshipPreviewRequest,SponsorshipPreviewResponse>("/employers/sponsorship-preview",{
      employer_label:"FICTIONAL employer",campaign_id:"demo-campaign-1",amount_usd:sponsorAmount,contribution_kind:kind}));}
    catch(e){setError(e instanceof Error?e.message:"Sponsorship preview failed");}
  }

  return <section className="panel ai-panel"><h2>Corporate sponsorship and matching</h2>
    <p className="ai-notice">Only fictional employers and projects. No matching offer is verified and no funds move.</p>
    <h3>Employee gift matching (illustrative 1:1, $500 cap)</h3>
    <div className="field"><label htmlFor="employer-gift">Employee donation (USD)</label><input id="employer-gift" inputMode="decimal" value={gift} onChange={e=>setGift(e.target.value)}/></div>
    <button className="secondary" onClick={previewGift}>Preview matching gift</button>
    {giftPreview&&<div className="item" role="status"><div className="metric">${Number(giftPreview.possible_employer_match_usd).toLocaleString()}</div>
      <p>Potential employer match — not a verified award.</p><ul>{giftPreview.limitations.map((x,i)=><li key={i}>{x}</li>)}</ul></div>}
    <div className="ai-panel"><h3>Sponsor a fictional housing project</h3>
      <div className="field"><label htmlFor="sponsor-amount">Proposed contribution (USD)</label><input id="sponsor-amount" inputMode="decimal" value={sponsorAmount} onChange={e=>setSponsorAmount(e.target.value)}/></div>
      <div className="field"><label htmlFor="sponsor-kind">Contribution type</label><select id="sponsor-kind" value={kind} onChange={e=>setKind(e.target.value as "CASH"|"IN_KIND")}><option value="CASH">Cash</option><option value="IN_KIND">In-kind materials/services</option></select></div>
      <button className="secondary" onClick={previewSponsor}>Preview sponsorship</button>
      {sponsorPreview&&<div className="item" role="status"><span className="pill">{sponsorPreview.status}</span>
        <p>Proposed ${Number(sponsorPreview.proposed_usd).toLocaleString()} {sponsorPreview.contribution_kind.toLowerCase()} sponsorship.</p>
        <p>Currently allocatable amount: ${Number(sponsorPreview.available_for_allocation_usd).toLocaleString()}.</p>
        <ul>{sponsorPreview.next_steps.map((x,i)=><li key={i}>{x}</li>)}</ul>
      </div>}
    </div>
    {error&&<p role="alert" className="error">{error}</p>}
  </section>;
}
