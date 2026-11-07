import { HomebuyerDashboard } from "@/components/homebuyer/HomebuyerDashboard";

/**
 * Purpose: Mount the homebuyer profile + eligibility preview workflow.
 * Inputs: No route params (demo).
 * Outputs: Homebuyer landing dashboard.
 */
export default function HomebuyerPage() {
  return <><div className="page-title"><div className="eyebrow">RESIDENT WORKSPACE</div><h1>Find homeownership assistance</h1><p>Understand potential programs by location, household, and financial need.</p></div><HomebuyerDashboard/></>;
}
