"use client";
import { useState } from "react";
import { apiPost } from "@/lib/api";
import { readPdfBase64 } from "@/lib/documentUpload";
import type { DocumentReviewRequest, DocumentReviewResponse, SourceDocument } from "@homely/contracts/ai";

/**
 * Purpose: Let a resident examine SAMPLE application documents for completeness using Claude.
 * Inputs: Pasted sample text or PDF, consent checkbox, document type, expected checklist.
 * Outputs: AI-extracted facts and possible gaps; never legal eligibility or application submission.
 * TODO(prod): Login + document vault, secure retention/deletion, authorized reviewer handoff.
 */
export function AIDocumentReview() {
  const [text, setText] = useState("Sample employer letter: Employee is employed full-time since Jan 2025. No salary stated.");
  const [pdf, setPdf] = useState<File|null>(null);
  const [kind,setKind] = useState("Employment verification letter");
  const [requirements,setRequirements] = useState("Current employment status\nAnnual income\nLetter date");
  const [consent,setConsent] = useState(false);
  const [result,setResult] = useState<DocumentReviewResponse|null>(null);
  const [error,setError] = useState<string|null>(null);
  const [busy,setBusy] = useState(false);

  /** Inputs: local form + optional PDF. Outputs: structured review state or sanitized API error. */
  async function analyze() {
    setBusy(true); setError(null); setResult(null);
    try {
      const source: SourceDocument = {source_label:pdf?.name??"Sample applicant statement",consent_to_send_to_claude:consent};
      if(pdf) source.pdf_base64 = await readPdfBase64(pdf);
      else source.document_text = text;
      const body: DocumentReviewRequest = {source, document_type:kind,
        required_items:requirements.split("\n").map(x=>x.trim()).filter(Boolean)};
      setResult(await apiPost<DocumentReviewRequest,DocumentReviewResponse>("/homebuyers/ai-document-review",body));
    } catch(e) { setError(e instanceof Error ? e.message : "Claude analysis unavailable"); }
    finally { setBusy(false); }
  }

  return <section className="panel ai-panel" aria-label="AI document review">
    <h2>Claude: Document readiness</h2>
    <p className="ai-notice">Demo only. Use fictional or redacted information. Documents are sent to the backend and, only with your consent, to the Claude API. No data is saved in Homely's demo database.</p>
    <div className="field"><label htmlFor="buyer-doc-kind">Document type</label><input id="buyer-doc-kind" value={kind} onChange={e=>setKind(e.target.value)}/></div>
    <div className="field"><label htmlFor="buyer-doc-checklist">Required evidence (one per line)</label>
      <textarea id="buyer-doc-checklist" value={requirements} onChange={e=>setRequirements(e.target.value)}/></div>
    <div className="field"><label htmlFor="buyer-doc-pdf">PDF (optional, up to 4 MiB)</label>
      <input id="buyer-doc-pdf" type="file" accept="application/pdf,.pdf" onChange={e=>setPdf(e.target.files?.[0]??null)}/></div>
    {!pdf && <div className="field"><label htmlFor="buyer-doc-text">Sample document text</label>
      <textarea id="buyer-doc-text" value={text} onChange={e=>setText(e.target.value)}/></div>}
    <label className="checkline"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/> I consent to sending this redacted/sample document to Claude for analysis.</label>
    <button disabled={busy||!consent||(!pdf&&!text.trim())} onClick={analyze}>{busy?"Analyzing…":"Review document with Claude"}</button>
    {error && <p className="error" role="alert">{error}</p>}
    {result && <div className="item" role="status"><p className="small">{result.disclaimer}</p>
      <h3>Extracted facts</h3>{result.extracted_facts.map((f,i)=><div className="item" key={i}><strong>{f.label}: {f.value}</strong><div className="code-quote">Evidence: {f.evidence_excerpt}</div></div>)}
      <h3>Possible missing items</h3><ul>{result.potentially_missing_items.map((x,i)=><li key={i}>{x}</li>)}</ul>
      <h3>Reviewer follow-up</h3><ul>{[...result.inconsistencies_to_check,...result.next_steps].map((x,i)=><li key={i}>{x}</li>)}</ul>
    </div>}
  </section>;
}
