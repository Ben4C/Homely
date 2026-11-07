from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)


# Purpose: Ensure homebuyer matches are never misrepresented as confirmed eligibility.
# Inputs: Valid fictional homebuyer profile.
# Outputs: HTTP 200 and only manual-review or out-of-area decisions.
def test_match_is_preliminary() -> None:
    profile = client.get("/api/v1/homebuyers/profile-template").json()
    response = client.post("/api/v1/homebuyers/match", json={"profile": profile})
    assert response.status_code == 200
    assert response.json()["demo"] is True
    assert all(x["outcome"] in {"NEEDS_MANUAL_REVIEW", "OUTSIDE_SERVICE_AREA"} for x in response.json()["matches"])


# Purpose: Reject invalid negative income before evaluating rules.
# Inputs: Invalid JSON profile with negative income.
# Outputs: HTTP 422 validation error.
def test_negative_income_is_rejected() -> None:
    profile = client.get("/api/v1/homebuyers/profile-template").json()
    profile["annual_income_usd"] = "-1.00"
    response = client.post("/api/v1/homebuyers/match", json={"profile": profile})
    assert response.status_code == 422
