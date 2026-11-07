import { EmployerDashboard } from "@/components/employer/EmployerDashboard";

/**
 * Purpose: Mount employer-assisted housing program showcase and pre-screen.
 * Inputs: None.
 * Outputs: Employer dashboard.
 */
export default function EmployerPage() {
  return <><div className="page-title"><div className="eyebrow">WORKFORCE HOUSING</div><h1>Employer-assisted homeownership</h1><p>Sponsor nonprofit homes or create approved benefits for eligible employees.</p></div><EmployerDashboard/></>;
}
