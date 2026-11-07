/** Browser transport: credentials remain ephemeral, errors never echo submitted documents. */
const baseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
// Purpose: Extract safe validation/provider messages. Inputs: failed response; outputs: useful error without raw applicant payloads.
async function failure(response: Response): Promise<never> {
  let message = "Request failed";
  try {
    const data = await response.json();
    if (typeof data.detail === "string") message = data.detail;
    else if (Array.isArray(data.detail))
      message = data.detail
        .map(
          (e: { loc?: string[]; msg?: string }) =>
            `${e.loc?.join(".") ?? "Input"}: ${e.msg ?? "Invalid value"}`,
        )
        .join("; ");
  } catch {}
  throw new Error(`API ${response.status}: ${message}`);
}
// Purpose: Fetch public or reviewer-scoped JSON. Inputs: relative path, optional in-memory credential; outputs: typed result or safe error.
export async function apiGet<T>(
  path: string,
  reviewerToken?: string,
): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    cache: "no-store",
    headers: reviewerToken ? { Authorization: `Bearer ${reviewerToken}` } : {},
  });
  if (!response.ok) return failure(response);
  return response.json() as Promise<T>;
}
// Purpose: Submit validated JSON, optionally under reviewer authority. Inputs: path/body/ephemeral token; outputs: typed result.
export async function apiPost<TRequest, TResponse>(
  path: string,
  body: TRequest,
  reviewerToken?: string,
): Promise<TResponse> {
  const response = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(reviewerToken ? { Authorization: `Bearer ${reviewerToken}` } : {}),
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) return failure(response);
  return response.json() as Promise<TResponse>;
}
