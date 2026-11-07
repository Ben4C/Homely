"""Homebuyer match and advisory document review safety tests."""
import base64
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def profile(county="Orange"):
    return {"profile_id": "fictional-buyer", "county": county, "household_size": 4,
            "annual_income_usd": "999999.00", "first_time_buyer": False,
            "employer_name": None, "preferred_language": "en"}


def review_body(source=None):
    return {"source": source or {"source_label": "redacted sample", "document_text": "Fictional income: $52,000.",
                                  "consent_to_send_to_claude": True},
            "document_type": "income statement", "required_items": ["income", "date"]}


# Purpose: Confirm county mismatch is explained and unknown criteria remain unresolved.
# Inputs: Synthetic profiles with matching and nonmatching service areas.
# Outputs: Preliminary-only match results that never claim confirmed eligibility.
def test_match_explains_county_and_unknown_criteria():
    matched = client.post("/api/v1/homebuyers/match", json={"profile": profile()}).json()
    oc = next(item for item in matched["matches"] if item["program_id"] == "demo-oc-downpayment")
    assert oc["outcome"] == "NEEDS_MANUAL_REVIEW"
    assert any("Income limit is unknown" in explanation for explanation in oc["explanations"])
    assert any("Household-size rules are unknown" in explanation for explanation in oc["explanations"])
    assert any("First-time buyer requirements are unknown" in explanation for explanation in oc["explanations"])
    assert oc["availability"] == "DEMO_UNVERIFIED"

    mismatched = client.post("/api/v1/homebuyers/match", json={"profile": profile("San Diego")}).json()
    assert all(item["outcome"] == "OUTSIDE_SERVICE_AREA" for item in mismatched["matches"])


# Purpose: Ensure homebuyer AI review rejects declined or malformed document submissions.
# Inputs: Consent-rejected text and incomplete PDF payloads.
# Outputs: Pydantic 422 responses without provider calls.
def test_ai_review_requires_consent_and_complete_pdf():
    body = review_body({"source_label": "sample", "document_text": "Fictional text", "consent_to_send_to_claude": False})
    assert client.post("/api/v1/homebuyers/ai-document-review", json=body).status_code == 422

    malformed = base64.b64encode(b"%PDF-1.7\ntruncated").decode()
    body = review_body({"source_label": "sample.pdf", "pdf_base64": malformed, "consent_to_send_to_claude": True})
    response = client.post("/api/v1/homebuyers/ai-document-review", json=body)
    assert response.status_code == 422
    assert "complete PDF" in response.text


# Purpose: Enforce the 4 MiB PDF limit before invoking the shared Claude adapter.
# Inputs: A PDF-shaped payload larger than the supported upload size.
# Outputs: HTTP 422 validation error.
def test_ai_review_rejects_pdf_over_four_mib():
    from app.core.claude_client import MAX_PDF_BYTES
    oversized = base64.b64encode(b"%PDF-1.7\n" + b"a" * MAX_PDF_BYTES + b"\n%%EOF").decode()
    body = review_body({"source_label": "oversize.pdf", "pdf_base64": oversized, "consent_to_send_to_claude": True})
    assert client.post("/api/v1/homebuyers/ai-document-review", json=body).status_code == 422


# Purpose: Ensure provider failures never echo source document contents to the caller.
# Inputs: Consented fictional text and a mocked SDK exception containing that text.
# Outputs: Sanitized HTTP 502 response with no document-content leak.
def test_ai_review_sanitizes_provider_failure(monkeypatch):
    import sys
    import types

    class FailingMessages:
        async def parse(self, **kwargs):
            raise RuntimeError("provider rejected Fictional income: $52,000")

    class FakeClient:
        def __init__(self, **kwargs):
            self.messages = FailingMessages()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-placeholder-not-a-real-key")
    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(AsyncAnthropic=FakeClient))
    response = client.post("/api/v1/homebuyers/ai-document-review", json=review_body())
    assert response.status_code == 502
    assert "Fictional income" not in response.text
    assert response.json()["detail"] == "Claude analysis failed. Check server configuration, API access, and request validity."
