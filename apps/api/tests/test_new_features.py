"""Contract and safety tests for Claude features, matching gifts, and sponsorship previews."""
import base64
from decimal import Decimal

from fastapi.testclient import TestClient
from app.main import app
from app.domains.homebuyers.ai_document import DocumentReviewAnalysis, ExtractedFact
from app.domains.funding_manager.ai_program import ProgramExtractAnalysis, DraftRule
from app.domains.developers.ai_advisor import FundingAdviceAnalysis, AdviceItem
from app.core.claude_client import SourceDocument

client = TestClient(app)


def source(text="Synthetic sample homebuyer program: Orange County residents only."):
    return {"source_label":"Synthetic guideline", "document_text":text, "consent_to_send_to_claude":True}


def gap():
    return {"cost_to_create_usd":"535000.00", "affordable_buyer_proceeds_usd":"285000.00",
            "public_development_subsidies_usd":"100000.00", "earned_project_revenue_usd":"55000.00",
            "nonprofit_donations_usd":"0.00", "employer_project_sponsorship_usd":"0.00"}


def candidate(track="DEVELOPMENT", amount="10000.00"):
    return {"id":"sample-source", "name":"Fictional employer", "funding_track":track,
            "type":"EMPLOYER", "proposed_amount_usd":amount, "availability":"UNVERIFIED",
            "program_terms":"No verified program or commitment", "source_url":None}


def test_ai_endpoints_need_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert client.post("/api/v1/homebuyers/ai-document-review",json={
        "source":source(),"document_type":"sample", "required_items":["income"]}).status_code==503
    assert client.post("/api/v1/programs/ai-extract",json={"source":source()}).status_code==503
    assert client.post("/api/v1/projects/ai-funding-advice",json={
        "financials":gap(),"sources":[candidate()],"question":"Any options?",
        "consent_to_send_to_claude":True}).status_code==503


def test_document_requires_consent_and_valid_pdf():
    body={"source":{**source(),"consent_to_send_to_claude":False},
          "document_type":"income sample","required_items":["annual income"]}
    assert client.post("/api/v1/homebuyers/ai-document-review",json=body).status_code==422
    body["source"]={"source_label":"Fake PDF", "pdf_base64":base64.b64encode(b"This is not a PDF").decode(),
                    "consent_to_send_to_claude":True}
    assert client.post("/api/v1/homebuyers/ai-document-review",json=body).status_code==422
    body["source"]={"source_label":"Valid synthetic PDF header", "pdf_base64":base64.b64encode(b"%PDF-1.7\n").decode(),
                    "consent_to_send_to_claude":True}
    assert SourceDocument.model_validate(body["source"]).pdf_base64


def test_document_review_uses_claude_mock(monkeypatch):
    async def mocked(system, content, result_type):
        assert "Untrusted source" in content[0]["text"]
        return DocumentReviewAnalysis(extracted_facts=[ExtractedFact(label="county",value="Orange",evidence_excerpt="Orange County")],
            potentially_missing_items=["income"], inconsistencies_to_check=[],next_steps=["Ask for income documentation"])
    monkeypatch.setattr("app.domains.homebuyers.ai_document.claude_json",mocked)
    res=client.post("/api/v1/homebuyers/ai-document-review",json={"source":source(),"document_type":"sample","required_items":["income"]})
    assert res.status_code==200, res.text
    assert res.json()["human_review_required"] is True
    assert res.json()["potentially_missing_items"] == ["income"]


def test_program_ai_extract_is_unpublished(monkeypatch):
    async def mocked(system, content, result_type):
        return ProgramExtractAnalysis(proposed_program_name="Fictional support",proposed_assistance_type="grant",
            proposed_eligibility_rules=[DraftRule(criterion="geography",proposed_requirement="Orange",evidence_excerpt="Orange County")],
            proposed_required_documents=["proof of residence"],proposed_deadline="Unknown",proposed_assistance_limit="Unknown",
            uncertainties=["Funding availability unknown"])
    monkeypatch.setattr("app.domains.funding_manager.ai_program.claude_json",mocked)
    r=client.post("/api/v1/programs/ai-extract",json={"source":source()})
    assert r.status_code==200,r.text
    assert r.json()["published"] is False
    assert r.json()["proposed_eligibility_rules"][0]["criterion"]=="geography"


def test_funding_advisor_never_adds_buyer_aid_to_development_gap(monkeypatch):
    async def mocked(system, content, result_type):
        return FundingAdviceAnalysis(overall_explanation="Buyer grants aren't development receipts",
            source_assessments=[AdviceItem(source_id="sample-source",opportunity_or_constraint="buyer-only",missing_verification="all"),
                                AdviceItem(source_id="hallucinated-id",opportunity_or_constraint="bad",missing_verification="bad")],
            potential_stack_conflicts=["Unknown"],next_actions=["Verify sources"])
    monkeypatch.setattr("app.domains.developers.ai_advisor.claude_json",mocked)
    res=client.post("/api/v1/projects/ai-funding-advice",json={"financials":gap(),"sources":[candidate("BUYER")],
         "question":"What fits?","consent_to_send_to_claude":True})
    assert res.status_code==200,res.text
    body=res.json()
    assert Decimal(body["deterministic_gap"]["remaining_gap_usd"])==Decimal("95000.00")
    assert len(body["source_assessments"])==1
    assert body["source_assessments"][0]["source_id"]=="sample-source"


def test_funding_advisor_rejects_no_consent_and_duplicate_ids():
    body={"financials":gap(),"sources":[candidate()],"consent_to_send_to_claude":False}
    assert client.post("/api/v1/projects/ai-funding-advice",json=body).status_code==400
    body["consent_to_send_to_claude"]=True
    body["sources"]=[candidate(),candidate()]
    assert client.post("/api/v1/projects/ai-funding-advice",json=body).status_code==422


def test_matching_gift_cap_and_no_payment():
    res=client.post("/api/v1/employers/matching-preview",json={"employer_program_id":"demo-employer-match",
            "employee_donation_usd":"750.00", "verified_eligible_donation":False})
    assert res.status_code==200,res.text
    body=res.json()
    assert Decimal(body["possible_employer_match_usd"])==Decimal("500.00")
    assert Decimal(body["total_potential_support_usd"])==Decimal("1250.00")
    assert body["status"]=="PREVIEW_ONLY"
    assert client.post("/api/v1/employers/matching-preview",json={"employer_program_id":"fake",
            "employee_donation_usd":"200.00", "verified_eligible_donation":False}).status_code==404


def test_sponsorship_cash_and_inkind_are_not_booked():
    for kind in ["CASH","IN_KIND"]:
        result=client.post("/api/v1/employers/sponsorship-preview",json={"employer_label":"Fictional",
            "campaign_id":"demo-campaign-1", "amount_usd":"12500.00", "contribution_kind":kind})
        assert result.status_code==200,result.text
        assert Decimal(result.json()["available_for_allocation_usd"])==Decimal("0.00")
        assert result.json()["status"]=="UNVERIFIED_PREVIEW"


def test_claude_sdk_adapter_invokes_parse_without_browser_key(monkeypatch):
    """Confirm server adapter passes a Pydantic type through SDK helper; no real network calls."""
    import sys
    import types
    import asyncio
    from app.core.claude_client import claude_json

    calls=[]
    class FakeMessages:
        async def parse(self, **kwargs):
            calls.append(kwargs)
            return types.SimpleNamespace(parsed_output=DocumentReviewAnalysis(
                extracted_facts=[], potentially_missing_items=["missing evidence"],
                inconsistencies_to_check=[], next_steps=["human review"] ))
    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["api_key"] == "test-placeholder-not-a-real-key"
            self.messages=FakeMessages()
    monkeypatch.setenv("ANTHROPIC_API_KEY","test-placeholder-not-a-real-key")
    monkeypatch.setitem(sys.modules,"anthropic",types.SimpleNamespace(AsyncAnthropic=FakeClient))
    result=asyncio.run(claude_json("Explain missing items",[{"type":"text","text":"Synthetic data"}],DocumentReviewAnalysis))
    assert result.potentially_missing_items == ["missing evidence"]
    assert calls[0]["output_format"] is DocumentReviewAnalysis
    assert calls[0]["model"] == "claude-sonnet-4-6"
