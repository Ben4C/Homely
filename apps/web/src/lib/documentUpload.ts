/** Shared transport contract. File bytes remain in memory; never use browser-exposed API keys. */
export interface SourceDocument {
  source_label: string;
  document_text?: string | null;
  pdf_base64?: string | null;
  consent_to_send_to_claude: boolean;
}

/**
 * Purpose: Convert a user-selected small PDF to a base64 payload for the backend only.
 * Inputs: File with application/pdf type and size <=4 MiB.
 * Outputs: Promise of bare base64 PDF bytes, or a useful validation error.
 * TODO(prod): Prefer multipart uploads with content scanning and per-user access controls.
 */
export function readPdfBase64(file: File): Promise<string> {
  if (file.type !== "application/pdf" || !file.name.toLowerCase().endsWith(".pdf")) {
    return Promise.reject(new Error("Please select a PDF file."));
  }
  if (file.size > 4 * 1024 * 1024) return Promise.reject(new Error("PDF must be 4 MiB or smaller."));
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Could not read the PDF."));
    reader.onload = () => resolve(String(reader.result).split(",")[1] ?? "");
    reader.readAsDataURL(file);
  });
}
