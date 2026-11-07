"""Dev 1: AI-assisted applicant document readiness (no automated determination)."""
import base64
from pydantic import BaseModel, Field, model_validator
from app.core.claude_client import SourceDocument, document_blocks, claude_json


class DocumentReviewRequest(BaseModel):
    source: SourceDocument
    document_type: str = Field(min_length=1, max_length=100)
    required_items: list[str] = Field(min_length=1, max_length=15)

    @model_validator(mode="after")
    def validate_review_inputs(self) -> "DocumentReviewRequest":
        self.document_type = self.document_type.strip()
        self.required_items = [item.strip() for item in self.required_items if item.strip()]
        if not self.document_type or not self.required_items:
            raise ValueError("Document type and at least one nonempty required item are required")
        if self.source.pdf_base64:
            payload = base64.b64decode(self.source.pdf_base64)
            if b"%%EOF" not in payload[-1024:]:
                raise ValueError("The uploaded file is not a complete PDF")
        return self


class ExtractedFact(BaseModel):
    label: str
    value: str
    evidence_excerpt: str


class DocumentReviewAnalysis(BaseModel):
    extracted_facts: list[ExtractedFact]
    potentially_missing_items: list[str]
    inconsistencies_to_check: list[str]
    next_steps: list[str]


class DocumentReviewResponse(DocumentReviewAnalysis):
    demo: bool = True
    ai_generated: bool = True
    source_label: str
    human_review_required: bool = True
    disclaimer: str = "Claude-generated draft, not proof of income, eligibility, or funding. Verify against the document and official program requirements."


# Purpose: Extract applicant document facts and flag potential missing evidence using Claude.
# Inputs: DocumentReviewRequest with explicit consent, source document, type, required items.
# Outputs: Nonbinding structured review and verification flags, never approval/denial.
# TODO(prod): Secure per-user authorization, doc retention policy, OCR checks, evidence offsets, PII minimization.
async def review_document(request: DocumentReviewRequest) -> DocumentReviewResponse:
    prompt = (
        f"Analyze this {request.document_type} for application readiness. Requirements supplied by a reviewer: "
        f"{request.required_items!r}. Extract only supported facts and very short source excerpts. "
        "For absent or unclear facts, list them as missing; do not invent details. "
        "Identify inconsistencies as questions for human verification, not accusations."
    )
    result = await claude_json(prompt, document_blocks(request.source), DocumentReviewAnalysis)
    return DocumentReviewResponse(**result.model_dump(), source_label=request.source.source_label)
