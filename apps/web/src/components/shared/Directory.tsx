"use client";
import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { apiGet, apiPost } from "@/lib/api";
import type {
  DirectoryProgram,
  DirectoryOrganization,
  ProgramSearch,
  OrganizationSearch,
  DirectoryArea,
} from "@homely/contracts/directory";
const counties = [
  "Orange",
  "Los Angeles",
  "San Diego",
  "Riverside",
  "San Bernardino",
];
// Purpose: Display verification without implying approval. Inputs: status; outputs: readable shared badge.
export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`badge ${status === "VERIFIED_OPEN" ? "tag-ok" : ""}`}>
      {status.replaceAll("_", " ")}
    </span>
  );
}
// Purpose: Render one sourced program and correct external channel. Inputs: API record; outputs: details, uncertainty and official links.
export function ProgramCard({
  program: p,
  intakePreview = false,
}: {
  program: DirectoryProgram;
  intakePreview?: boolean;
}) {
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  // Purpose: Preview intake without claiming submission. Inputs: selected real program ID and fictional profile; outputs: backend acknowledgement.
  async function preview() {
    setBusy(true);
    setMessage("");
    try {
      const r = await apiPost<object, { message: string }>("/applications", {
        program_id: p.id,
        homebuyer_profile_id: "synthetic-preview-profile",
        consent_to_share: true,
      });
      setMessage(r.message);
    } catch (e) {
      setMessage(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <article className="panel">
      <h3>
        <Link href={`/funding-programs/${p.id}`}>{p.name}</Link>
      </h3>
      <p>
        {p.organization_name} · {p.channel.replaceAll("_", " ")}
      </p>
      <StatusBadge status={p.availability} />
      <p className="small">
        Source checked:{" "}
        {p.last_verified_at
          ? new Date(p.last_verified_at).toLocaleDateString()
          : "Not reviewed"}
      </p>
      <p>{p.description}</p>
      <p>
        {p.max_assistance_usd
          ? `Published maximum assistance: $${p.max_assistance_usd} (conditions apply)`
          : "Assistance amount is not established by this record."}
      </p>
      {p.assistance_formula && <p>{p.assistance_formula}</p>}
      <StatusBadge status={p.outcome} />
      <ul>
        {p.explanations.map((text, i) => (
          <li key={i}>{text}</li>
        ))}
      </ul>
      <div className="action-buttons">
        <Link
          className="button-link secondary"
          href={`/funding-programs/${p.id}`}
        >
          View program details
        </Link>
        <a
          className="external"
          href={p.official_url}
          target="_blank"
          rel="noopener noreferrer"
        >
          Official source ↗
        </a>
      </div>
      {intakePreview && (
        <button disabled={busy} onClick={preview}>
          {busy ? "Preparing preview…" : "Preview intake — not a submission"}
        </button>
      )}
      {message && <p role="status">{message}</p>}
    </article>
  );
}
// Purpose: Present source-checked organizations separately from financial offers. Inputs: directory record; outputs: truthful service card.
export function OrganizationCard({
  organization: o,
}: {
  organization: DirectoryOrganization;
}) {
  return (
    <article className="panel">
      <h3>
        <Link href={`/organizations/${o.id}`}>{o.name}</Link>
      </h3>
      <StatusBadge status={o.verification_status} />
      <p>
        {o.headquarters} ·{" "}
        {o.services.map((s) => s.replaceAll("_", " ")).join(", ")}
      </p>
      <p className="small">
        Checked:{" "}
        {o.last_verified_at
          ? new Date(o.last_verified_at).toLocaleDateString()
          : "Not independently reviewed"}
      </p>
      <p>
        Service listing only. No Homely partnership, current subsidy, or
        independently verified charitable status is implied.
      </p>
      <Link href={`/organizations/${o.id}`}>Organization details</Link> ·{" "}
      <a href={o.website} target="_blank" rel="noopener noreferrer">
        Official website ↗
      </a>
    </article>
  );
}
// Purpose: Search only persisted programs/organizations with explicit filters and stable pagination.
// Inputs: role context and user filters; outputs: live API results or clear empty/loading/error states, never fictional fallback.
export function DirectorySearch({
  organizations = false,
  intakePreview = false,
}: {
  organizations?: boolean;
  intakePreview?: boolean;
}) {
  const [filters, setFilters] = useState<Record<string, string>>({
    county: "Orange",
    city: "",
    q: "",
    assistance_type: "",
    category: "",
    employer: "",
    purchase_price: "",
    organization_type: organizations ? "NONPROFIT" : "",
    status: "",
    first_time_buyer: "",
    household_income: "",
    household_size: "",
    residence_county: "",
    residence_city: "",
    zip_code: "",
    channel: "",
    sort: "name",
  });
  const [areas, setAreas] = useState<DirectoryArea[]>([]);
  const [result, setResult] = useState<
    ProgramSearch | OrganizationSearch | null
  >(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState(
    organizations
      ? "county=Orange&organization_type=NONPROFIT"
      : "county=Orange",
  );
  const [reload, setReload] = useState(0);
  const [page, setPage] = useState(1);
  // Purpose: Load authoritative supported selectors. Inputs: mount; outputs: known city identifiers, or API error handled by the actual search.
  useEffect(() => {
    let active = true;
    apiGet<{ areas: DirectoryArea[] }>("/funding-programs/locations")
      .then((r) => {
        if (active) setAreas(r.areas);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);
  // Purpose: Fetch the selected page, ignoring obsolete search completions. Inputs: submitted query/page; outputs: current data state.
  useEffect(() => {
    let active = true;
    setBusy(true);
    setError("");
    setResult(null);
    const params = new URLSearchParams(query);
    params.set("page", String(page));
    params.set("page_size", "6");
    if (organizations && params.has("organization_type")) {
      params.set("kind", params.get("organization_type")!);
      params.delete("organization_type");
    }
    apiGet<ProgramSearch | OrganizationSearch>(
      `${organizations ? "/organizations/search" : "/funding-programs/search"}?${params}`,
    )
      .then((r) => {
        if (active) setResult(r);
      })
      .catch((e) => {
        if (active) setError(String(e));
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => {
      active = false;
    };
  }, [query, page, organizations, reload]);
  // Purpose: Apply filter changes only on submission. Inputs: validated form; outputs: new search and page reset.
  function submit(e: FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => {
      if (v) params.set(k, v);
    });
    setQuery(params.toString());
    setPage(1);
    setReload((n) => n + 1);
  }
  // Purpose: Update one filter and clear incompatible city selection on county change. Inputs: key/value; outputs: coherent draft filters.
  function update(key: string, value: string) {
    setFilters((old) => ({
      ...old,
      [key]: value,
      ...(key === "county" ? { city: "" } : {}),
    }));
  }
  return (
    <section
      aria-label={
        organizations ? "Organization directory" : "Program discovery"
      }
    >
      <h2>
        {organizations
          ? "Housing organization directory"
          : "Find source-backed programs"}
      </h2>
      <p>
        {organizations
          ? "Official service information, separate from the synthetic campaigns below."
          : "Choose the intended property location. Geographic compatibility is only one part of eligibility."}
      </p>
      <form onSubmit={submit}>
        <div className="filters">
          <div>
            <label htmlFor={`${organizations ? "org" : "program"}-state`}>
              State
            </label>
            <select
              id={`${organizations ? "org" : "program"}-state`}
              value="CA"
              disabled
            >
              <option value="CA">California</option>
            </select>
          </div>
          <div>
            <label htmlFor={`${organizations ? "org" : "program"}-search`}>
              Search name
            </label>
            <input
              id={`${organizations ? "org" : "program"}-search`}
              value={filters.q}
              maxLength={120}
              onChange={(e) => update("q", e.target.value)}
            />
          </div>
          <div>
            <label htmlFor={`${organizations ? "org" : "program"}-county`}>
              {organizations ? "Service county" : "Purchase county"}
            </label>
            <select
              id={`${organizations ? "org" : "program"}-county`}
              value={filters.county}
              onChange={(e) => update("county", e.target.value)}
            >
              <option value="">All supported counties</option>
              {counties.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor={`${organizations ? "org" : "program"}-city`}>
              {organizations ? "Service city" : "Purchase city"}
            </label>
            <select
              id={`${organizations ? "org" : "program"}-city`}
              value={filters.city}
              onChange={(e) => update("city", e.target.value)}
            >
              <option value="">Any / not specified</option>
              {areas
                .filter(
                  (a) =>
                    a.kind === "CITY" &&
                    (!filters.county ||
                      a.parent_id ===
                        `ca-${filters.county.toLowerCase().replaceAll(" ", "-")}`),
                )
                .map((a) => (
                  <option key={a.id}>{a.name}</option>
                ))}
            </select>
          </div>
          {!organizations && (
            <>
              <div>
                <label htmlFor="program-category">Assistance type</label>
                <select
                  id="program-category"
                  value={filters.assistance_type}
                  onChange={(e) => update("assistance_type", e.target.value)}
                >
                  <option value="">All</option>
                  {[
                    "DOWN_PAYMENT",
                    "HOMEOWNERSHIP",
                    "DEVELOPMENT",
                    "COUNSELING",
                    "REHABILITATION",
                    "FIRST_MORTGAGE",
                  ].map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="program-kind">Program category</label>
                <select
                  id="program-kind"
                  value={filters.category}
                  onChange={(e) => update("category", e.target.value)}
                >
                  <option value="">All</option>
                  <option value="HOMEOWNERSHIP">Homeownership</option>
                  <option value="REHABILITATION">Housing rehabilitation</option>
                  <option value="DEVELOPMENT">Housing development</option>
                </select>
              </div>
              <div>
                <label htmlFor="program-employer">
                  Employer (when a published rule applies)
                </label>
                <input
                  id="program-employer"
                  maxLength={120}
                  value={filters.employer}
                  onChange={(e) => update("employer", e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="program-purchase-price">
                  Intended purchase price (USD)
                </label>
                <input
                  id="program-purchase-price"
                  type="number"
                  min="0"
                  step="0.01"
                  value={filters.purchase_price}
                  onChange={(e) => update("purchase_price", e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="program-admin-type">Administrator type</label>
                <select
                  id="program-admin-type"
                  value={filters.organization_type}
                  onChange={(e) => update("organization_type", e.target.value)}
                >
                  <option value="">All</option>
                  <option>GOVERNMENT</option>
                  <option>NONPROFIT</option>
                </select>
              </div>
              <div>
                <label htmlFor="program-status">
                  Application / verification status
                </label>
                <select
                  id="program-status"
                  value={filters.status}
                  onChange={(e) => update("status", e.target.value)}
                >
                  <option value="">All published statuses</option>
                  {[
                    "VERIFIED_OPEN",
                    "VERIFIED_CLOSED",
                    "WAITLIST",
                    "UNKNOWN",
                    "STALE",
                  ].map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="program-first-time">
                  First-time buyer status
                </label>
                <select
                  id="program-first-time"
                  value={filters.first_time_buyer}
                  onChange={(e) => update("first_time_buyer", e.target.value)}
                >
                  <option value="">Unknown</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>
              <div>
                <label htmlFor="program-income">
                  Annual household income (USD)
                </label>
                <input
                  id="program-income"
                  type="number"
                  min="0"
                  step="0.01"
                  value={filters.household_income}
                  onChange={(e) => update("household_income", e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="program-size">Household size</label>
                <input
                  id="program-size"
                  type="number"
                  min="1"
                  max="30"
                  step="1"
                  value={filters.household_size}
                  onChange={(e) => update("household_size", e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="program-residence">
                  Current residence county
                </label>
                <select
                  id="program-residence"
                  value={filters.residence_county}
                  onChange={(e) => update("residence_county", e.target.value)}
                >
                  <option value="">Not specified</option>
                  {counties.map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="program-zip">
                  Purchase ZIP (verified mappings only)
                </label>
                <input
                  id="program-zip"
                  pattern="[0-9]{5}"
                  maxLength={5}
                  value={filters.zip_code}
                  onChange={(e) => update("zip_code", e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="program-residence-city">
                  Current residence city
                </label>
                <input
                  id="program-residence-city"
                  maxLength={120}
                  value={filters.residence_city}
                  onChange={(e) => update("residence_city", e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="program-channel">Application channel</label>
                <select
                  id="program-channel"
                  value={filters.channel}
                  onChange={(e) => update("channel", e.target.value)}
                >
                  <option value="">All</option>
                  {[
                    "DIRECT_HOMEBUYER",
                    "PARTICIPATING_LENDER",
                    "PARTICIPATING_NONPROFIT",
                    "LOCAL_ADMINISTERING_AGENCY",
                    "DEVELOPMENT_FINANCING",
                    "EXTERNAL_REFERRAL",
                  ].map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="program-sort">Sort</label>
                <select
                  id="program-sort"
                  value={filters.sort}
                  onChange={(e) => update("sort", e.target.value)}
                >
                  <option value="name">Name</option>
                  <option value="reviewed">Last reviewed</option>
                </select>
              </div>
            </>
          )}
        </div>
        <p className="small">
          ZIP filtering is supported only when an authoritative mapping has been
          imported. Use county/city when a ZIP cannot be resolved.
        </p>
        <button disabled={busy} type="submit">
          {busy ? "Searching…" : "Search directory"}
        </button>
      </form>
      {busy && <p role="status">Loading the persistent directory…</p>}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {result && !busy && (
        <>
          <p role="status">{result.total} directory results</p>
          <div className="result-grid">
            {"programs" in result
              ? result.programs.map((p) => (
                  <ProgramCard
                    key={p.id}
                    program={p}
                    intakePreview={intakePreview}
                  />
                ))
              : result.organizations.map((o) => (
                  <OrganizationCard key={o.id} organization={o} />
                ))}
          </div>
          {result.total === 0 && (
            <p className="empty">
              No matching records. Try a broader location or another status. No
              fictional programs are substituted.
            </p>
          )}
          <div className="pagination">
            <button
              className="secondary"
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous page
            </button>
            <span>
              Page {page} of {Math.max(1, Math.ceil(result.total / 6))}
            </span>
            <button
              className="secondary"
              disabled={page * 6 >= result.total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next page
            </button>
          </div>
        </>
      )}
    </section>
  );
}
