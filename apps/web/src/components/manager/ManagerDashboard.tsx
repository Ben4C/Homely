"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { DirectorySearch } from "@/components/shared/Directory";
import { RegistryReview } from "@/components/shared/RegistryReview";
import { ProgramRuleExtractor } from "./ProgramRuleExtractor";
import type { ApplicationListResponse } from "@homely/contracts/funding_manager";
// Purpose: Combine the persistent registry, scoped source review, preserved demo application queue and Claude draft extraction.
// Inputs: public directory and explicitly authorized review credentials; outputs: truthful management workflows.
export function ManagerDashboard() {
  const [applications, setApplications] =
    useState<ApplicationListResponse | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    apiGet<ApplicationListResponse>("/applications")
      .then((r) => {
        if (active) setApplications(r);
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
      <DirectorySearch intakePreview />
      <RegistryReview />
      <section className="panel ai-panel">
        <h2>Synthetic application review queue</h2>
        <p>
          These sample cases are separate from real directory records. No actual
          applications have been submitted through Homely.
        </p>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {!applications && !error && <p role="status">Loading sample queue…</p>}
        {applications?.applications.map((a) => (
          <article className="item" key={a.id}>
            <h3>{a.applicant_label}</h3>
            <p>
              {a.program_id} · {a.status}
            </p>
            <ul>
              {a.missing_documents.map((d, i) => (
                <li key={i}>{d}</li>
              ))}
            </ul>
            <p>
              Updated: {a.updated_at ?? "Not recorded"} · Reviewer:{" "}
              {a.last_reviewed_by ?? "Not assigned"}
            </p>
          </article>
        ))}
      </section>
      <ProgramRuleExtractor />
    </>
  );
}
