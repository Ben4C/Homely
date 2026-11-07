# Developer 4 — Corporate Sponsorship & Employer Matching

**Owner:** Person 4 · **Branch:** `feat/dev4-corporate-sponsorship`  
**User archetype:** Company sponsor / employer program administrator  
**Approximate effort:** 20%; UI 35%, API/money policy 40%, tests/docs 25%.

## Exclusive file ownership

- `apps/web/src/app/employer/page.tsx`
- `apps/web/src/components/employer/{EmployerDashboard,SponsorshipTools}.tsx` **(new)**
- `apps/api/app/domains/employers/{router,schemas,service,fixtures,workflow_stubs,sponsorship}.py`
- `packages/contracts/src/employers.ts`
- `apps/api/tests/test_employers.py` + employer-specific sponsorship tests

**Read-only:** donor fixture campaigns and ledger interfaces (Dev 3), development gap (Dev 5), homebuyer profile (Dev 1).

## Assigned functions — input → output

1. `preview_match(MatchingGiftRequest) -> MatchingGiftResponse` **(new)**: deterministic 1:1 fictional employee match with $500 cap and no budget reservation.
2. `preview_sponsorship(SponsorshipPreviewRequest) -> SponsorshipPreviewResponse` **(new)**: classify CASH vs IN_KIND contribution and return 0 presently allocatable dollars; in-kind cannot be treated as cash.
3. `SponsorshipTools()` **(new)**: corporate sponsor UI for matching and project support previews.
4. `check_employer_program(...) -> EmployerCheckResponse`: consent-gated geographic prescreen, never self-confirm employment.
5. `create_sponsorship_agreement(...)` **(stub)**: sponsor terms, nonprofit acceptance, documented in-kind valuation or cash receipt.
6. `verify_employee_eligibility(...)` **(stub)**: authorized, minimum-data employment attestation through nonprofit administrator; **no employer access to personal finance documents**.

## Deliverables

- [ ] Employer programs dashboard and employer-specific caps/budgets (fictional demo fixtures only).
- [ ] Project sponsorship preview with separate CASH and IN_KIND workflows.
- [ ] Employee gift matching preview with limits, payroll/HR verification as future integration.
- [ ] Design organization permissions separating sponsor view from private applicant review.
- [ ] Correct accounting: pending sponsorship is not development revenue; matching gift is not paid money.
- [ ] Tests: unknown policy/campaign, negative amounts, cap, budget, in-kind, no payment.

## Integration contract

- `POST /api/v1/employers/matching-preview` **(new)** consumed by Dev 3.
- `POST /api/v1/employers/sponsorship-preview` **(new)** consumed by employer GUI.
- Sponsorship confirmed by a future manager workflow may be surfaced to Dev 5 in `employer_project_sponsorship_usd` only after approved/received verification.

## Definition of done

Corporate user can inspect mock sponsored projects, preview a matching policy and sponsor cash or materials. Results explicitly show unverified/zero-allocatable state; staff have no unauthorized applicant access. Tests + screenshot + API example accompany PR.
