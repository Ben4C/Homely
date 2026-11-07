"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import type { AdminReviewResponse } from "@homely/contracts/admin";
import styles from "./Dashboard.module.css";
// Purpose: Present synthetic integrity reviews without granting administrator privileges.
// Inputs: Published review-queue response; outputs: metrics, source flags and workflow prerequisites.
export function AdminDashboard() {
  const [queue, setQueue] = useState<AdminReviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("ALL");
  // Purpose: Retrieve synthetic queue on mount. Inputs: none; outputs: cancellable loading and error state.
  useEffect(() => {
    let active = true;
    apiGet<AdminReviewResponse>("/admin/review-queue")
      .then((x) => {
        if (active) setQueue(x);
      })
      .catch((e) => {
        if (active) setError(String(e));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);
  return (
    <div className={styles.dashboard}>
      <p className={styles.notice}>
        Synthetic platform oversight. No private applicant evidence is exposed.
      </p>
      {loading && <p role="status">Loading review queue...</p>}
      {error && <p role="alert">{error}</p>}
      <div className={styles.cards}>
        {Object.entries(queue?.metrics ?? {}).map(([name, value]) => (
          <section className="panel" key={name}>
            <h2>{name.replaceAll("_", " ")}</h2>
            <div className="metric">{value}</div>
            <p>Synthetic queue count</p>
          </section>
        ))}
      </div>
      <section className="panel">
        <h2>Organization and program review</h2>
        <label htmlFor="review-filter">Review category</label>
        <select
          id="review-filter"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="ALL">All reviews</option>
          <option value="ORGANIZATION">Organization verification</option>
          <option value="PROGRAM_SOURCE">Program integrity</option>
        </select>
        {queue?.items
          .filter((item) => filter === "ALL" || item.category === filter)
          .map((item) => (
            <article className="item" key={item.id}>
              <h3>{item.category.replaceAll("_", " ")}</h3>
              <p>{item.reason}</p>
              <span className="pill">{item.status}</span>
              <p>Resource: {item.organization_id ?? item.id}</p>
              <p>
                Source verified: {item.source_verified_on ?? "Not verified"} ·
                Deadline: {item.application_deadline ?? "Unknown"}
              </p>
              <ul>
                {item.review_flags.map((flag) => (
                  <li key={flag}>{flag}</li>
                ))}
              </ul>
              <details>
                <summary>Review requirements</summary>
                <p>
                  Inspect official source dates, eligibility rules and
                  authorized organizational evidence. Verification requires an
                  authenticated administrator and persistent audit records.
                </p>
              </details>
            </article>
          ))}
        {queue &&
          !queue.items.some(
            (item) => filter === "ALL" || item.category === filter,
          ) && <p>No reviews in this category.</p>}
      </section>
      <section className="panel">
        <h2>Verification decisions and audit records</h2>
        <p>
          Decisions are disabled until identity, organization permissions and
          database persistence are integrated. Audit events must record the
          authenticated actor, action, UTC timestamp, resource ID and
          previous/new status.
        </p>
        <button disabled>
          Record verification decision (requires authorized persistence)
        </button>
        {queue?.warnings.map((warning) => (
          <p key={warning}>{warning}</p>
        ))}
      </section>
    </div>
  );
}
