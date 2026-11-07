import type { GapRequest } from "@homely/contracts/developers";

export { formatUsd } from "@/lib/money";

// Purpose: Keep the legacy aggregate valid when itemized costs are the authoritative inputs.
// Inputs: Editable pro forma; outputs: API-compatible assumptions without mutating the draft.
// Constraints: Only the backend sums costs; the unused aggregate is a zero placeholder.
export function prepareFinancials(form: GapRequest): GapRequest {
  return form.itemized_costs ? { ...form, cost_to_create_usd: "0.00" } : form;
}
