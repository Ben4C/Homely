"use client";
import { useState } from "react";
import { apiPost } from "@/lib/api";
import type { GapRequest } from "@homely/contracts/developers";
import type { CandidateFundingSource, FundingAdviceRequest, FundingAdviceResponse } from "@homely/contracts/ai";

const fakeCandidates: CandidateFundingSource[] = [
  { id:"demo-public-source",name:"Fictional county development subsidy",funding_track:"DEVELOPMENT",type:"GOVERNMENT",proposed_amount_usd:"40000.00",availability:"UNVERIFIED",program_terms:"Illustrative development capital; restrictions and availability unknown." },
  { id:"demo-employer-source",name:"Fictional employer project sponsor",funding_track:"DEVELOPMENT",type:"EMPLOYER",proposed_amount_usd:"30000.00",availability:"UNVERIFIED",program_terms:"Sponsorship is not a cash commitment without signed terms and receipt." },
  { id:"demo-buyer-source",name:"Fictional employee down-payment assistance",funding_track:"BUYER",type:"EMPLOYER",proposed_amount_usd:"10000.00",availability:"UNVERIFIED",program_terms:"Buyer-only assistance; do not count as project-development revenue." },
];

/**
 * Purpose: Let Claude explain *candidate* funding sources and their restrictions; math remains on server.
 * Inputs: Developer's deterministic gap fields, sample funding source descriptions, explicit consent.
 * Outputs: Advisory narrative, source-specific cautions, and authoritative current gap.
 * TODO(prod): Replace synthetic candidates with validated registry, dated source terms, manager approval.
 */
export function AIFundingAdvisor({ financials }: {financials: GapRequest}) {
  const [sources,setSources] = useState<CandidateFundingSource[]>(fakeCandidates);
  const [question,setQuestion] = useState("Which of these hypothetical funding sources might help close the project development gap?");
  const [consent,setConsent] = useState(false);
  const [result,setResult] = useState<FundingAdviceResponse|null>(null);
  const [error,setError] = useState<string|null>(null);
  const [busy,setBusy] = useState(false);

  /** Inputs: submitted financial assumptions + candidate source list. Outputs: Claude advice and deterministic totals. */
  async function advise() {
    setBusy(true); setError(null); setResult(null);
    try { const body: FundingAdviceRequest = {financials, sources,question,consent_to_send_to_claude:consent};
      setResult(await apiPost<FundingAdviceRequest,FundingAdviceResponse>("/projects/ai-funding-advice",body));
    } catch(e) { setError(e instanceof Error?e.message:"Claude funding advisor unavailable"); }
    finally {setBusy(false);}
  }
  return <section className="panel ai-panel"><h2>Claude: Funding stack advisor</h2>
    <p className="ai-notice">These funding sources are FICTIONAL. No real grants are available in this demo; AI suggestions do not change project funding or determine stackability.</p>
    <div className="field"><label htmlFor="advisor-question">Question</label><textarea id="advisor-question" value={question} onChange={e=>setQuestion(e.target.value)}/></div>
    {sources.map((s,index)=><div className="item" key={s.id}><strong>{s.name}</strong><p className="small">{s.funding_track} · {s.type} · {s.availability}</p>
      <div className="field"><label htmlFor={`source-amount-${index}`}>Hypothetical potential amount (USD)</label>
      <input id={`source-amount-${index}`} inputMode="decimal" value={s.proposed_amount_usd} onChange={e=>setSources(old=>old.map((a,i)=>i===index?{...a,proposed_amount_usd:e.target.value}:a))}/></div>
    </div>)}
    <label className="checkline"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/> I consent to sending these synthetic assumptions to Claude.</label>
    <button disabled={!consent||busy} onClick={advise}>{busy?"Analyzing…":"Analyze funding stack"}</button>
    {error&&<p className="error" role="alert">{error}</p>}
    {result&&<div className="item" role="status"><div className="eyetag">Deterministically calculated project gap</div>
      <div className="metric">${Number(result.deterministic_gap.remaining_gap_usd).toLocaleString()}</div>
      <p>{result.overall_explanation}</p><h3>Source assessment</h3>{result.source_assessments.map((s,i)=><div className="item" key={i}>
        <strong>{s.source_id}</strong><p>{s.opportunity_or_constraint}</p><p className="small">Verify: {s.missing_verification}</p></div>)}
      <h3>Potential conflicts</h3><ul>{result.potential_stack_conflicts.map((x,i)=><li key={i}>{x}</li>)}</ul>
      <h3>Next steps</h3><ul>{result.next_actions.map((x,i)=><li key={i}>{x}</li>)}</ul>
      <p className="small">{result.disclaimer}</p></div>}
  </section>;
}
