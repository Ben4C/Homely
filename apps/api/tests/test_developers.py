from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)


# Purpose: Confirm challenge-style synthetic project balances with $95k missing.
# Inputs: $535k cost, $285k buyer, $100k subsidy, $55k revenue, no donations/sponsors.
# Outputs: Remaining gap exactly $95,000 in decimal string form.
def test_project_gap_calculation() -> None:
    response = client.post("/api/v1/projects/gap", json={
        "cost_to_create_usd":"535000.00", "affordable_buyer_proceeds_usd":"285000.00",
        "public_development_subsidies_usd":"100000.00", "earned_project_revenue_usd":"55000.00",
        "nonprofit_donations_usd":"0.00", "employer_project_sponsorship_usd":"0.00",
    })
    assert response.status_code == 200
    assert response.json()["remaining_gap_usd"] == "95000.00"


# Purpose: Prevent negative cost or funding input values.
# Inputs: Negative cost with otherwise valid payload.
# Outputs: HTTP 422 rather than bogus math.
def test_negative_cost_rejected() -> None:
    response = client.post("/api/v1/projects/gap", json={
        "cost_to_create_usd":"-1.00", "affordable_buyer_proceeds_usd":"0.00",
        "public_development_subsidies_usd":"0.00", "earned_project_revenue_usd":"0.00",
        "nonprofit_donations_usd":"0.00", "employer_project_sponsorship_usd":"0.00",
    })
    assert response.status_code == 422


# Purpose: Disallow fractional cents to prevent silent money rounding.
# Inputs: Cost amount with three decimal places.
# Outputs: HTTP 422 validation error.
def test_fractional_cents_rejected() -> None:
    response = client.post("/api/v1/projects/gap", json={
        "cost_to_create_usd":"535000.001", "affordable_buyer_proceeds_usd":"285000.00",
        "public_development_subsidies_usd":"100000.00", "earned_project_revenue_usd":"55000.00",
        "nonprofit_donations_usd":"0.00", "employer_project_sponsorship_usd":"0.00",
    })
    assert response.status_code == 422
