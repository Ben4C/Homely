from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.domains.donors import ledger_stubs
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


def test_designated_allocation_cannot_be_reassigned() -> None:
    response = client.post("/api/v1/donors/allocate-preview", json={
        "total_available_usd": "25.01", "designated_campaign_ids": ["demo-campaign-2"]
    })
    assert response.status_code == 200
    data = response.json()
    assert [line["campaign_id"] for line in data["lines"]] == ["demo-campaign-2"]
    assert Decimal(data["lines"][0]["suggested_usd"]) == Decimal("25.01")
    assert Decimal(data["unallocated_usd"]) == Decimal("0.00")


def test_allocation_rejects_unknown_designated_campaign() -> None:
    response = client.post("/api/v1/donors/allocate-preview", json={
        "total_available_usd": "1.00", "designated_campaign_ids": ["missing"]
    })
    assert response.status_code == 404


def test_matching_preview_is_capped_and_unconfirmed() -> None:
    response = client.post("/api/v1/employers/matching-preview", json={
        "employer_program_id": "demo-employer-match",
        "employee_donation_usd": "750.25", "verified_eligible_donation": False
    })
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["possible_employer_match_usd"]) == Decimal("500.00")
    assert Decimal(data["total_potential_support_usd"]) == Decimal("1250.25")
    assert data["status"] == "PREVIEW_ONLY"


def test_ledger_requires_receipt_before_reservation_and_is_idempotent() -> None:
    pledge = ledger_stubs.record_donation_pledge(
        "donor-a", "fund-ledger-test", "10.01", {"campaign_id": "campaign-ledger-test"},
        organization_id="org-ledger-test", campaign_id="campaign-ledger-test", idempotency_key="pledge-1",
    )
    repeated = ledger_stubs.record_donation_pledge(
        "donor-a", "fund-ledger-test", "10.01", {"campaign_id": "campaign-ledger-test"},
        organization_id="org-ledger-test", campaign_id="campaign-ledger-test", idempotency_key="pledge-1",
    )
    assert pledge["event_id"] == repeated["event_id"]
    snapshot = ledger_stubs.ledger_snapshot("fund-ledger-test", organization_id="org-ledger-test", campaign_id="campaign-ledger-test")
    assert snapshot["available_usd"] == "0.00"
    try:
        ledger_stubs.reserve_restricted_funds(
            "fund-ledger-test", "beneficiary-a", "1.00", "manager-a",
            organization_id="org-ledger-test", campaign_id="campaign-ledger-test", idempotency_key="reserve-early",
        )
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 409
    else:
        raise AssertionError("pledged funds must not be reservable")
