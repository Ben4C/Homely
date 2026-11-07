/**
 * Purpose: Display loading or API errors in a readable, accessible message.
 * Inputs: loading boolean and optional error string.
 * Outputs: Conditional status UI, or null when no status exists.
 */
export function Status({ loading, error }: { loading?: boolean; error?: string | null }) {
  if (loading) return <p role="status" className="status">Loading demonstration data…</p>;
  if (error) return <p role="alert" className="error">{error}</p>;
  return null;
}
