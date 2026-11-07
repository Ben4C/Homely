# Architecture and end-to-end pipeline

## Two distinct financial tracks

1. **Development financing:** nonprofit developer defines housing project → pro forma costs + expected affordable sale proceeds → project financing gap → compatible contributions/awards → funding-manager verification → commitments/disbursement **recorded**, never automatically paid.
2. **Buyer assistance:** resident profile → verified program discovery → preliminary eligibility → submission to authorized program administrator → documents and human review → separate award commitment → lender/escrow coordination **outside the MVP**.

**Do not count a buyer down-payment award as a direct developer subsidy without a legally valid, documented accounting link.**

## Participants

- Homebuyer: owns household profile, consent, selected program applications.
- Donor: selects an eligible nonprofit/campaign and tracks organization-reported impact.
- Employer: creates restricted employee assistance or nonprofit project sponsorship.
- Funding manager: verifies program administration, applicant eligibility, budgets, commitments.
- Housing developer: maintains projects, model assumptions, project financing sources.
- Platform administrator: verifies organizations/program claims and oversees technical integrity; not a universal financial decision-maker.

## System structure

```text
apps/web/src/app/{homebuyer,manager,donor,employer,developer,admin}/page.tsx
     ↓ (typed browser API requests)
apps/api/app/main.py
     ↓ routes by domain
apps/api/app/domains/{homebuyers,funding_manager,donors,employers,developers,admin}/
     ↓ SQLAlchemy directory repositories + separate synthetic financial previews
PostgreSQL / server-only Claude SDK (requires configured key)
```

## Shared workflow state machines (design target)

### Program listing
`DRAFT → CLAIM_PENDING → VERIFIED_OPEN / VERIFIED_CLOSED / WAITLIST / UNCONFIRMED → STALE → ARCHIVED`

### Application
`DRAFT → SUBMITTED → SCREENING → MORE_INFO → HUMAN_REVIEW → APPROVED / DECLINED / WAITLISTED → COMMITTED → DISBURSED → CLOSED`

### Money / fund availability
`PLEDGED → RECEIVED → AVAILABLE → RESERVED → COMMITTED → DISBURSEMENT_PENDING → DISBURSED → RECONCILED`

These are domain contracts, **not** currently implemented transaction state machines. Transitions must require the right organization authority and maintain audit events.

## Privacy and fairness

Use minimum necessary fields during preliminary match. No SSNs, identity documents, income proofs, or real banking details in fixtures. No speculative approval likelihood. No protected-class inference. Matching should be deterministic and versioned with explicit program sources; any automated queue ranking must use an organization's published authorized priorities.


## Implemented directory integration (2026-11-07)

All routes share root navigation, template tokens, accessible form/card styles, and theme selection. Program/organization details use stable IDs. The homebuyer profile distinguishes residence from intended purchase location. The donor directory is separate from synthetic campaigns; manager/admin review is separate from application decisions.

`app/data/schemas.py` validates official-source imports; `ingestion.py` normalizes and stages changes; `models.py` stores normalized geography and immutable source/rule history; `repository.py` performs conservative screening and discovery; `router.py` exposes public reads and authorized review. Alembic owns the schema. See [operations](DIRECTORY_OPERATIONS.md).

Eligibility evaluates published geographic areas and sourced rule versions. Income tables are keyed by household size; assistance caps are separate money fields. Unsupported or missing criteria remain explicit unknowns. Review and source retrieval must both be fresh. Default accepting-applications queries include only VERIFIED_OPEN. No calculated percentage represents approval likelihood.

`REGISTRY_MODE=database` is the default. Legacy manager/homebuyer routes delegate to the repository. Explicit demo mode remains available for original fixture compatibility; missing database configuration does not activate it. Donor, employer, project, and application previews remain synthetic and unpersisted. Source review uses server-configured reviewer scope, revision checks, row locks, and atomic audit writes; it cannot authorize money.
