from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)


# Purpose: Verify registry returns demo markers instead of implying live open programs.
# Inputs: No request payload.
# Outputs: Test success if program metadata is explicit and synthetic.
def test_list_programs_are_not_claimed_live() -> None:
    response = client.get("/api/v1/programs?county=Orange")
    assert response.status_code == 200
    payload = response.json()
    assert payload["demo"] is True
    assert all(p["availability"] == "DEMO_UNVERIFIED" for p in payload["programs"])


# Purpose: Ensure application preview refuses sharing without user consent.
# Inputs: Program ID, profile ID and false consent flag.
# Outputs: HTTP 400, no submission.
def test_no_application_without_consent() -> None:
    response = client.post("/api/v1/applications", json={"program_id":"demo-oc-downpayment", "homebuyer_profile_id":"demo-buyer", "consent_to_share":False})
    assert response.status_code == 400
