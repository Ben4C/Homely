"use client";
import { ProgramRuleExtractor } from "@/components/manager/ProgramRuleExtractor";
import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { Status } from "@/components/shared/Status";
import type { ProgramListResponse, ApplicationListResponse, ApplicationCreate, ApplicationResponse } from "@homely/contracts/funding_manager";

/**
 * Purpose: Surface a nonprofit manager's program metadata and synthetic review queue.
 * Inputs: Demo programs and applications read through the shared API client.
 * Outputs: Cards for program verification and a preview of applicant intake.
 * TODO(prod): Add RBAC, sources, program editing and authorization of actual review actions.
 */
export function ManagerDashboard() {
  const [programs, setPrograms] = useState<ProgramListResponse | null>(null);
  const [applications, setApplications] = useState<ApplicationListResponse | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  /**
   * Purpose: Load the synthetic program registry and the manager review queue on mount.
   * Inputs: No local parameters.
   * Outputs: React state containing the API payloads or error details.
   */
  useEffect(() => {
    Promise.all([apiGet<ProgramListResponse>("/programs"), apiGet<ApplicationListResponse>("/applications")])
      .then(([p,a])=>{ setPrograms(p); setApplications(a); })
      .catch(e=>setError(e instanceof Error?e.message:"Unable to load manager dashboard"))
      .finally(()=>setLoading(false));
  }, []);

  /**
   * Purpose: Preview manager-directed applicant intake for one program without submitting data.
   * Inputs: A selected program ID and fictional profile ID.
   * Outputs: Visible API acknowledgement that no real application was filed.
   */
  async function previewApplication(programId: string) {
    setError(null); setMessage("");
    try { const result = await apiPost<ApplicationCreate,ApplicationResponse>("/applications",{
      program_id: programId, homebuyer_profile_id:"demo-buyer", consent_to_share:true }); setMessage(result.message); }
    catch(e){ setError(e instanceof Error?e.message:"Preview failed"); }
  }

  return <><div className="split">
    <section className="panel"><h2>Registered program listings</h2><Status loading={loading} error={error}/>
      {programs?.programs.map(p=><div className="item" key={p.id}><h3>{p.name}</h3>
        <p className="small">{p.county} County · {p.assistance_type.replaceAll("_"," ")}</p>
        <div><span className="pill">{p.availability}</span> <span className="muted small">Last verified: {p.last_verified_at??"Never"}</span></div>
        <p className="small">{p.eligibility_summary}</p><button className="secondary" onClick={()=>previewApplication(p.id)}>Preview intake</button>
      </div>)}
    </section>
    <section className="panel"><h2>Review queue</h2>{applications?.applications.map(a=><div className="item" key={a.id}>
      <h3>{a.applicant_label}</h3><p className="small">{a.program_id}</p><span className="pill">{a.status.replaceAll("_"," ")}</span>
      {a.missing_documents.length>0&&<><h4>Incomplete documents</h4><ul>{a.missing_documents.map((doc,i)=><li key={i}>{doc}</li>)}</ul></>}
      <p className="small muted">Last updated: {a.updated_at??"Not recorded"} · Reviewer: {a.last_reviewed_by??"Not assigned"}</p>
    </div>)}{message && <p role="status" className="success">{message}</p>}
      <p className="small muted">Production work: private applicant review, rule versioning, staff access controls, finance ledger integration.</p>
    </section>
  </div>
    <ProgramRuleExtractor />
  </>;
}
