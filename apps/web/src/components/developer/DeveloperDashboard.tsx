import { AIFundingAdvisor } from "@/components/developer/AIFundingAdvisor";
"use client";
import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { Status } from "@/components/shared/Status";
import type { ProjectListResponse, GapRequest, GapResponse } from "@homely/contracts/developers";

const initialFinancials: GapRequest = {
  cost_to_create_usd:"535000.00", affordable_buyer_proceeds_usd:"285000.00",
  public_development_subsidies_usd:"100000.00", earned_project_revenue_usd:"55000.00",
  nonprofit_donations_usd:"0.00", employer_project_sponsorship_usd:"0.00",
};
const labels: Record<keyof GapRequest,string> = {
  cost_to_create_usd:"Total development cost", affordable_buyer_proceeds_usd:"Affordable buyer proceeds",
  public_development_subsidies_usd:"Public development subsidies", earned_project_revenue_usd:"Earned project revenue",
  nonprofit_donations_usd:"Nonprofit donations", employer_project_sponsorship_usd:"Employer project sponsorship",
};

/**
 * Purpose: Present synthetic developer projects and a usable development-gap calculator.
 * Inputs: User-edited financial assumptions in USD and project listing API.
 * Outputs: GapResponse showing project financing deficit or surplus; no certified pro forma.
 * TODO(prod): Add dated AMI tables, affordability caps, acquisition/carry costs and real commitments.
 */
export function DeveloperDashboard() {
  const [projects,setProjects] = useState<ProjectListResponse|null>(null);
  const [form,setForm] = useState<GapRequest>(initialFinancials);
  const [result,setResult] = useState<GapResponse|null>(null);
  const [error,setError] = useState<string|null>(null);
  const [loading,setLoading] = useState(true);

  /**
   * Purpose: Load demonstration development project listings.
   * Inputs: Component mount.
   * Outputs: ProjectListResponse or an error state.
   */
  useEffect(()=>{ apiGet<ProjectListResponse>("/projects")
    .then(setProjects).catch(e=>setError(e instanceof Error?e.message:"Projects unavailable"))
    .finally(()=>setLoading(false)); },[]);

  /**
   * Purpose: Recalculate gap based on six independently classified financing inputs.
   * Inputs: Form state containing USD decimal strings.
   * Outputs: GapResponse with nonnegative gap and surplus.
   */
  async function calculate() {
    setError(null);setResult(null);
    try { setResult(await apiPost<GapRequest,GapResponse>("/projects/gap",form)); }
    catch(e){ setError(e instanceof Error?e.message:"Gap calculation failed"); }
  }

  return <><div className="split"><section className="panel"><h2>Project pro forma</h2><Status loading={loading} error={error}/>
    <p>Sample figures mirror the event's fictional one-home arithmetic. They are not local cost benchmarks.</p>
    {(Object.keys(labels) as (keyof GapRequest)[]).map(key=><div className="field" key={key}>
      <label htmlFor={key}>{labels[key]} (USD)</label>
      <input id={key} inputMode="decimal" value={form[key]} onChange={e=>setForm(prev=>({...prev,[key]:e.target.value}))}/>
    </div>)}
    <button onClick={calculate}>Calculate development gap</button>
    {result && <div className="item"><p className="small">Total sources: ${Number(result.total_funding_usd).toLocaleString()}</p>
      <div className="eyetag">Remaining gap</div><div className="metric">${Number(result.remaining_gap_usd).toLocaleString()}</div>
      <p className="small">Surplus: ${Number(result.surplus_usd).toLocaleString()}</p><p className="small">{result.explanation}</p>
    </div>}
  </section><section className="panel"><h2>Development projects</h2>
    {projects?.projects.map(p=><div key={p.id} className="item"><h3>{p.project_name}</h3>
      <p>{p.county} County · {p.units} home(s)</p><span className="pill">{p.status}</span>
    </div>)}<div className="item"><h3>Funding model constraint</h3><p className="small">Employer project sponsorships belong in the development pipeline. Employee down-payment benefits belong in buyer financing unless a verified accounting relationship permits otherwise.</p></div>
  </section></div>
    <AIFundingAdvisor financials={form} />
  </>;
}
