// Purpose: Separate real directory information from simulated financial activity. Inputs: optional message; outputs: truthful platform notice.
export function Notice({ text }: { text?: string }) {
  return (
    <div className="notice" role="note">
      <strong>Directory & planning workspace.</strong>{" "}
      {text ??
        "Program sources and review dates are shown individually. Donations, sponsorships and applications are previews only; no payments or approvals occur here."}
    </div>
  );
}
