/**
 * Purpose: Make it unmistakable that sample programs, funding and profiles are fictional.
 * Inputs: Optional string for additional caution.
 * Outputs: Read-only demo safety notice.
 */
export function Notice({ text }: { text?: string }) {
  return <div className="notice" role="note"><strong>DEMO MODE.</strong> {text ?? "Synthetic programs and people only. No payments, official applications or approvals."}</div>;
}
