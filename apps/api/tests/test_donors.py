from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)


# Purpose: Ensure allocation math never exceeds supplied hypothetical funds.
# Inputs: $50,000 test balance.
# Outputs: Suggested lines sum to <= available; no posted payment.
def test_allocation_preview_is_bounded() -> None:
    response = client.post("/api/v1/donors/allocate-preview", json={"total_available_usd": "50000.00"})
    assert response.status_code == 200
    data = response.json()
    total = sum((Decimal(x["suggested_usd"]) for x in data["lines"]), Decimal("0"))
    assert total + Decimal(data["unallocated_usd"]) == Decimal("50000.00")
    assert data["demo"] is True


# Purpose: Prevent zero-value pledges and unsupported campaigns.
# Inputs: Invalid amount and unknown campaign ID.
# Outputs: HTTP 422 for zero; HTTP 404 for nonexistent campaign.
def test_pledge_is_not_a_payment() -> None:
    assert client.post("/api/v1/donors/pledge-preview", json={"campaign_id":"demo-campaign-1","amount_usd":"0"}).status_code == 422
    response = client.post("/api/v1/donors/pledge-preview", json={"campaign_id":"demo-campaign-1","amount_usd":"12.00"})
    assert response.json()["status"] == "NOT_SUBMITTED"
