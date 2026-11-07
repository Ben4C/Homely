"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { Status } from "@/components/shared/Status";
import type { AdminReviewResponse } from "@homely/contracts/admin";

/**
 * Purpose: Demonstrate a platform verification backlog without accessing real applicant data.
 * Inputs: Synthetic admin review queue API response.
 * Outputs: Read-only verification task cards; no live admin actions.
 * TODO(prod): Admin-only RBAC, source checking, organization authorization and audit trail.
 */
export function AdminDashboard() {
  const [queue,setQueue] = useState<AdminReviewResponse|null>(null);
  const [error,setError] = useState<string|null>(null);
  const [loading,setLoading] = useState(true);

  /**
   * Purpose: Load fictional verification tasks for an admin role demonstration.
   * Inputs: Component mount.
   * Outputs: AdminReviewResponse state or error.
   */
  useEffect(()=>{ apiGet<AdminReviewResponse>("/admin/review-queue")
    .then(setQueue).catch(e=>setError(e instanceof Error?e.message:"Admin review queue unavailable"))
    .finally(()=>setLoading(false)); },[]);

  return <section className="panel"><h2>Program and organization verification</h2><Status loading={loading} error={error}/>
    {queue?.items.map(item=><div className="item" key={item.id}><h3>{item.category.replaceAll("_"," ")}</h3>
      <p>{item.reason}</p><span className="pill">{item.status}</span></div>)}
    <p className="small muted">Access must be restricted to platform-authorized admins before any real integrations.</p>
  </section>;
}
