import { DonorDashboard } from "@/components/donor/DonorDashboard";

/**
 * Purpose: Mount donor program explorer and fake gift/allocation previews.
 * Inputs: None.
 * Outputs: Demo donor dashboard.
 */
export default function DonorPage() {
  return <><div className="page-title"><div className="eyebrow">DONOR WORKSPACE</div><h1>Help close a housing gap</h1><p>Discover nonprofit projects and see what a contribution could support.</p></div><DonorDashboard/></>;
}
