"use client";
import { useState, type FormEvent } from "react";
import { apiGet, apiPost } from "@/lib/api";
import type { DirectoryProgram } from "@homely/contracts/directory";
import { StatusBadge } from "./Directory";
interface ReviewQueue {
  actor_id: string;
  role: string;
  programs: DirectoryProgram[];
  organizations: {
    id: string;
    name: string;
    revision: number;
    status: string;
    source_url: string;
  }[];
  drafts: {
    id: string;
    resource_id: string;
    kind: string;
    status: string;
    payload: Record<string, unknown>;
  }[];
  audit: {
    id: string;
    actor_id: string;
    action: string;
    occurred_at: string;
    resource_id: string;
    previous_status: string | null;
    new_status: string | null;
    reason: string;
  }[];
}
// Purpose: Review public directory sources under configured, scoped authorization. Inputs: ephemeral reviewer credential; outputs: persistent decisions/audit, never financial approvals.
export function RegistryReview() {
  const [token, setToken] = useState("");
  const [queue, setQueue] = useState<ReviewQueue | null>(null);
  const [selected, setSelected] = useState("");
  const [kind, setKind] = useState("PROGRAM");
  const [status, setStatus] = useState("UNKNOWN");
  const [reason, setReason] = useState("");
  const [evidence, setEvidence] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [rules, setRules] = useState("");
  const [checked, setChecked] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  // Purpose: Retrieve authorized review queue. Inputs: in-memory bearer token; outputs: owned resources and recent audit events.
  async function load(e?: FormEvent) {
    e?.preventDefault();
    setBusy(true);
    setError("");
    setQueue(null);
    try {
      setQueue(await apiGet<ReviewQueue>("/directory/review-queue", token));
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }
  // Purpose: Select a reviewed resource without retaining prior resource evidence. Inputs: ID/kind; outputs: coherent empty review draft.
  function choose(id: string, type: string, url: string) {
    setSelected(id);
    setKind(type);
    setStatus(type === "PROGRAM" ? "UNKNOWN" : "DRAFT_UNVERIFIED");
    setSourceUrl(url);
    setReason("");
    setEvidence("");
    setRules("");
    setChecked(false);
    setMessage("");
  }
  // Purpose: Atomically submit source attestation with optimistic revision and optional human-validated rules.
  // Inputs: form evidence, selected resource and trusted token; outputs: persisted status/version/audit or conflict/error.
  async function save(e: FormEvent) {
    e.preventDefault();
    if (!queue || !checked) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const record =
        kind === "PROGRAM"
          ? queue.programs.find((p) => p.id === selected)
          : queue.organizations.find((o) => o.id === selected);
      if (!record) throw new Error("Reload the selected resource");
      const body = {
        expected_revision: record.revision,
        status,
        reason,
        source: {
          url: sourceUrl,
          title: `Reviewer checked source for ${selected}`,
          retrieved_at: new Date().toISOString(),
          evidence,
          verified: true,
        },
        ...(kind === "PROGRAM" && rules.trim()
          ? { rules: JSON.parse(rules) }
          : {}),
      };
      await apiPost(
        `/directory/${kind === "PROGRAM" ? "programs" : "organizations"}/${selected}/review`,
        body,
        token,
      );
      setQueue(await apiGet<ReviewQueue>("/directory/review-queue", token));
      setSelected("");
      setMessage(
        "Directory review and audit event saved. No funding or applicant decision was made.",
      );
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }
  // Purpose: Resolve an import/source lead only after explicit human attestation. Inputs: draft form and current revision; outputs: audited acceptance/rejection/acknowledgement.
  async function resolveDraft(
    e: FormEvent<HTMLFormElement>,
    draft: ReviewQueue["drafts"][number],
  ) {
    e.preventDefault();
    const form = e.currentTarget;
    const fields = new FormData(form);
    const button = (e.nativeEvent as SubmitEvent)
      .submitter as HTMLButtonElement;
    const decision = button.value;
    const record =
      draft.kind === "PROGRAM"
        ? queue?.programs.find((p) => p.id === draft.resource_id)
        : queue?.organizations.find((o) => o.id === draft.resource_id);
    setBusy(true);
    setError("");
    try {
      await apiPost(
        `/directory/import-drafts/${draft.id}/review`,
        {
          decision,
          source_checked: fields.get("source_checked") === "on",
          reason: String(fields.get("reason")),
          expected_revision: record?.revision ?? null,
        },
        token,
      );
      setQueue(await apiGet<ReviewQueue>("/directory/review-queue", token));
      setMessage("Import review saved with an audit event.");
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel ai-panel">
      <h2>Authorized directory review</h2>
      <p>
        Public sources only. Review access uses server-configured credentials;
        this field never stores a token in browser storage. Authentication is
        required before records can change.
      </p>
      <form onSubmit={load}>
        <label htmlFor="review-token">Reviewer access token</label>
        <input
          id="review-token"
          type="password"
          autoComplete="off"
          value={token}
          onChange={(e) => {
            setToken(e.target.value);
            setQueue(null);
            setSelected("");
          }}
          required
        />
        <button disabled={busy || !token}>Load authorized records</button>
      </form>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {message && <p role="status">{message}</p>}
      {queue && (
        <>
          <p>
            Signed in as {queue.actor_id} ({queue.role}).
          </p>
          <h3>Programs and source freshness</h3>
          {queue.programs.map((p) => (
            <div className="item" key={p.id}>
              <strong>{p.name}</strong> <StatusBadge status={p.availability} />
              <p>
                Revision {p.revision} · Rules {p.eligibility_rule_version} ·
                Checked {p.last_verified_at ?? "Never"}
              </p>
              <a href={p.source_url} target="_blank" rel="noopener noreferrer">
                Open source ↗
              </a>{" "}
              <button
                className="secondary"
                onClick={() => choose(p.id, "PROGRAM", p.source_url)}
              >
                Review {p.name}
              </button>
            </div>
          ))}
          {queue.role === "ADMIN" && (
            <>
              <h3>Organization verification</h3>
              {queue.organizations.map((o) => (
                <div className="item" key={o.id}>
                  <strong>{o.name}</strong> <StatusBadge status={o.status} />
                  <button
                    className="secondary"
                    onClick={() => choose(o.id, "ORGANIZATION", o.source_url)}
                  >
                    Review {o.name}
                  </button>
                </div>
              ))}
            </>
          )}
          {selected && (
            <form onSubmit={save}>
              <h3>Review {selected}</h3>
              <label htmlFor="review-status">New status</label>
              <select
                id="review-status"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                {(kind === "PROGRAM"
                  ? [
                      "UNKNOWN",
                      "VERIFIED_OPEN",
                      "VERIFIED_CLOSED",
                      "WAITLIST",
                      "STALE",
                      "DRAFT_UNVERIFIED",
                    ]
                  : ["OFFICIAL_SITE_VERIFIED", "DRAFT_UNVERIFIED", "REJECTED"]
                ).map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
              <label htmlFor="review-source-url">Official source URL</label>
              <input
                id="review-source-url"
                type="url"
                required
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
              />
              <label htmlFor="review-evidence">
                Evidence from the current source
              </label>
              <textarea
                id="review-evidence"
                required
                minLength={10}
                maxLength={2000}
                value={evidence}
                onChange={(e) => setEvidence(e.target.value)}
              />
              <label htmlFor="review-reason">Review reason</label>
              <textarea
                id="review-reason"
                required
                minLength={10}
                maxLength={1000}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
              {kind === "PROGRAM" && (
                <details>
                  <summary>
                    Publish a new structured rule version (optional)
                  </summary>
                  <p>
                    Use a JSON array of supported rules. Verify every value
                    against the original source; AI text must be normalized and
                    reviewed first. Leave blank to retain the existing version.
                  </p>
                  <textarea
                    aria-label="Reviewed structured rules"
                    value={rules}
                    onChange={(e) => setRules(e.target.value)}
                    placeholder='[{"criterion":"FIRST_TIME_BUYER","value":{"required":true},"explanation":"Source-backed requirement"}]'
                  />
                </details>
              )}
              <label className="checkline">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(e) => setChecked(e.target.checked)}
                />
                I opened the current original source and verified the facts and
                application status. This attestation records the current UTC
                review time.
              </label>
              <button disabled={!checked || busy}>
                Save source review and audit event
              </button>
            </form>
          )}
          <h3>Imports and source changes awaiting review</h3>
          {queue.drafts.length ? (
            queue.drafts.map((d) => (
              <details key={d.id}>
                <summary>
                  {d.kind}: {d.resource_id} — {d.status}
                </summary>
                <pre>{JSON.stringify(d.payload, null, 2)}</pre>
                <form onSubmit={(e) => resolveDraft(e, d)}>
                  <label>
                    Review reason
                    <textarea
                      name="reason"
                      required
                      minLength={10}
                      maxLength={1000}
                    />
                  </label>
                  <label className="checkline">
                    <input name="source_checked" type="checkbox" required />I
                    reviewed the original evidence and the proposed change.
                  </label>
                  <div className="action-buttons">
                    {["PROGRAM", "ORGANIZATION"].includes(d.kind) ? (
                      <button disabled={busy} value="ACCEPT">
                        Accept reviewed update
                      </button>
                    ) : (
                      <button disabled={busy} value="ACKNOWLEDGE">
                        Acknowledge for manual follow-up
                      </button>
                    )}
                    <button
                      className="secondary"
                      disabled={busy}
                      value="REJECT"
                    >
                      Reject this draft
                    </button>
                  </div>
                </form>
              </details>
            ))
          ) : (
            <p>No changed import drafts await review.</p>
          )}
          <h3>Recent audit history</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Actor / time</th>
                  <th>Resource / action</th>
                  <th>Status / reason</th>
                </tr>
              </thead>
              <tbody>
                {queue.audit.map((a) => (
                  <tr key={a.id}>
                    <td>
                      {a.actor_id}
                      <br />
                      {a.occurred_at}
                    </td>
                    <td>
                      {a.resource_id}
                      <br />
                      {a.action}
                    </td>
                    <td>
                      {a.previous_status ?? "New"} → {a.new_status}
                      <br />
                      {a.reason}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
