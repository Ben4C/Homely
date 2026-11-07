"""Focused safety and contract tests for manager program rule extraction."""
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.domains.funding_manager.ai_program import DraftRule, ProgramExtractAnalysis
from app.domains.funding_manager.schemas import FundingProgram

client = TestClient(app)


def _source(text: str = "Synthetic sample rules") -> dict[str, object]:
    return {"source_label": "Fictional sample guidance", "document_text": text,
            "consent_to_send_to_claude": True}


def test_extract_requires_consent_and_a_source() -> None:
    no_consent = _source()
    no_consent["consent_to_send_to_claude"] = False
    assert client.post("/api/v1/programs/ai-extract", json={"source": no_consent}).status_code == 422
    assert client.post("/api/v1/programs/ai-extract", json={"source": {
        "source_label": "empty", "consent_to_send_to_claude": True,
    }}).status_code == 422


def test_extract_requires_server_key(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    response = client.post("/api/v1/programs/ai-extract", json={"source": _source(
        "Income must be below $80,000. Another section says income must be below $100,000.")})
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


def test_contradictory_guidance_stays_a_human_review_draft(monkeypatch) -> None:
    async def mocked(system, content, result_type):
        return ProgramExtractAnalysis(
            proposed_program_name="Fictional assistance", proposed_assistance_type="Grant",
            proposed_eligibility_rules=[
                DraftRule(criterion="income", proposed_requirement="Income below $80,000", evidence_excerpt="Income must be below $80,000"),
                DraftRule(criterion="income", proposed_requirement="Income below $100,000", evidence_excerpt="Income must be below $100,000"),
            ], proposed_required_documents=["Income records"], proposed_deadline="Unknown",
            proposed_assistance_limit="Unknown", uncertainties=["Contradictory income limits require reviewer resolution"],
        )

    monkeypatch.setattr("app.domains.funding_manager.ai_program.claude_json", mocked)
    response = client.post("/api/v1/programs/ai-extract", json={"source": _source(
        "Income must be below $80,000. Another section says income must be below $100,000.")})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["published"] is False
    assert result["human_review_required"] is True
    assert len(result["proposed_eligibility_rules"]) == 2
    assert "application deadline is not stated" in result["uncertainties"]


def test_stale_verified_program_is_downgraded_without_recent_source(monkeypatch) -> None:
    stale = FundingProgram(
        id="stale-program", organization_id="demo-org", name="Stale sample", county="Orange",
        assistance_type="DOWN_PAYMENT", max_assistance_usd="15000", source_url="https://agency.example/program",
        last_verified_at="2020-01-01T00:00:00Z", availability="VERIFIED_OPEN", eligibility_summary="Sample",
    )
    monkeypatch.setattr("app.domains.funding_manager.service.SYNTHETIC_PROGRAMS", [stale])
    response = client.get("/api/v1/programs?county=Orange")
    assert response.status_code == 200
    program = response.json()["programs"][0]
    assert program["availability"] == "UNKNOWN"
    assert program["last_verified_at"] == "2020-01-01T00:00:00Z"
    checked = client.post("/api/v1/programs/check", json={"program_id": program["id"]})
    assert checked.status_code == 200
    assert checked.json()["result"] == "REQUIRES_SOURCE_VERIFICATION"


def test_recent_source_required_to_report_verified_open(monkeypatch) -> None:
    current = datetime.now(timezone.utc).isoformat()
    fresh = FundingProgram(
        id="fresh-program", organization_id="demo-org", name="Fresh sample", county="Orange",
        assistance_type="DOWN_PAYMENT", max_assistance_usd="15000", source_url="https://agency.example/program",
        last_verified_at=current, availability="VERIFIED_OPEN", eligibility_summary="Sample",
    )
    monkeypatch.setattr("app.domains.funding_manager.service.SYNTHETIC_PROGRAMS", [fresh])
    response = client.get("/api/v1/programs?county=Orange")
    assert response.status_code == 200
    assert response.json()["programs"][0]["availability"] == "VERIFIED_OPEN"


def test_extraction_prompt_calls_out_confidence_limits(monkeypatch) -> None:
    prompts = []

    async def mocked(system, content, result_type):
        prompts.append(system)
        return ProgramExtractAnalysis(
            proposed_program_name="Fictional assistance", proposed_assistance_type="Unknown",
            proposed_eligibility_rules=[], proposed_required_documents=[], proposed_deadline="Unknown",
            proposed_assistance_limit="Unknown", uncertainties=[
                "program year or effective date is missing", "funding availability is not stated",
                "income limit/table is absent",
            ],
        )

    monkeypatch.setattr("app.domains.funding_manager.ai_program.claude_json", mocked)
    response = client.post("/api/v1/programs/ai-extract", json={"source": _source()})
    assert response.status_code == 200, response.text
    assert all(token in prompts[0].lower() for token in ("program year", "funding availability", "income limit/table"))
    assert len(response.json()["uncertainties"]) >= 4  # includes missing deadline

