# Developer 3 — Donor Experience, Matching-Gift Discovery & Allocation Ledger

**Owner:** Person 3 · **Branch:** `feat/dev3-donor-matching-ledger`  
**User archetype:** Individual donor / charity fundraiser  
**Approximate effort:** 20%; UI 30%, ledger/algorithm 45%, tests/docs 25%.

## Exclusive file ownership

- `apps/web/src/app/donor/page.tsx`
- `apps/web/src/components/donor/{DonorDashboard,MatchingGiftDemo}.tsx` **(matching UI new)**
- `apps/api/app/domains/donors/{router,schemas,service,fixtures,ledger_stubs}.py`
- `packages/contracts/src/donors.ts`
- `apps/api/tests/test_donors.py` + domain-specific ledger tests

**Read-only:** employer matching contract and route (Dev 4), shared financial utilities / AI adapter (Dev 5), manager funding programs (Dev 2).

## Assigned functions — input → output

1. `list_campaigns() -> CampaignListResponse`: show **verified nonprofit** campaigns when available; synthetic demos otherwise.
2. `preview_pledge(PledgePreviewRequest) -> PledgePreviewResponse`: validate proposed donation, no charge.
3. `preview_allocations(AllocationPreviewRequest) -> AllocationPreviewResponse`: nonbinding queue order under a fictional unrestricted pool, correct cents and no over-allocation.
4. `MatchingGiftDemo()` **(new)**: donor enters fictional donation, calls Dev 4 `POST /employers/matching-preview`, sees capped potential match with no confirmed employer offer.
5. `ledger_stubs.py` functions: implement data model for `pledged/received/available/reserved/committed/disbursed/reconciled` with scoped organization/campaign IDs, immutable event history and idempotent keys; **no real transactions in hackathon**.
6. `DonorDashboard()`: include corporate match preview alongside donor pledge and charity allocation queue.

## Deliverables

- [ ] Donor campaign search, direct nonprofit choice, simulated pledge preview.
- [ ] Employee matching gift discovery with explicit hypothetical policy and cap; avoid collecting payroll/HR data.
- [ ] Restricted vs unrestricted donation behavior; donor designations must not be reassigned by auto-queue.
- [ ] Ledger state machine spec: funds are not usable until actually received and eligible.
- [ ] Add cent-accurate tests for allocation, duplicate requests, amounts and matching cap.
- [ ] Partner with Dev 4 on matching policy; partner with Dev 5 on development gap reconciliation.

## Integration contract

- `GET /api/v1/donors/campaigns`, `POST /api/v1/donors/pledge-preview`, `POST /api/v1/donors/allocate-preview`.
- Read-only `POST /api/v1/employers/matching-preview` via Dev 4's published contract.
- Manager-approved donation allocations must be separately authorized before any commitment.

## Definition of done

Donor completes a fictional campaign pledge preview, sees a capped hypothetical matching gift and a manager-controlled allocation suggestion. No payment occurs or misleading tax-deduction claims. Tests + screenshot + API example accompany PR.
