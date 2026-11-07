"use client";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { formatUsd, prepareFinancials } from "./finance";
import type { ProgramSearch } from "@homely/contracts/directory";
import type { GapRequest, HousingProject } from "@homely/contracts/developers";
import type {
  CandidateFundingSource,
  FundingAdviceRequest,
  FundingAdviceResponse,
} from "@homely/contracts/ai";

/**
 * Purpose: Let Claude explain *candidate* funding sources and their restrictions; math remains on server.
 * Inputs: Developer's deterministic gap fields, sample funding source descriptions, explicit consent.
 * Outputs: Advisory narrative, source-specific cautions, and authoritative current gap.
 * Registry candidates retain source dates and availability; user assumptions and AI advice require administrator verification.
 */
export function AIFundingAdvisor({
  financials,
  project,
}: {
  financials: GapRequest;
  project?: HousingProject;
}) {
  const [sources, setSources] = useState<CandidateFundingSource[]>([]);
  const [sourceError, setSourceError] = useState("");
  const [sourceLoading, setSourceLoading] = useState(true);
  // Purpose: Load actual development candidates; inputs: published registry; outputs: classified supplied sources, never fictional fallback.
  useEffect(() => {
    let active = true;
    apiGet<ProgramSearch>(
      "/funding-programs/search?funding_track=DEVELOPMENT&page_size=12",
    )
      .then((r) => {
        if (active)
          setSources(
            r.programs.map((p) => ({
              id: p.id,
              name: p.name,
              funding_track: "DEVELOPMENT",
              type:
                p.organization_type === "GOVERNMENT"
                  ? "GOVERNMENT"
                  : "NONPROFIT",
              proposed_amount_usd: "0.00",
              availability:
                p.availability === "VERIFIED_CLOSED" ? "CLOSED" : "UNVERIFIED",
              contribution_kind: "UNKNOWN",
              program_terms: [p.description, ...p.restrictions]
                .join(" ")
                .slice(0, 1500),
              source_url: p.source_url,
            })),
          );
      })
      .catch((e) => {
        if (active) setSourceError(String(e));
      })
      .finally(() => {
        if (active) setSourceLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);
  const [question, setQuestion] = useState(
    "What restrictions and verification steps apply to these supplied development funding sources?",
  );
  const [consent, setConsent] = useState(false);
  const [result, setResult] = useState<FundingAdviceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const snapshot = JSON.stringify({ financials, sources, question, project });
  const [analyzedSnapshot, setAnalyzedSnapshot] = useState<string | null>(null);
  const requestVersion = useRef(0);
  // Purpose: Invalidate pending responses when inputs change or this advisor unmounts.
  // Inputs: Serialized assumptions; outputs: current loading/error/result state only.
  useEffect(() => {
    requestVersion.current += 1;
    setResult(null);
    setError(null);
    setBusy(false);
    return () => {
      requestVersion.current += 1;
    };
  }, [snapshot]);

  /** Purpose: Request source-bounded advice. Inputs: submitted assumptions and consent; outputs: Claude analysis or sanitized API error. */
  async function advise(event: FormEvent) {
    event.preventDefault();
    if (!consent || busy || sources.length === 0) return;
    const version = ++requestVersion.current;
    setBusy(true);
    setError(null);
    setResult(null);
    setAnalyzedSnapshot(snapshot);
    try {
      const body: FundingAdviceRequest = {
        financials: prepareFinancials(financials),
        sources,
        question,
        project,
        consent_to_send_to_claude: consent,
      };
      const response = await apiPost<
        FundingAdviceRequest,
        FundingAdviceResponse
      >("/projects/ai-funding-advice", body);
      if (version === requestVersion.current) setResult(response);
    } catch (e) {
      if (version === requestVersion.current)
        setError(
          e instanceof Error ? e.message : "Claude funding advisor unavailable",
        );
    } finally {
      if (version === requestVersion.current) setBusy(false);
    }
  }
  return (
    <section className="panel ai-panel">
      <h2>Claude: Funding stack advisor</h2>
      <p className="ai-notice">
        Candidates come from the source-backed directory. Listing a program does
        not confirm an award or open intake. Enter hypothetical amounts only; AI
        advice never changes confirmed project financing.
      </p>
      {sourceLoading && <p role="status">Loading development candidates?</p>}
      {sourceError && (
        <p role="alert" className="error">
          {sourceError}
        </p>
      )}
      {!sourceLoading && !sourceError && sources.length === 0 && (
        <p>
          No published development candidates are available. No fictional
          funding sources are substituted.
        </p>
      )}
      <form onSubmit={advise}>
        <fieldset disabled={busy}>
          <legend>Candidate analysis inputs</legend>
          <div className="field">
            <label htmlFor="advisor-question">Question</label>
            <textarea
              id="advisor-question"
              maxLength={600}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
          </div>
          {sources.map((s, index) => (
            <div className="item" key={s.id}>
              <strong>{s.name}</strong>
              <p className="small">
                {s.funding_track} · {s.type} · {s.availability}
                {" · "}
                {s.contribution_kind ?? "UNKNOWN"}
              </p>
              <div className="field">
                <label htmlFor={`source-amount-${index}`}>
                  Hypothetical potential amount (USD)
                </label>
                <input
                  id={`source-amount-${index}`}
                  required
                  type="number"
                  min="0"
                  step="0.01"
                  value={s.proposed_amount_usd}
                  onChange={(e) =>
                    setSources((old) =>
                      old.map((a, i) =>
                        i === index
                          ? { ...a, proposed_amount_usd: e.target.value }
                          : a,
                      ),
                    )
                  }
                />
              </div>
              <p>{s.program_terms}</p>
              <label htmlFor={`candidate-kind-${index}`}>
                Supported contribution classification
              </label>
              <select
                id={`candidate-kind-${index}`}
                value={s.contribution_kind ?? "UNKNOWN"}
                onChange={(e) =>
                  setSources((old) =>
                    old.map((a, i) =>
                      i === index
                        ? {
                            ...a,
                            contribution_kind: e.target.value as
                              "CASH" | "IN_KIND" | "UNKNOWN",
                          }
                        : a,
                    ),
                  )
                }
              >
                <option>UNKNOWN</option>
                <option>CASH</option>
                <option>IN_KIND</option>
              </select>
              <p>
                Reference: {s.source_url ?? s.id} (supplied source; verify
                current terms)
              </p>
            </div>
          ))}
          <label className="checkline">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />{" "}
            I consent to sending these project assumptions and public program
            terms to Claude.
          </label>
          <button
            type="submit"
            disabled={!consent || busy || sources.length === 0}
          >
            {busy ? "Analyzing…" : "Analyze funding stack"}
          </button>
        </fieldset>
      </form>
      {busy && <p role="status">Claude is analyzing the supplied sources...</p>}
      {error && analyzedSnapshot === snapshot && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {result && analyzedSnapshot === snapshot && (
        <div className="item" role="status">
          <div className="eyetag">Deterministically calculated project gap</div>
          <div className="metric">
            {formatUsd(result.deterministic_gap.remaining_gap_usd)}
          </div>
          <p>{result.overall_explanation}</p>
          <h3>Source assessment</h3>
          {result.source_assessments.map((s, i) => (
            <div className="item" key={i}>
              <strong>{s.source_id}</strong>
              <p>{s.opportunity_or_constraint}</p>
              <p className="small">Verify: {s.missing_verification}</p>
            </div>
          ))}
          <h3>Potential conflicts</h3>
          <ul>
            {result.potential_stack_conflicts.map((x, i) => (
              <li key={i}>{x}</li>
            ))}
          </ul>
          <h3>Next steps</h3>
          <ul>
            {result.next_actions.map((x, i) => (
              <li key={i}>{x}</li>
            ))}
          </ul>
          <h3>Hypothetical financing scenarios</h3>
          {result.scenarios.map((s) => (
            <div className="item" key={s.source_id}>
              <strong>{s.source_id}</strong>
              <p>
                Additional cash assumption: {formatUsd(s.hypothetical_cash_usd)}
                ; remaining gap: {formatUsd(s.hypothetical_remaining_gap_usd)};
                surplus: {formatUsd(s.hypothetical_surplus_usd)}
              </p>
              <p>{s.assumption}</p>
            </div>
          ))}
          <p className="small">{result.disclaimer}</p>
        </div>
      )}
    </section>
  );
}
