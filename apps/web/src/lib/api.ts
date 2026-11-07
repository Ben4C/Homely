/** Shared browser API transport. Dev 5 reviews modifications to this file. */
const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

/**
 * Purpose: Safely request typed JSON from a v1 GET endpoint.
 * Inputs: relative path starting with /, e.g. "/programs".
 * Outputs: Promise<T> response or a thrown Error with server feedback.
 * TODO(prod): Authentication, short-lived tokens, request IDs, retries, server response validation.
 */
export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`API ${response.status}: ${await response.text()}`);
  return (await response.json()) as T;
}

/**
 * Purpose: Send a typed JSON request to a demo API without performing payment actions.
 * Inputs: endpoint path and serializable request DTO.
 * Outputs: Promise<TResponse> or thrown server error.
 * TODO(prod): CSRF protection where needed, auth, input validation at runtime, safe logging.
 */
export async function apiPost<TRequest, TResponse>(path: string, body: TRequest): Promise<TResponse> {
  const response = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`API ${response.status}: ${await response.text()}`);
  return (await response.json()) as TResponse;
}
