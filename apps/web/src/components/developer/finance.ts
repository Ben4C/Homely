import type { GapRequest } from "@homely/contracts/developers";

// Purpose: Format normalized server USD strings without binary floating-point conversion.
// Inputs: Nonnegative decimal-string dollars; outputs: US currency with exact cents.
export function formatUsd(value: string): string {
  const [whole, cents = ""] = value.split(".");
  return `$${BigInt(whole).toLocaleString("en-US")}.${cents.padEnd(2, "0")}`;
}

// Purpose: Keep the legacy aggregate valid when itemized costs are the authoritative inputs.
// Inputs: Editable pro forma; outputs: API-compatible assumptions without mutating the draft.
// Constraints: Only the backend sums costs; the unused aggregate is a zero placeholder.
export function prepareFinancials(form: GapRequest): GapRequest {
  return form.itemized_costs ? { ...form, cost_to_create_usd: "0.00" } : form;
}
