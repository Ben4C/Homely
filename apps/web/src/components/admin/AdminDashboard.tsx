"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { RegistryReview } from "@/components/shared/RegistryReview";
// Purpose: Show real directory oversight and authorized source/audit workflows. Inputs: database metrics; outputs: factual admin overview without fictional totals.
export function AdminDashboard() {
  const [metrics, setMetrics] = useState<Record<string, number> | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    apiGet<Record<string, number>>("/directory/overview")
      .then((r) => {
        if (active) setMetrics(r);
      })
      .catch((e) => {
        if (active) setError(String(e));
      });
    return () => {
      active = false;
    };
  }, []);
  return (
    <>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {!metrics && !error && (
        <p role="status">Loading directory integrity metrics…</p>
      )}
      <div className="card-grid">
        {Object.entries(metrics ?? {}).map(([name, count]) => (
          <section className="panel" key={name}>
            <h2>{name.replaceAll("_", " ")}</h2>
            <div className="metric">{count}</div>
            <p className="small">Persistent public-directory count</p>
          </section>
        ))}
      </div>
      <RegistryReview />
      <section className="panel ai-panel">
        <h2>Review boundaries</h2>
        <p>
          Source existence, application availability, eligibility rules and
          charitable status are distinct checks. No review here approves a
          household or authorizes a financial transaction.
        </p>
        <p>
          Identity-provider integration and private evidence storage remain
          production requirements. Local reviewer credentials are configured
          only on the server.
        </p>
      </section>
    </>
  );
}
