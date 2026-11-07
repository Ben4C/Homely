"use client";
import { useState } from "react";
import { apiPost } from "@/lib/api";
import type { MatchingGiftRequest,MatchingGiftResponse } from "@homely/contracts/employers";

/**
 * Purpose: Show donors how a fictional employer matching policy could multiply a donation.
 * Inputs: Sample donation amount; no employee identity, payroll, or actual donation data.
 * Outputs: Read-only match estimate from employer-owned API, with all limitations exposed.
 * TODO(prod): Confirm donor gift eligibility with employer + charity before showing claim instructions.
 */
export function MatchingGiftDemo() {
  const [amount,setAmount] = useState("100.00");
  const [preview,setPreview] = useState<MatchingGiftResponse|null>(null);
  const [error,setError] = useState<string|null>(null);

  /** Inputs: donation amount. Outputs: fictional matching policy result, never a charged gift. */
  async function calculate() {
    setError(null);setPreview(null);
    try {setPreview(await apiPost<MatchingGiftRequest,MatchingGiftResponse>("/employers/matching-preview",{
      employer_program_id:"demo-employer-match",employee_donation_usd:amount,verified_eligible_donation:false}));}
    catch(e){setError(e instanceof Error?e.message:"Match preview unavailable");}
  }
  return <section className="panel ai-panel"><h2>Could your employer match your gift?</h2>
    <p className="small">Illustration using a fictional employer's 1:1 match with a $500 maximum. Not a live matching program.</p>
    <div className="field"><label htmlFor="donor-match-amount">Potential donation (USD)</label><input id="donor-match-amount" inputMode="decimal" value={amount} onChange={e=>setAmount(e.target.value)}/></div>
    <button className="secondary" onClick={calculate}>Preview matching impact</button>
    {preview&&<div className="item" role="status"><div className="metric">${Number(preview.total_potential_support_usd).toLocaleString()}</div>
      <p>Hypothetical combined support if both the contribution and match are approved and paid.</p>
      <ul>{preview.limitations.map((x,i)=><li key={i}>{x}</li>)}</ul></div>}
    {error&&<p className="error" role="alert">{error}</p>}
  </section>;
}
