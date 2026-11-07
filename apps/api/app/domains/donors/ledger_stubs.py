"""In-memory donor ledger model for demos. It records events and never moves money.

Balances are scoped to an organization and campaign. A pledge is not spendable;
only received funds are available, and reservations must stay within designation.
This process-local store is intentionally not a production accounting ledger.
"""
from copy import deepcopy
from dataclasses import dataclass, field
from decimal import Decimal
from threading import RLock
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from app.core.money import usd

_lock = RLock()


@dataclass
class Fund:
    organization_id: str
    campaign_id: str
    events: list[dict[str, Any]] = field(default_factory=list)
    idempotency: dict[str, str] = field(default_factory=dict)


_funds: dict[str, Fund] = {}
_pledges: dict[str, dict[str, Any]] = {}
_reservations: dict[str, dict[str, Any]] = {}
_commitments: dict[str, dict[str, Any]] = {}


def _amount(value: str) -> Decimal:
    try:
        amount = usd(value)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if amount <= 0:
        raise HTTPException(422, "Amount must be positive")
    return amount


def _event(fund: Fund, state: str, amount: Decimal, key: str, **details: Any) -> dict[str, Any]:
    prior = fund.idempotency.get(key)
    if prior:
        return deepcopy(next(event for event in fund.events if event["event_id"] == prior))
    event = {"event_id": str(uuid4()), "state": state, "amount_usd": f"{amount:.2f}",
             "organization_id": fund.organization_id, "campaign_id": fund.campaign_id,
             "idempotency_key": key, **deepcopy(details)}
    fund.events.append(event)
    fund.idempotency[key] = event["event_id"]
    return deepcopy(event)


def _fund(fund_id: str, organization_id: str | None = None, campaign_id: str | None = None) -> Fund:
    fund = _funds.get(fund_id)
    if not fund or (organization_id and fund.organization_id != organization_id) or (campaign_id and fund.campaign_id != campaign_id):
        raise HTTPException(404, "Fund not found in requested organization/campaign scope")
    return fund


def record_donation_pledge(donor_id: str, fund_id: str, amount_usd: str,
                           restrictions: dict[str, object], *, organization_id: str,
                           campaign_id: str, idempotency_key: str) -> dict[str, object]:
    """Record PLEDGED intent. The designated campaign is immutable on this record."""
    amount = _amount(amount_usd)
    if not donor_id or not organization_id or not campaign_id or not idempotency_key:
        raise HTTPException(422, "Donor, scope, and idempotency key are required")
    designation = deepcopy(restrictions)
    if designation.get("campaign_id", campaign_id) != campaign_id:
        raise HTTPException(422, "Restriction campaign must match the scoped campaign")
    with _lock:
        fund = _funds.setdefault(fund_id, Fund(organization_id, campaign_id))
        _fund(fund_id, organization_id, campaign_id)
        event = _event(fund, "PLEDGED", amount, idempotency_key, donor_id=donor_id,
                       restrictions=designation, pledge_id=str(uuid4()))
        pledge_id = str(event["pledge_id"])
        _pledges[pledge_id] = {"fund_id": fund_id, "amount": amount, "state": "PLEDGED",
                               "event_id": event["event_id"]}
        return event


def confirm_funds_received(pledge_id: str, provider_reference: str, *, idempotency_key: str) -> dict[str, object]:
    """Recognize receipt only after external reconciliation confirmation."""
    with _lock:
        pledge = _pledges.get(pledge_id)
        if not pledge:
            raise HTTPException(404, "Pledge not found")
        fund = _fund(pledge["fund_id"])
        if pledge["state"] != "PLEDGED":
            if pledge.get("received_event"):
                return deepcopy(pledge["received_event"])
            raise HTTPException(409, "Pledge is not eligible for receipt")
        event = _event(fund, "RECEIVED", pledge["amount"], idempotency_key,
                       pledge_id=pledge_id, provider_reference=provider_reference)
        reconciliation = _event(fund, "RECONCILED", Decimal("0.00"), f"{idempotency_key}:reconciled",
                                related_event_id=event["event_id"], provider_reference=provider_reference)
        pledge["state"] = "RECEIVED"
        pledge["received_event"] = event
        pledge["reconciliation_event"] = reconciliation
        return event


def _balance(fund: Fund, fund_id: str) -> tuple[Decimal, Decimal]:
    received = sum((Decimal(e["amount_usd"]) for e in fund.events if e["state"] == "RECEIVED"), Decimal("0.00"))
    settled = sum((Decimal(e["amount_usd"]) for e in fund.events if e["state"] in {"DISBURSED", "RECONCILED"}), Decimal("0.00"))
    reserved = sum((item["amount"] for item in _reservations.values()
                    if item["fund_id"] == fund_id
                    and item["state"] in {"RESERVED", "COMMITTED"}), Decimal("0.00"))
    return received - settled, reserved


def reserve_restricted_funds(fund_id: str, beneficiary_id: str, amount_usd: str,
                             manager_id: str, *, organization_id: str, campaign_id: str,
                             idempotency_key: str) -> dict[str, object]:
    """Reserve received eligible funds for the same scoped campaign; manager approval required."""
    amount = _amount(amount_usd)
    if not manager_id or not beneficiary_id:
        raise HTTPException(422, "Manager authorization and beneficiary are required")
    with _lock:
        fund = _fund(fund_id, organization_id, campaign_id)
        prior_id = fund.idempotency.get(idempotency_key)
        if prior_id:
            return deepcopy(next(event for event in fund.events if event["event_id"] == prior_id))
        available, reserved = _balance(fund, fund_id)
        if amount > available - reserved:
            raise HTTPException(409, "Insufficient received, eligible funds")
        event = _event(fund, "RESERVED", amount, idempotency_key,
                       reservation_id=str(uuid4()), beneficiary_id=beneficiary_id, manager_id=manager_id)
        reservation_id = event["reservation_id"]
        stored = next(e for e in fund.events if e["event_id"] == event["event_id"])
        _reservations[reservation_id] = {"fund_id": fund_id, "state": "RESERVED", "amount": amount}
        return deepcopy(stored)


def confirm_commitment(reservation_id: str, reviewer_id: str, conditions: dict[str, object], *,
                       idempotency_key: str) -> dict[str, object]:
    with _lock:
        reservation = _reservations.get(reservation_id)
        if not reservation:
            raise HTTPException(404, "Reservation not found")
        if reservation["state"] != "RESERVED":
            raise HTTPException(409, "Reservation is not available for commitment")
        if not reviewer_id:
            raise HTTPException(422, "Reviewer authorization is required")
        fund = _fund(reservation["fund_id"])
        prior_id = fund.idempotency.get(idempotency_key)
        if prior_id:
            return deepcopy(next(event for event in fund.events if event["event_id"] == prior_id))
        event = _event(fund, "COMMITTED", reservation["amount"], idempotency_key,
                       commitment_id=str(uuid4()), reservation_id=reservation_id,
                       reviewer_id=reviewer_id, conditions=conditions)
        commitment_id = event["commitment_id"]
        stored = next(e for e in fund.events if e["event_id"] == event["event_id"])
        reservation["state"] = "COMMITTED"
        _commitments[commitment_id] = {"fund_id": reservation["fund_id"], "amount": reservation["amount"],
                                       "reservation_id": reservation_id, "state": "COMMITTED"}
        return deepcopy(stored)


def reconcile_external_disbursement(commitment_id: str, settlement_reference: str, *,
                                    idempotency_key: str) -> dict[str, object]:
    """Record external settlement; does not initiate a transfer."""
    with _lock:
        commitment = _commitments.get(commitment_id)
        if not commitment:
            raise HTTPException(404, "Commitment not found")
        fund = _fund(commitment["fund_id"])
        prior_id = fund.idempotency.get(idempotency_key)
        if prior_id:
            return deepcopy(next(event for event in fund.events if event["event_id"] == prior_id))
        if commitment["state"] != "COMMITTED":
            raise HTTPException(409, "Commitment is not eligible for disbursement reconciliation")
        if not settlement_reference:
            raise HTTPException(422, "Settlement reference is required")
        event = _event(fund, "DISBURSED", commitment["amount"], idempotency_key,
                       commitment_id=commitment_id, settlement_reference=settlement_reference)
        reconciliation = _event(fund, "RECONCILED", Decimal("0.00"), f"{idempotency_key}:reconciled",
                                related_event_id=event["event_id"], settlement_reference=settlement_reference)
        commitment["state"] = "DISBURSED"
        _reservations[commitment["reservation_id"]]["state"] = "DISBURSED"
        commitment["disbursement_event"] = event
        commitment["reconciliation_event"] = reconciliation
        return event


def prepare_donor_impact_report(campaign_id: str, start_date: str, end_date: str,
                                *, organization_id: str | None = None) -> dict[str, object]:
    """Return only aggregate ledger states for a campaign, with no household data."""
    with _lock:
        events = [event for fund in _funds.values()
                  if fund.campaign_id == campaign_id and (organization_id is None or fund.organization_id == organization_id)
                  for event in fund.events]
        totals = {state.lower(): sum((Decimal(e["amount_usd"]) for e in events if e["state"] == state), Decimal("0.00"))
                  for state in ("PLEDGED", "RECEIVED", "RESERVED", "COMMITTED", "DISBURSED", "RECONCILED")}
        return {"campaign_id": campaign_id, "start_date": start_date, "end_date": end_date,
                "totals_usd": {key: f"{value:.2f}" for key, value in totals.items()}, "event_count": len(events)}


def ledger_snapshot(fund_id: str, *, organization_id: str, campaign_id: str) -> dict[str, object]:
    """Read a scoped immutable event copy and derived available/reserved balances."""
    with _lock:
        fund = _fund(fund_id, organization_id, campaign_id)
        available, reserved = _balance(fund, fund_id)
        return {"organization_id": fund.organization_id, "campaign_id": fund.campaign_id,
                "pledged_usd": f"{sum((Decimal(e['amount_usd']) for e in fund.events if e['state']=='PLEDGED'), Decimal('0.00')):.2f}",
                "received_usd": f"{sum((Decimal(e['amount_usd']) for e in fund.events if e['state']=='RECEIVED'), Decimal('0.00')):.2f}",
                "available_usd": f"{max(Decimal('0.00'), available-reserved):.2f}",
                "reserved_usd": f"{reserved:.2f}", "events": deepcopy(fund.events)}
