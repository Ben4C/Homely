import { HomebuyerDashboard } from "@/components/homebuyer/HomebuyerDashboard";

/**
 * Purpose: Mount the template-based homebuyer onboarding and document readiness experience.
 * Inputs: No route parameters; this demo uses local sample profile state.
 * Outputs: Functional homebuyer dashboard connected to the v1 homebuyer API.
 */
export default function HomebuyerPage() {
  return <><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;700&family=Source+Sans+3:wght@400;600&display=swap"/><HomebuyerDashboard /></>;
}
