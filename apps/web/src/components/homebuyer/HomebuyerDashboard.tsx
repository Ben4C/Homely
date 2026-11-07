import { AIDocumentReview } from "@/components/homebuyer/AIDocumentReview";
"use client";
import { useState } from "react";
import { apiPost } from "@/lib/api";
import { Status } from "@/components/shared/Status";
import type { HomebuyerProfile, MatchRequest, MatchResponse } from "@homely/contracts/homebuyers";

/**
 * Purpose: Show a resident intake profile and preview preliminary program matches.
 * Inputs: Household/county/income fields entered locally by the visitor.
 * Outputs: MatchResponse results; no real application or eligibility decision.
 * TODO(prod): Add profile persistence, validated income limits, consent and application routing.
 */
export function HomebuyerDashboard() {
  const [county, setCounty] = useState("Orange");
  const [householdSize, setHouseholdSize] = useState(3);
  const [income, setIncome] = useState("52000.00");
  const [firstTime, setFirstTime] = useState(true);
  const [result, setResult] = useState<MatchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Purpose: Submit a fictional or user-entered sample household for conservative pre-screening.
   * Inputs: Controlled form state.
   * Outputs: UI state reflecting demo matching response or validation error.
   */
  async function runMatch() {
    setLoading(true); setError(null); setResult(null);
    const profile: HomebuyerProfile = { profile_id: "demo-browser-profile", county, household_size: householdSize,
      annual_income_usd: income, first_time_buyer: firstTime, employer_name: null, preferred_language: "en" };
    try { setResult(await apiPost<MatchRequest, MatchResponse>("/homebuyers/match", { profile })); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to load matches"); }
    finally { setLoading(false); }
  }

  return <><div className="split">
    <section className="panel"><h2>Homebuyer profile</h2><p>Use sample information only. Current program eligibility is not verified.</p>
      <div className="field"><label htmlFor="buyer-county">County</label><select id="buyer-county" value={county} onChange={e=>setCounty(e.target.value)}>
        {["Orange","Los Angeles","San Diego","Riverside","San Bernardino"].map(c=><option key={c}>{c}</option>)}
      </select></div>
      <div className="field"><label htmlFor="buyer-size">Household size</label><input id="buyer-size" type="number" min="1" max="30" value={householdSize} onChange={e=>setHouseholdSize(Number(e.target.value))}/></div>
      <div className="field"><label htmlFor="buyer-income">Annual household income (USD)</label><input id="buyer-income" inputMode="decimal" value={income} onChange={e=>setIncome(e.target.value)}/></div>
      <label className="checkline"><input type="checkbox" checked={firstTime} onChange={e=>setFirstTime(e.target.checked)}/> First-time homebuyer (self-reported)</label>
      <button onClick={runMatch} disabled={loading}>Preview assistance matches</button>
    </section>
    <section className="panel"><h2>Possible programs</h2><Status loading={loading} error={error}/>
      {!result && !loading && !error && <p>Submit a demonstration profile to see eligibility explanations.</p>}
      {result && <><p className="small muted">{result.disclaimer}</p>{result.matches.map(m => <div className="item" key={m.program_id}>
        <h3>{m.program_name}</h3><span className="pill">{m.outcome.replaceAll("_"," ")}</span><ul>{m.explanations.map(x=><li key={x}>{x}</li>)}</ul>
      </div>)}</>}
    </section>
  </div>
    <AIDocumentReview />
  </>;
}
