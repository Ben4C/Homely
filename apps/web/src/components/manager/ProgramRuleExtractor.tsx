"use client";
import { useState } from "react";
import { apiPost } from "@/lib/api";
import { readPdfBase64 } from "@/lib/documentUpload";
import type { ProgramExtractRequest, ProgramExtractResponse, SourceDocument } from "@homely/contracts/ai";

/**
 * Purpose: Draft housing program criteria from sample guidance using Claude, with human signoff.
 * Inputs: Pasted text or PDF, source name and explicit Claude processing consent.
 * Outputs: Unpublished extraction showing rules, short evidence excerpts, unknowns.
 * TODO(prod): Source URL verification, source-effective-date checks, approved version persistence.
 */
export function ProgramRuleExtractor() {
  const [text,setText] = useState("FICTIONAL Orange County housing program: Applicants must live in Orange County, be first-time buyers and have annual household income under $90,000. Applications close December 31, 2026. Provide photo ID and income verification. Funding availability is not stated.");
  const [file,setFile] = useState<File|null>(null);
  const [label,setLabel] = useState("Fictional program guidance");
  const [consent,setConsent] = useState(false);
  const [result,setResult] = useState<ProgramExtractResponse|null>(null);
  const [error,setError] = useState<string|null>(null);
  const [busy,setBusy] = useState(false);
  const [edited,setEdited] = useState(false);

  /** Inputs: source text/PDF. Outputs: draft extraction; it does not publish any rules. */
  async function extract() {
    setBusy(true);setError(null);setResult(null);setEdited(false);
    try {
      const source: SourceDocument = {source_label:file?.name??label,consent_to_send_to_claude:consent};
      if(file) source.pdf_base64 = await readPdfBase64(file);
      else source.document_text = text;
      setResult(await apiPost<ProgramExtractRequest,ProgramExtractResponse>("/programs/ai-extract",{source}));
    } catch(e) {setError(e instanceof Error?e.message:"Unable to analyze document");}
    finally {setBusy(false);}
  }

  return <section className="panel ai-panel" aria-label="Program rule extraction"><h2>Claude: Program rule extraction</h2>
    <p className="ai-notice">Proposes rules from official guidance, but NEVER publishes or verifies a program automatically. Upload only a sample/redacted document.</p>
    <div className="field"><label htmlFor="mgr-source-label">Source label</label><input id="mgr-source-label" value={label} onChange={e=>setLabel(e.target.value)}/></div>
    <div className="field"><label htmlFor="mgr-pdf">Guideline PDF (optional, up to 4 MiB)</label><input id="mgr-pdf" type="file" accept="application/pdf,.pdf" onChange={e=>setFile(e.target.files?.[0]??null)}/></div>
    {!file&&<div className="field"><label htmlFor="mgr-text">Paste guidance</label><textarea id="mgr-text" value={text} onChange={e=>setText(e.target.value)}/></div>}
    <label className="checkline"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/> I consent to processing this document through Claude.</label>
    <button disabled={busy||!consent||(!file&&!text.trim())} onClick={extract}>{busy?"Extracting…":"Draft rules with Claude"}</button>
    {error&&<p className="error" role="alert">{error}</p>}
    {result&&<div className="item" role="status"><span className="pill">UNPUBLISHED · HUMAN REVIEW REQUIRED</span>
      <p className="small">AI-proposed source excerpts are evidence candidates, not verified citations. Review against the original guidance.</p>
      <div className="field"><label htmlFor="draft-name">Proposed program name</label><input id="draft-name" value={result.proposed_program_name} onChange={e=>{setEdited(true);setResult({...result,proposed_program_name:e.target.value});}}/></div>
      <div className="field"><label htmlFor="draft-type">Assistance type</label><input id="draft-type" value={result.proposed_assistance_type} onChange={e=>{setEdited(true);setResult({...result,proposed_assistance_type:e.target.value});}}/></div>
      <div className="field"><label htmlFor="draft-limit">Proposed assistance limit</label><input id="draft-limit" value={result.proposed_assistance_limit} onChange={e=>{setEdited(true);setResult({...result,proposed_assistance_limit:e.target.value});}}/></div>
      <div className="field"><label htmlFor="draft-deadline">Proposed deadline</label><input id="draft-deadline" value={result.proposed_deadline} onChange={e=>{setEdited(true);setResult({...result,proposed_deadline:e.target.value});}}/></div>
      <h3>Proposed rules</h3>{result.proposed_eligibility_rules.map((r,i)=><div className="item" key={i}>
        <div className="field"><label htmlFor={`draft-rule-${i}`}>{r.criterion}</label><textarea id={`draft-rule-${i}`} value={r.proposed_requirement} onChange={e=>{setEdited(true);setResult({...result,proposed_eligibility_rules:result.proposed_eligibility_rules.map((rule,j)=>j===i?{...rule,proposed_requirement:e.target.value}:rule)});}}/></div>
        <div className="code-quote">AI-proposed excerpt: {r.evidence_excerpt||"No source excerpt returned"}</div></div>)}
      <div className="field"><label htmlFor="draft-documents">Proposed required documents (one per line)</label><textarea id="draft-documents" value={result.proposed_required_documents.join("\n")} onChange={e=>{setEdited(true);setResult({...result,proposed_required_documents:e.target.value.split("\n").map(x=>x.trim()).filter(Boolean)});}}/></div>
      <h3>Confidence limits and unknowns</h3><ul>{result.uncertainties.map((x,i)=><li key={i}>{x}</li>)}</ul>
      {edited&&<p className="small" role="status">Local review edits only. Nothing has been saved or published.</p>}
      <p className="small">{result.disclaimer}</p>
    </div>}
  </section>;
}
