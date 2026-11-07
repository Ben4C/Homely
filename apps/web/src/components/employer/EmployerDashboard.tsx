"use client";
import { SponsorshipTools } from "@/components/employer/SponsorshipTools";
import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { Status } from "@/components/shared/Status";
import type { EmployerProgramListResponse, EmployerCheckRequest, EmployerCheckResponse } from "@homely/contracts/employers";

/**
 * Purpose: Preview employer workforce housing benefits and privacy-sensitive pre-screening.
 * Inputs: Fictional program ID, county, tenure and employee consent.
 * Outputs: Preliminary EmployerCheckResponse, never actual employment verification.
 * TODO(prod): Verified employer admins, partner organizations, no HR access to private household finances.
 */
export function EmployerDashboard() {
  const [programs,setPrograms] = useState<EmployerProgramListResponse|null>(null);
  const [programId,setProgramId] = useState("demo-employer-aid");
  const [county,setCounty] = useState("Orange");
  const [months,setMonths] = useState(24);
  const [consent,setConsent] = useState(false);
  const [result,setResult] = useState<EmployerCheckResponse|null>(null);
  const [error,setError] = useState<string|null>(null);
  const [loading,setLoading] = useState(true);

  /**
   * Purpose: Load fictional EAH programs and display their restrictions.
   * Inputs: Component mount.
   * Outputs: EmployerProgramListResponse state or error.
   */
  useEffect(()=>{ apiGet<EmployerProgramListResponse>("/employers/programs")
    .then(setPrograms).catch(e=>setError(e instanceof Error?e.message:"Employer program loading failed"))
    .finally(()=>setLoading(false)); },[]);

  /**
   * Purpose: Request a pre-screen that checks consent and service area only.
   * Inputs: Local form state programId, county, tenure and explicit consent.
   * Outputs: EmployerCheckResponse with remaining verification steps.
   */
  async function check() {
    setError(null); setResult(null);
    try { setResult(await apiPost<EmployerCheckRequest,EmployerCheckResponse>("/employers/check",{program_id:programId,county,tenure_months:months,employee_consent:consent})); }
    catch(e){ setError(e instanceof Error?e.message:"Employer check failed"); }
  }

  return <><div className="split"><section className="panel"><h2>Employer housing programs</h2><Status loading={loading} error={error}/>
    {programs?.programs.map(p=><div key={p.id} className="item"><h3>{p.program_name}</h3><p className="small">{p.employer_label} · {p.county} County</p>
      <p className="metric">${Number(p.award_cap_usd).toLocaleString()}</p><span className="pill">{p.status}</span></div>)}
  </section><section className="panel"><h2>Employee benefit pre-screen</h2><p>No employer database is queried in the demonstration.</p>
    <div className="field"><label htmlFor="employer-program">Example benefit</label><select id="employer-program" value={programId} onChange={e=>setProgramId(e.target.value)}>
      {programs?.programs.map(p=><option key={p.id} value={p.id}>{p.program_name}</option>)}
    </select></div>
    <div className="field"><label htmlFor="employer-county">Work or housing county (demo)</label><select id="employer-county" value={county} onChange={e=>setCounty(e.target.value)}>
      {["Orange","Los Angeles","San Diego"].map(c=><option key={c}>{c}</option>)}
    </select></div>
    <div className="field"><label htmlFor="employer-months">Months employed</label><input id="employer-months" type="number" min="0" value={months} onChange={e=>setMonths(Number(e.target.value))}/></div>
    <label className="checkline"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/> I consent to a future employment eligibility check</label>
    <button disabled={!consent} onClick={check}>Preview eligibility steps</button>
    {result && <div className="item"><span className="pill">{result.result}</span><ul>{result.required_steps.map(s=><li key={s}>{s}</li>)}</ul></div>}
  </section></div>
    <SponsorshipTools />
  </>;
}
