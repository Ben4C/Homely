import { AdminDashboard } from "@/components/admin/AdminDashboard";

/**
 * Purpose: Mount platform-admin verification task dashboard.
 * Inputs: None; requires auth in production.
 * Outputs: Persistent directory overview and authenticated, scoped review controls.
 */
export default function AdminPage() {
  return (
    <>
      <div className="page-title">
        <div className="eyebrow">PLATFORM TRUST & SAFETY</div>
        <h1>Verify platform integrity</h1>
        <p>
          Review official-source evidence, organization credentials, and program
          claims.
        </p>
      </div>
      <AdminDashboard />
    </>
  );
}
