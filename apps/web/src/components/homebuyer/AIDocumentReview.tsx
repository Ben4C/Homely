"use client";

import { useState } from "react";
import { apiPost } from "@/lib/api";
import { readPdfBase64 } from "@/lib/documentUpload";
import type { DocumentReviewRequest, DocumentReviewResponse, SourceDocument } from "@homely/contracts/ai";
import styles from "./Homebuyer.module.css";

/** Purpose: Collect explicit consent and analyze a redacted sample document for readiness.
 * Inputs: One text or <=4 MiB PDF, document kind, required checklist, and per-request consent.
 * Outputs: Claude's advisory facts, evidence excerpts, gaps, uncertainties, and next steps.
 */
export function AIDocumentReview() {
  const [text, setText] = useState("");
  const [pdf, setPdf] = useState<File | null>(null);
  const [kind, setKind] = useState("Income verification document");
  const [requirements, setRequirements] = useState("Current document date\nHousehold income\nApplicant name or redacted identifier");
  const [consent, setConsent] = useState(false);
  const [result, setResult] = useState<DocumentReviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  /** Purpose: Validate the selected source locally and call the server-only Claude review route.
   * Inputs: Current component fields and consent checkbox.
   * Outputs: Structured review or a sanitized API/provider error.
   */
  async function analyze() {
    setBusy(true); setError(null); setResult(null);
    try {
      const items = requirements.split("\n").map(item => item.trim()).filter(Boolean);
      if (!items.length) throw new Error("Add at least one document requirement to review.");
      const source: SourceDocument = { source_label: pdf?.name ?? "Redacted pasted document text", consent_to_send_to_claude: consent };
      if (pdf) source.pdf_base64 = await readPdfBase64(pdf);
      else source.document_text = text;
      const body: DocumentReviewRequest = { source, document_type: kind.trim(), required_items: items };
      setResult(await apiPost<DocumentReviewRequest, DocumentReviewResponse>("/homebuyers/ai-document-review", body));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Claude analysis is unavailable.");
    } finally {
      setBusy(false);
    }
  }

  function choosePdf(file: File | undefined) {
    setError(null); setResult(null);
    if (!file) { setPdf(null); return; }
    if (file.type !== "application/pdf" || !file.name.toLowerCase().endsWith(".pdf")) {
      setPdf(null); setError("Choose a PDF file only."); return;
    }
    if (file.size > 4 * 1024 * 1024) {
      setPdf(null); setError("PDF must be 4 MiB or smaller."); return;
    }
    setPdf(file);
  }

  return <section className={`${styles.card} ${styles.aiCard}`} aria-label="AI document readiness review">
    <span className={styles.eyebrow}>OPTIONAL · AI ASSISTED</span><h2>Document readiness review</h2>
    <p>Claude can help spot facts and possible gaps. Results are not verified citations or an eligibility decision. With consent, your document is sent to the Homely backend and Claude for this review. Homely does not save it; Claude’s own data handling and retention terms may apply.</p>
    <div className={styles.warning}><strong>Protect your privacy:</strong> Use fictional or redacted material only. Remove Social Security numbers, bank account and routing numbers, full birth dates, signatures, and other sensitive details before pasting or uploading.</div>
    <div className={styles.field}><label htmlFor="hb-doc-kind">Document type</label><input id="hb-doc-kind" value={kind} maxLength={100} onChange={e => setKind(e.target.value)} /></div>
    <div className={styles.field}><label htmlFor="hb-doc-requirements">Required evidence (one item per line)</label><textarea id="hb-doc-requirements" value={requirements} onChange={e => setRequirements(e.target.value)} rows={4} /></div>
    <div className={styles.field}><label htmlFor="hb-doc-pdf">Upload redacted PDF (up to 4 MiB)</label>
      <input id="hb-doc-pdf" type="file" accept="application/pdf,.pdf" onChange={e => choosePdf(e.target.files?.[0])} />
      {pdf && <div className={styles.fileLine}><span>{pdf.name} · {(pdf.size / 1024).toFixed(0)} KiB</span><button type="button" className={styles.textButton} onClick={() => { setPdf(null); const input = document.getElementById("hb-doc-pdf") as HTMLInputElement | null; if (input) input.value = ""; }}>Remove PDF</button></div>}
    </div>
    {!pdf && <div className={styles.field}><label htmlFor="hb-doc-text">Or paste redacted document text</label><textarea id="hb-doc-text" value={text} maxLength={40000} onChange={e => setText(e.target.value)} rows={7} placeholder="Paste only fictional or carefully redacted text" /></div>}
    <label className={styles.consent}><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} /> I consent to sending this redacted sample to Claude for this review.</label>
    <button type="button" className={styles.button} disabled={busy || !consent || !kind.trim() || (!pdf && !text.trim())} onClick={analyze}>{busy ? "Reviewing document…" : "Review document"}</button>
    {error && <p className={styles.error} role="alert">{error}</p>}
    {result && <div className={styles.reviewResult} role="status">
      <div className={styles.notice}>{result.disclaimer} A person must verify every result against the original document and program rules.</div>
      <h3>Extracted facts</h3>{result.extracted_facts.length ? result.extracted_facts.map((fact, i) => <article className={styles.fact} key={`${fact.label}-${i}`}><strong>{fact.label}: {fact.value}</strong><blockquote>“{fact.evidence_excerpt}”</blockquote></article>) : <p className={styles.empty}>No supported facts were extracted.</p>}
      <div className={styles.resultColumns}><div><h3>Potentially missing</h3>{result.potentially_missing_items.length ? <ul>{result.potentially_missing_items.map((item, i) => <li key={`${item}-${i}`}>{item}</li>)}</ul> : <p>No potential gaps identified.</p>}</div>
        <div><h3>Uncertain information</h3>{result.inconsistencies_to_check.length ? <ul>{result.inconsistencies_to_check.map((item, i) => <li key={`${item}-${i}`}>{item}</li>)}</ul> : <p>No inconsistencies flagged.</p>}</div></div>
      <h3>Suggested next steps</h3><ul>{result.next_steps.map((step, i) => <li key={`${step}-${i}`}>{step}</li>)}</ul>
    </div>}
  </section>;
}
