/** AI results are draft analyses only, never final program verification or eligibility decisions. */
export interface SourceDocument {
  source_label: string;
  document_text?: string | null;
  pdf_base64?: string | null;
  consent_to_send_to_claude: boolean;
}
export interface DocumentReviewRequest { source: SourceDocument; document_type: string; required_items: string[] }
export interface ExtractedFact { label: string; value: string; evidence_excerpt: string }
export interface DocumentReviewResponse {
  demo: boolean; ai_generated: boolean; source_label: string; human_review_required: boolean;
  extracted_facts: ExtractedFact[]; potentially_missing_items: string[];
  inconsistencies_to_check: string[]; next_steps: string[]; disclaimer: string;
}
export interface ProgramExtractRequest { source: SourceDocument }
export interface DraftRule { criterion: string; proposed_requirement: string; evidence_excerpt: string }
export interface ProgramExtractResponse {
  demo: boolean; ai_generated: boolean; source_label: string; human_review_required: boolean; published: boolean;
  proposed_program_name: string; proposed_assistance_type: string;
  proposed_eligibility_rules: DraftRule[]; proposed_required_documents: string[];
  proposed_deadline: string; proposed_assistance_limit: string; uncertainties: string[]; disclaimer: string;
}
export interface CandidateFundingSource {
  id: string; name: string; funding_track: "DEVELOPMENT" | "BUYER";
  type: "GOVERNMENT" | "NONPROFIT" | "EMPLOYER" | "DONOR" | "LENDER";
  proposed_amount_usd: string; availability: "UNVERIFIED" | "CONFIRMED_BY_MANAGER" | "CLOSED";
  program_terms: string; source_url?: string | null;
}
export interface FundingAdviceRequest {
  financials: import("./developers").GapRequest;
  sources: CandidateFundingSource[]; question: string; consent_to_send_to_claude: boolean;
}
export interface AdviceItem { source_id: string; opportunity_or_constraint: string; missing_verification: string }
export interface FundingAdviceResponse {
  demo: boolean; ai_generated: boolean; human_review_required: boolean;
  deterministic_gap: import("./developers").GapResponse;
  overall_explanation: string; source_assessments: AdviceItem[];
  potential_stack_conflicts: string[]; next_actions: string[]; disclaimer: string;
}
