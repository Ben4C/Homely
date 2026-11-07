"""Dev 2: Extract draft rules from program guidance; manager must verify before use."""
from pydantic import BaseModel
from app.core.claude_client import SourceDocument, document_blocks, claude_json


class ProgramExtractRequest(BaseModel):
    source: SourceDocument


class DraftRule(BaseModel):
    criterion: str
    proposed_requirement: str
    evidence_excerpt: str


class ProgramExtractAnalysis(BaseModel):
    proposed_program_name: str
    proposed_assistance_type: str
    proposed_eligibility_rules: list[DraftRule]
    proposed_required_documents: list[str]
    proposed_deadline: str
    proposed_assistance_limit: str
    uncertainties: list[str]


class ProgramExtractResponse(ProgramExtractAnalysis):
    demo: bool = True
    ai_generated: bool = True
    source_label: str
    human_review_required: bool = True
    published: bool = False
    disclaimer: str = "Unverified extraction draft. A program administrator must confirm source version, rules, deadlines, funding availability, and publication."


# Purpose: Use Claude to propose structured eligibility rules from an official program document.
# Inputs: ProgramExtractRequest containing consented text/PDF and source label.
# Outputs: Unpublished draft rule candidates, evidence excerpts, and unknowns.
# TODO(prod): Official URL provenance, approval workflow, rule-version persistence, date validation.
async def extract_program(request: ProgramExtractRequest) -> ProgramExtractResponse:
    prompt = (
        "Read the provided housing funding program guidance. Extract draft eligibility conditions, "
        "required documents, assistance cap, and deadline if explicit. Cite short verbatim evidence "
        "excerpts in each rule; set unknown fields to 'Unknown' and list missing information. "
        "Do not infer funding availability or publish anything."
    )
    result = await claude_json(prompt, document_blocks(request.source), ProgramExtractAnalysis)
    return ProgramExtractResponse(**result.model_dump(), source_label=request.source.source_label)
