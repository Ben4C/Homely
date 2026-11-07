// Purpose: Format normalized server USD strings without binary floating-point conversion.
// Inputs: Nonnegative decimal-string dollars; outputs: US currency with exact cents.
export function formatUsd(value: string): string {
  const [whole, cents = ""] = value.split(".");
  return `$${BigInt(whole).toLocaleString("en-US")}.${cents.padEnd(2, "0")}`;
}
