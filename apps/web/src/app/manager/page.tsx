import { ManagerDashboard } from "@/components/manager/ManagerDashboard";

/**
 * Purpose: Mount nonprofit program-management dashboard.
 * Inputs: None; organization scope will be added after auth.
 * Outputs: Read-only synthetic program and application views with preview action.
 */
export default function ManagerPage() {
  return <><div className="page-title"><div className="eyebrow">NONPROFIT WORKSPACE</div><h1>Manage housing assistance</h1><p>Maintain programs, review applicants, and track verification requirements.</p></div><ManagerDashboard/></>;
}
