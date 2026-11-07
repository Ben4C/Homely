"use client";
import { useEffect, useState, type FormEvent } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { AIFundingAdvisor } from "./AIFundingAdvisor";
import { formatUsd as money, prepareFinancials } from "./finance";
import type {
  ProjectListResponse,
  GapRequest,
  GapResponse,
  DevelopmentCosts,
  FinancingSource,
} from "@homely/contracts/developers";
import styles from "./Dashboard.module.css";
const initial: GapRequest = {
  cost_to_create_usd: "535000.00",
  affordable_buyer_proceeds_usd: "285000.00",
  public_development_subsidies_usd: "100000.00",
  earned_project_revenue_usd: "55000.00",
  nonprofit_donations_usd: "0.00",
  employer_project_sponsorship_usd: "0.00",
};
const labels = {
  cost_to_create_usd: "Total development cost",
  affordable_buyer_proceeds_usd: "Affordable buyer sale proceeds",
  public_development_subsidies_usd: "Confirmed public subsidies",
  earned_project_revenue_usd: "Eligible earned project revenue",
  nonprofit_donations_usd: "Confirmed nonprofit contributions",
  employer_project_sponsorship_usd: "Confirmed employer project sponsorship",
};
const costLabels: Record<keyof DevelopmentCosts, string> = {
  land: "Land acquisition",
  construction: "Construction",
  rehabilitation: "Rehabilitation",
  carrying: "Carrying costs",
  financing: "Financing expenses",
  fees_design_legal: "Fees, design and legal",
};
// Purpose: Edit a synthetic project pro forma. Inputs: user assumptions and API data; outputs: deterministic financing results and optional Claude advice.
export function DeveloperDashboard() {
  const [projects, setProjects] = useState<ProjectListResponse | null>(null);
  const [models, setModels] = useState<Record<string, GapRequest>>({});
  const [itemizedDrafts, setItemizedDrafts] = useState<
    Record<string, DevelopmentCosts>
  >({});
  const [result, setResult] = useState<GapResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [projectError, setProjectError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState("demo-project-1");
  const form = models[selected] ?? initial;
  // Purpose: Load published project listings. Inputs: mount; outputs: synthetic records or a separate listing error.
  useEffect(() => {
    let active = true;
    apiGet<ProjectListResponse>("/projects")
      .then((x) => {
        if (active) {
          setProjects(x);
          if (x.projects.length && !x.projects.some((p) => p.id === selected))
            setSelected(x.projects[0].id);
        }
      })
      .catch((e) => {
        if (active) setProjectError(String(e));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);
  // Purpose: Invalidate outdated analysis after an edit. Inputs: next assumptions; outputs: current form with cleared totals.
  function update(next: GapRequest) {
    setModels((previous) => ({ ...previous, [selected]: next }));
    setResult(null);
    setError(null);
  }
  // Purpose: Switch cost-entry modes without discarding a project's itemized draft.
  // Inputs: Desired mode; outputs: preserved session draft and invalidated calculation.
  function toggleItemized(enabled: boolean) {
    if (enabled) {
      update({
        ...form,
        itemized_costs: itemizedDrafts[selected] ?? {
          land: "0.00",
          construction: form.cost_to_create_usd || "0.00",
          rehabilitation: "0.00",
          carrying: "0.00",
          financing: "0.00",
          fees_design_legal: "0.00",
        },
      });
    } else {
      if (form.itemized_costs)
        setItemizedDrafts((previous) => ({
          ...previous,
          [selected]: form.itemized_costs!,
        }));
      update({ ...form, itemized_costs: null });
    }
  }
  // Purpose: Submit validated decimal strings. Inputs: native form event; outputs: server-calculated results or error.
  async function calculate(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setResult(
        await apiPost<GapRequest, GapResponse>(
          "/projects/gap",
          prepareFinancials(form),
        ),
      );
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  // Purpose: Edit a separately classified source. Inputs: index and patch; outputs: updated source list without changing legacy financing.
  function editSource(index: number, patch: Partial<FinancingSource>) {
    update({
      ...form,
      funding_sources: form.funding_sources?.map((s, i) =>
        i === index ? { ...s, ...patch } : s,
      ),
    });
  }
  return (
    <div className={styles.dashboard}>
      <p className={styles.notice}>
        Synthetic planning workspace. Enter each financing source once.
        Confirmed amounts are user assumptions, not independently verified
        receipts.
      </p>
      <section className="panel">
        <h2>Project overview</h2>
        {loading && <p role="status">Loading projects...</p>}
        {projectError && <p role="alert">{projectError}</p>}
        <div className={styles.cards}>
          {projects?.projects.map((p) => (
            <article className="item" key={p.id}>
              <h3>{p.project_name}</h3>
              <p>
                {p.county} County · {p.units} home(s)
              </p>
              <span className="pill">{p.status}</span>
              <p>
                Budget and financing:{" "}
                {selected === p.id && result
                  ? `${money(result.cost_to_create_usd)} cost; ${money(result.total_funding_usd)} identified; ${money(result.remaining_gap_usd)} gap`
                  : "not saved for this project"}
              </p>
              <button
                type="button"
                aria-pressed={selected === p.id}
                disabled={busy}
                onClick={() => {
                  setSelected(p.id);
                  setResult(null);
                  setError(null);
                }}
              >
                Model this project
              </button>
            </article>
          ))}
        </div>
        {!loading && !projectError && projects?.projects.length === 0 && (
          <p>No projects available.</p>
        )}
        <p>
          Model changes are session-only and are not saved to the project
          registry.
        </p>
      </section>
      <div className={styles.columns}>
        <form className="panel" onSubmit={calculate}>
          <h2>Development pro forma</h2>
          <fieldset disabled={busy}>
            <legend>Project costs and entered financing (USD)</legend>
            <label className="checkline">
              <input
                type="checkbox"
                checked={!!form.itemized_costs}
                onChange={(e) => toggleItemized(e.target.checked)}
              />
              Use itemized costs instead of the total cost
            </label>
            {form.itemized_costs &&
              (Object.keys(costLabels) as (keyof DevelopmentCosts)[]).map(
                (key) => (
                  <div className="field" key={key}>
                    <label htmlFor={`cost-${key}`}>{costLabels[key]}</label>
                    <input
                      id={`cost-${key}`}
                      required
                      type="number"
                      min="0"
                      step="0.01"
                      value={form.itemized_costs![key]}
                      onChange={(e) =>
                        update({
                          ...form,
                          itemized_costs: {
                            ...form.itemized_costs!,
                            [key]: e.target.value,
                          },
                        })
                      }
                    />
                  </div>
                ),
              )}
            {(Object.keys(labels) as (keyof typeof labels)[])
              .filter(
                (key) => !form.itemized_costs || key !== "cost_to_create_usd",
              )
              .map((key) => (
                <div className="field" key={key}>
                  <label htmlFor={key}>{labels[key]}</label>
                  <input
                    id={key}
                    required
                    type="number"
                    min="0"
                    step="0.01"
                    value={form[key]}
                    onChange={(e) => update({ ...form, [key]: e.target.value })}
                  />
                </div>
              ))}
            <h3>Additional financing sources</h3>
            <p>
              Use these records for contributions not entered above. Pledges and
              unverified opportunities remain potential.
            </p>
            {form.funding_sources?.map((s, i) => (
              <fieldset key={s.id}>
                <legend>Source {i + 1}</legend>
                <label htmlFor={`amount-${i}`}>Amount (USD)</label>
                <input
                  id={`amount-${i}`}
                  required
                  type="number"
                  step="0.01"
                  min="0"
                  value={s.amount_usd}
                  onChange={(e) =>
                    editSource(i, { amount_usd: e.target.value })
                  }
                />
                <label htmlFor={`category-${i}`}>Category</label>
                <select
                  id={`category-${i}`}
                  value={s.category}
                  onChange={(e) =>
                    editSource(i, {
                      category: e.target.value as FinancingSource["category"],
                    })
                  }
                >
                  {["PUBLIC", "NONPROFIT", "EMPLOYER", "OTHER"].map((x) => (
                    <option key={x}>{x}</option>
                  ))}
                </select>
                <label htmlFor={`status-${i}`}>Status</label>
                <select
                  id={`status-${i}`}
                  value={s.status}
                  onChange={(e) =>
                    editSource(i, {
                      status: e.target.value as FinancingSource["status"],
                    })
                  }
                >
                  {["UNVERIFIED", "PLEDGED", "CONFIRMED", "RECEIVED"].map(
                    (x) => (
                      <option key={x}>{x}</option>
                    ),
                  )}
                </select>
                <label htmlFor={`track-${i}`}>Funding track</label>
                <select
                  id={`track-${i}`}
                  value={s.funding_track}
                  onChange={(e) =>
                    editSource(i, {
                      funding_track: e.target
                        .value as FinancingSource["funding_track"],
                    })
                  }
                >
                  <option>DEVELOPMENT</option>
                  <option>BUYER</option>
                </select>
                <label htmlFor={`kind-${i}`}>Contribution kind</label>
                <select
                  id={`kind-${i}`}
                  value={s.contribution_kind}
                  onChange={(e) =>
                    editSource(i, {
                      contribution_kind: e.target
                        .value as FinancingSource["contribution_kind"],
                    })
                  }
                >
                  <option>CASH</option>
                  <option>IN_KIND</option>
                </select>
                <button
                  type="button"
                  onClick={() =>
                    update({
                      ...form,
                      funding_sources: form.funding_sources?.filter(
                        (_, j) => i !== j,
                      ),
                    })
                  }
                >
                  Remove source
                </button>
              </fieldset>
            ))}
            <button
              type="button"
              onClick={() =>
                update({
                  ...form,
                  funding_sources: [
                    ...(form.funding_sources ?? []),
                    {
                      id: crypto.randomUUID(),
                      category: "OTHER",
                      amount_usd: "0.00",
                      status: "UNVERIFIED",
                      funding_track: "DEVELOPMENT",
                      contribution_kind: "CASH",
                    },
                  ],
                })
              }
            >
              Add source
            </button>{" "}
            <button type="submit">
              {busy ? "Calculating..." : "Calculate development gap"}
            </button>
          </fieldset>
          {error && <p role="alert">{error}</p>}
        </form>
        <section className="panel" aria-live="polite">
          <h2>Financing composition</h2>
          {!result ? (
            <p>
              Calculate the pro forma to see financing, potential support, and
              the remaining gap.
            </p>
          ) : (
            <>
              <p>Total development cost: {money(result.cost_to_create_usd)}</p>
              <p>Identified financing: {money(result.total_funding_usd)}</p>
              <div className="metric">{money(result.remaining_gap_usd)}</div>
              <p>Remaining funding gap</p>
              <progress
                aria-label="Project financing identified"
                max="100"
                value={Math.min(
                  100,
                  Number(result.financing_identified_percent),
                )}
              />
              <p>{result.financing_identified_percent}% financing identified</p>
              <p>Surplus: {money(result.surplus_usd)}</p>
              <p>
                Potential, excluded from confirmed total:{" "}
                {money(result.potential_funding_usd)}
              </p>
              <p>
                Buyer / in-kind support excluded:{" "}
                {money(result.excluded_funding_usd)}
              </p>
              <div className={styles.table}>
                <table>
                  <caption>Identified financing sources</caption>
                  <thead>
                    <tr>
                      <th scope="col">Source</th>
                      <th scope="col">USD</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(result.source_breakdown).map(
                      ([name, value]) => (
                        <tr key={name}>
                          <th scope="row">{name.replaceAll("_", " ")}</th>
                          <td>
                            {money(value)}
                            <progress
                              aria-label={`${name} share of project cost`}
                              max="100"
                              value={Math.min(
                                100,
                                Number(result.source_percentages[name]),
                              )}
                            />
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
              <p>{result.explanation}</p>
            </>
          )}
        </section>
      </div>
      <AIFundingAdvisor
        financials={form}
        project={projects?.projects.find((p) => p.id === selected)}
      />
    </div>
  );
}
