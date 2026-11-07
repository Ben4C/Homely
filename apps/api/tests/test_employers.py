from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)


# Purpose: Confirm no employer benefit is represented as verified or open.
# Inputs: None.
# Outputs: All records labelled DEMO_UNVERIFIED.
def test_employer_programs_are_synthetic() -> None:
    data = client.get("/api/v1/employers/programs").json()
    assert data["demo"] is True
    assert all(p["status"] == "DEMO_UNVERIFIED" for p in data["programs"])


# Purpose: Ensure employer pre-screen requires explicit consent.
# Inputs: Fictional program ID with false consent.
# Outputs: HTTP 400 before any verification action.
def test_employer_check_requires_consent() -> None:
    response = client.post("/api/v1/employers/check", json={"program_id":"demo-employer-aid","county":"Orange","tenure_months":24,"employee_consent":False})
    assert response.status_code == 400
